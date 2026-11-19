"""Run the Azure synthetic-data workflow against local real APIs; clean only owned data."""
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_baseline import Api, exercise

api = Api({'restaurants': 'http://127.0.0.1:8001', 'dining': 'http://127.0.0.1:8002'}, 'http://localhost:8080')
marker = 'Local baseline check ' + uuid4().hex
try:
    before = exercise(api, populate=True, marker=marker)
    assert exercise(api, populate=True, marker=marker) == before, 'Repeat duplicated or changed data'
    assert exercise(api, marker=marker) == before, 'Read-only verification changed data'
    print('Baseline workflow: real HTTP/SQL, CORS, cross-service visit, item, exact bill bytes and repeat all passed')
finally:
    rows = api.call('restaurants', 'GET', '/restaurants')
    for row in rows:
        if row['title'] != marker:
            continue
        if row.get('saved'):
            api.call('restaurants', 'DELETE', '/saved-restaurants/' + str(row['saved']['id']), expected=204)
        # Only this unique check's exact catalog ID/title is removed. Never user data.
        subprocess.run(['docker', 'compose', 'exec', '-T', 'restaurants', 'python', '-'], text=True, check=True,
                       input=f'''from services.restaurants.catalog import transaction
with transaction() as cursor:
    cursor.execute('DELETE FROM dbo.restaurants WHERE id=%s AND title=%s', ({row['id']!r}, {marker!r}))
''')
