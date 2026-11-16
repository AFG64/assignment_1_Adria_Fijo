"""Bounded local HTTP/SQL integration and restart persistence check (no Azure)."""
from pathlib import Path
import json
import subprocess
import time
from http.client import HTTPException
from urllib.request import urlopen


def wait_health(port):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            with urlopen(f'http://127.0.0.1:{port}/health', timeout=8) as response:
                assert json.load(response)['db'] == 'ok'
                return
        except (OSError, HTTPException):
            time.sleep(2)
    raise SystemExit(f'Health did not become ready on local port {port}')


for port in (8001, 8002):
    wait_health(port)
for service in ('restaurants', 'dining'):
    subprocess.run(['docker', 'compose', 'exec', '-T', service, 'python', '-'],
                   input=Path('scripts/sql_smoke.py').read_text(), text=True, check=True)
subprocess.run(['docker', 'compose', 'restart', 'restaurants', 'dining'], check=True)
for port in (8001, 8002):
    wait_health(port)
for service in ('restaurants', 'dining'):
    subprocess.run(['docker', 'compose', 'exec', '-T', service, 'python', '-'],
                   input='''import os
from service_runtime.database import connect
connection = connect(os.environ['DATABASE_URL'])
cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM dbo.health_probe WHERE token='restart-check'")
assert cursor.fetchone()[0] == 1, 'Restart lost data'
cursor.execute("DELETE FROM dbo.health_probe WHERE token='restart-check'")
connection.commit()
connection.close()
print('Restart retained marker')
''', text=True, check=True)
print('Local stack integration checks passed')
