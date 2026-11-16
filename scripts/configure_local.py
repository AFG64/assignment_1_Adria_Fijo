"""Generate private, URL/SQL-safe development passwords once; never overwrite."""
import os
from pathlib import Path
import secrets

path = Path('.env')
values = {name: 'Aa1' + secrets.token_hex(24) for name in (
    'MSSQL_SA_PASSWORD', 'RESTAURANTS_PASSWORD', 'DINING_PASSWORD',
)}
try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit('.env already exists; left unchanged')
with os.fdopen(descriptor, 'w') as stream:
    stream.write(''.join(f'{name}={value}\n' for name, value in values.items()))
print('Created private .env with generated local passwords; do not commit it.')
