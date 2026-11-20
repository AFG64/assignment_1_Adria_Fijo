"""Real HTTP + local SQL seam, stopped-peer recovery and concurrent deletion checks."""
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def call(port, method, path, body=None):
    request=Request(f'http://127.0.0.1:{port}'+path,
                    data=json.dumps(body).encode() if body is not None else None,
                    method=method, headers={'Content-Type':'application/json'})
    try:
        response=urlopen(request,timeout=15)
    except HTTPError as exc:
        response=exc
    with response:
        raw=response.read()
        return response.status, json.loads(raw) if raw else None


def start(service):
    subprocess.run(['docker','compose','up','-d','--wait','--wait-timeout','180',service],check=True)


created=[]
try:
    status,restaurant=call(8001,'POST','/restaurants',{'title':'Seam-'+uuid4().hex})
    assert status==201
    created.append(restaurant)
    sid=restaurant['saved']['id'];history=f'/saved-restaurants/{sid}/visits'
    code,visit=call(8002,'POST',history,{'visit_date':'2026-01-01','rating':4})
    assert code==201,(code,visit)
    assert call(8001,'GET',f'/saved-restaurants/{sid}')[1]['status']=='visited'
    assert call(8002,'GET',history)[1][0]['id']==visit['id']
    visit_path=history+'/'+str(visit['id'])
    assert call(8002,'POST',visit_path+'/items',{'item_name':'Soup','quantity':1})[0]==201
    multipart=(b'--seam-boundary\r\nContent-Disposition: form-data; name="bill_file"; filename="test.pdf"\r\n'
               b'Content-Type: application/pdf\r\n\r\n%PDF-seam\r\n--seam-boundary--\r\n')
    request=Request('http://127.0.0.1:8002'+visit_path+'/bills',data=multipart,method='POST',
                    headers={'Content-Type':'multipart/form-data; boundary=seam-boundary'})
    with urlopen(request,timeout=10) as response:
        assert response.status==201
        bill=json.load(response)

    assert call(8002,'POST','/saved-restaurants/2147483647/visits',{'visit_date':'2026-01-01'})[0]==404
    subprocess.run(['docker','compose','stop','restaurants'],check=True)
    assert call(8002,'GET','/health')[0]==200
    assert call(8002,'GET',history)[0]==200
    failed=call(8002,'POST',history,{'visit_date':'2026-01-01'})
    assert failed[0]==503 and not failed[1]['retryable']
    assert len(call(8002,'GET',history)[1])==1
    start('restaurants')
    subprocess.run(['docker','compose','stop','dining'],check=True)
    assert call(8001,'GET','/health')[0]==200
    assert call(8001,'GET','/restaurants')[0]==200
    failed=call(8001,'DELETE',f'/saved-restaurants/{sid}')
    assert failed[0]==503 and failed[1]['error']=='cleanup_pending'
    assert call(8001,'GET',f'/saved-restaurants/{sid}')[0]==404
    start('dining')
    assert call(8001,'DELETE',f'/saved-restaurants/{sid}')[0]==204
    assert call(8001,'DELETE',f'/saved-restaurants/{sid}')[0]==204
    assert call(8002,'GET',history)[1]==[]
    assert call(8002,'GET',visit_path+'/bills/'+str(bill['id']))[0]==404
    # Every interleaving ends without an orphan once the idempotent delete succeeds.
    for _ in range(3):
        _,row=call(8001,'POST','/restaurants',{'title':'Concurrent-'+uuid4().hex})
        created.append(row);saved=row['saved']['id'];path=f'/saved-restaurants/{saved}'
        with ThreadPoolExecutor(max_workers=2) as pool:
            insert=pool.submit(call,8002,'POST',path+'/visits',{'visit_date':'2026-01-01'})
            delete=pool.submit(call,8001,'DELETE',path)
            assert insert.result()[0] in (201,404,503)
            assert delete.result()[0] in (204,503)
        assert call(8001,'DELETE',path)[0]==204
        assert call(8002,'GET',path+'/visits')[1]==[]
    print('Seam passed: real visit coordination, stopped peers, explicit partial deletion, retry cleanup, concurrent create/delete')
finally:
    start('restaurants');start('dining')
    for row in created:
        call(8001,'DELETE',f"/saved-restaurants/{row['saved']['id']}")
    ids=[row['id'] for row in created]
    subprocess.run(['docker','compose','exec','-T','restaurants','python','-m','service_runtime.local_start','python','-'],text=True,check=True,input=f'''
from services.restaurants.catalog import transaction
with transaction() as cursor:
    for restaurant_id in {ids!r}:
        cursor.execute('DELETE FROM dbo.restaurants WHERE id=%s',(restaurant_id,))
''')
