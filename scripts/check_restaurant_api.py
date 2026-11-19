"""Real SQL-backed HTTP regression checks. Run only against the local compose stack."""
import json
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8001'


def call(method, path, payload=None, expected=200):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(BASE + path, data=body, method=method, headers={'Content-Type': 'application/json', 'Origin': 'http://localhost:8080'})
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == expected, (path, response.status, response.read())
        assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:8080'
        return None if expected == 204 else json.load(response)


created = None
saved_seed_id = None
try:
    call('POST','/restaurants',{'title':'bad', 'rating':8},400)
    call('GET','/restaurants/2147483647', expected=404)
    created = call('POST','/restaurants',{'title':'SQL-check-'+uuid4().hex,'category_name':'Test','city':'Madrid','price':2},201)
    rid, sid = created['id'], created['saved']['id']
    assert call('GET',f'/restaurants/{rid}')['title']==created['title']
    assert any(row['id']==rid for row in call('GET','/restaurants?category=Test&city=Madrid&price=2&status=want_to_go'))
    assert any(row['id']==rid for row in call('GET','/saved-restaurants'))
    call('POST',f'/restaurants/{rid}/saved-entry',{'status':'visited'},409)
    call('PATCH',f'/saved-restaurants/{sid}',{'rating':4.5,'notes':'SQL test','would_go_back':True})
    assert call('GET',f'/saved-restaurants/{sid}')['would_go_back'] is True
    assert any(row['id']==rid for row in call('GET','/restaurants?min_rating=4.5'))
    call('PUT',f'/saved-restaurants/{sid}/visited')
    assert call('GET',f'/saved-restaurants/{sid}')['status']=='visited'
    call('PUT',f'/restaurants/{rid}/location',{'mode':'manual','address':'Test address','latitude':40.4,'longitude':-3.7})
    assert call('GET',f'/restaurants/{rid}')['latitude']==40.4
    candidates = call('GET','/restaurants?status=not_saved')
    if candidates:
        saved = call('POST', f"/restaurants/{candidates[0]['id']}/saved-entry", {'status':'want_to_go'}, 201)
        saved_seed_id = saved['id']
        assert call('GET', f'/saved-restaurants/{saved_seed_id}')['restaurant_id'] == candidates[0]['id']
    # Seed reruns do not duplicate catalog rows. Personal data stays intact.
    subprocess.run(['docker','compose','exec','-T','restaurants','python','-'],text=True,check=True,input='''
from services.restaurants.seed import seed
from services.restaurants.catalog import transaction
with transaction() as cursor:
    cursor.execute('SELECT COUNT(*) AS n FROM dbo.restaurants')
    before=cursor.fetchone()['n']
seed(); seed()
with transaction() as cursor:
    cursor.execute('SELECT COUNT(*) AS n FROM dbo.restaurants')
    assert cursor.fetchone()['n']==before
print('Seed rerun: unchanged row count')
''')
    call('PATCH',f'/saved-restaurants/{sid}',{'rating':None,'notes':None,'would_go_back':None})
    assert call('GET',f'/saved-restaurants/{sid}')['rating'] is None
    call('DELETE',f'/saved-restaurants/{sid}',expected=204)
    call('GET',f'/saved-restaurants/{sid}',expected=404)
    call('DELETE',f'/saved-restaurants/{sid}',expected=204)
finally:
    if saved_seed_id:
        subprocess.run(['docker','compose','exec','-T','restaurants','python','-',str(saved_seed_id)], text=True,check=True,input='''
import sys
from services.restaurants.catalog import transaction
with transaction() as cursor:
    cursor.execute('DELETE FROM dbo.saved_restaurants WHERE id=%s',(int(sys.argv[1]),))
''')
    if created:
        # Remove only this test's owned restaurant; no public deletion claims yet.
        subprocess.run(['docker','compose','exec','-T','restaurants','python','-',str(created['id'])], text=True,check=True,input='''
import sys
from services.restaurants.catalog import transaction
with transaction() as cursor:
    cursor.execute('DELETE FROM dbo.restaurants WHERE id=%s',(int(sys.argv[1]),))
''')
print('Restaurant SQL HTTP workflows passed')
