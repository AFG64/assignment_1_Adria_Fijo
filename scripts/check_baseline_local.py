"""Run the Azure synthetic-data workflow against local real APIs; clean only owned data."""
from pathlib import Path
import json
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_baseline import Api, exercise
from scripts.azure_deploy import wait_health

urls = {'restaurants': 'http://127.0.0.1:8001', 'dining': 'http://127.0.0.1:8002'}
api = Api(urls, 'http://localhost:8080')
marker = 'Local baseline check ' + uuid4().hex
try:
    before = exercise(api, populate=True, marker=marker)
    assert before['line_total'] == 7, 'Computed total missing or incorrect in real API response'
    config = json.loads(subprocess.check_output(['docker', 'compose', 'config', '--format', 'json'], text=True))
    assert config['services']['sql']['image'] == 'mcr.microsoft.com/mssql/server:2022-latest'
    versions = {service: api.call(service, 'GET', '/health')['version'] for service in urls}
    try:
        subprocess.run(['docker', 'compose', 'stop', 'sql'], check=True, timeout=120)
        for service, url in urls.items():
            try:
                with urlopen(url + '/health', timeout=15):
                    raise AssertionError('Own SQL failure returned a healthy response')
            except HTTPError as error:
                body = json.load(error)
                assert error.code == 503 and body['db'] == 'unavailable' and body['version'] == versions[service]
    finally:
        subprocess.run(['docker', 'compose', 'start', 'sql'], check=True, timeout=120)
        for service, url in urls.items():
            wait_health(url, versions[service], budget=180)
    assert exercise(api, populate=True, marker=marker) == before, 'Repeat duplicated or changed data'
    assert exercise(api, marker=marker) == before, 'Read-only verification changed data'
    logs = subprocess.check_output(['docker', 'compose', 'logs', '--no-log-prefix', '--no-color', 'restaurants', 'dining'], text=True)
    health_logs = []
    for line in logs.splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get('path') == '/health':
            health_logs.append(record)
    for service in urls:
        records = [r for r in health_logs if r.get('service') == service]
        assert {200, 503} <= {r['status'] for r in records}
        assert all({'method', 'path', 'status', 'duration_ms', 'version'} <= r.keys() for r in records)
    print('Baseline recovery: own SQL down503/recovered200, versioned request logs, unchanged IDs/item total/PDF bytes, repeated workflow and CORS passed')
finally:
    rows = api.call('restaurants', 'GET', '/restaurants')
    for row in rows:
        if row['title'] != marker:
            continue
        if row.get('saved'):
            api.call('restaurants', 'DELETE', '/saved-restaurants/' + str(row['saved']['id']), expected=204)
        # Only this unique check's exact catalog ID/title is removed. Never user data.
        subprocess.run(['docker', 'compose', 'exec', '-T', 'restaurants', 'python', '-m', 'service_runtime.local_start', 'python', '-'], text=True, check=True,
                       input=f'''from services.restaurants.catalog import transaction
with transaction() as cursor:
    cursor.execute('DELETE FROM dbo.restaurants WHERE id=%s AND title=%s', ({row['id']!r}, {marker!r}))
''')
