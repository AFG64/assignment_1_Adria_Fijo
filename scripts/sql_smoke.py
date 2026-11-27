"""Run inside each service image with stdin, against the local compose SQL only."""
import os
from pathlib import Path
from urllib.parse import urlsplit

import pymssql

from service_runtime.database import connect, migrate, probe

url = os.environ['DATABASE_URL']
name = urlsplit(url).path.lstrip('/')
other = 'picky_dining' if name == 'picky_restaurants' else 'picky_restaurants'
assert migrate(url, Path('/app/migrations')) == 0, 'Second boot reapplied migration'
connection = connect(url)
try:
    cursor = connection.cursor()
    cursor.execute('SELECT version FROM dbo.schema_migrations ORDER BY version')
    expected = sorted(path.name for path in Path('/app/migrations').glob('[0-9][0-9][0-9]_*.sql'))
    assert [row[0] for row in cursor.fetchall()] == expected
    cursor.execute("SELECT COUNT(*) FROM sys.tables WHERE name IN ('restaurants', 'saved_restaurants', 'visits', 'bills', 'visit_items')")
    assert cursor.fetchone()[0] == (2 if name == 'picky_restaurants' else 3)
    cursor.execute('SELECT COUNT(*) FROM dbo.health_probe')
    before = cursor.fetchone()[0]
    probe(url)
    cursor.execute('SELECT COUNT(*) FROM dbo.health_probe')
    assert cursor.fetchone()[0] == before
    try:
        cursor.execute(f'SELECT name FROM [{other}].sys.tables')
    except pymssql.DatabaseError:
        connection.rollback()
    else:
        raise AssertionError('Service login accessed peer database')
    # Fixed test marker retained across the restart check; repeat runs do not duplicate.
    cursor.execute("IF NOT EXISTS (SELECT 1 FROM dbo.health_probe WHERE token='restart-check') "
                   "INSERT INTO dbo.health_probe (token) VALUES ('restart-check')")
    connection.commit()
finally:
    connection.close()
print(f'{name}: migration no-op, own read/write, peer denied, persistence marker ready')
