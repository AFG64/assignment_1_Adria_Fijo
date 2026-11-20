"""Check Azure-style contained users/roles using disposable LOCAL SQL databases.

Never connects to Azure. Restores instance options and removes only databases
created by this invocation. Existing compose database contents are untouched.
"""
import json
import os
import secrets
import subprocess
from uuid import uuid4


def run(args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError('Local contained-user check failed; credential-bearing tool output suppressed')
    return result.stdout


def sql(statement):
    return run(['docker', 'compose', 'exec', '-T', 'sql', 'python3', '/local/bootstrap.py', 'sql', '-h-1', '-W', '-s,'],
               input='SET NOCOUNT ON;\n' + statement, timeout=120)


def main():
    config = json.loads(run(['docker', 'compose', 'config', '--format', 'json']))
    if config['services']['sql']['image'] != 'mcr.microsoft.com/mssql/server:2022-latest':
        raise RuntimeError('This check requires the project LOCAL SQL container')
    original = {}
    for line in sql("SELECT name,CONVERT(int,value_in_use) FROM sys.configurations WHERE name IN ('show advanced options','contained database authentication');").splitlines():
        if ',' in line:
            name, value = line.rsplit(',', 1)
            original[name.strip()] = int(value)
    assert set(original) == {'show advanced options', 'contained database authentication'}
    suffix = uuid4().hex[:8]
    names = {s: f'picky_rolecheck_{s}_{suffix}' for s in ('restaurants', 'dining')}
    passwords = {s: 'Aa1' + secrets.token_hex(24) for s in names}
    created = []
    try:
        sql("EXEC sp_configure 'show advanced options',1; RECONFIGURE; EXEC sp_configure 'contained database authentication',1; RECONFIGURE;")
        for service, name in names.items():
            sql(f'CREATE DATABASE [{name}] CONTAINMENT=PARTIAL;')
            created.append(name)
            user = 'rolecheck_' + service
            sql(f"USE [{name}]; CREATE USER [{user}] WITH PASSWORD='{passwords[service]}', DEFAULT_SCHEMA=dbo; "
                + ' '.join(f'ALTER ROLE [{role}] ADD MEMBER [{user}];' for role in ('db_ddladmin', 'db_datareader', 'db_datawriter')))
        for service, name in names.items():
            peer = next(value for key, value in names.items() if key != service)
            code = '''
import os
from pathlib import Path
import pymssql
from service_runtime.database import connect, migrate, probe
url=os.environ['DATABASE_URL']
assert migrate(url,Path('/app/migrations'))==1
assert migrate(url,Path('/app/migrations'))==0
probe(url)
with connect(url) as connection:
    cursor=connection.cursor()
    cursor.execute("SELECT IS_ROLEMEMBER('db_owner')")
    assert cursor.fetchone()[0]==0
    cursor.execute("DECLARE @r int; EXEC @r=sp_getapplock @Resource='saved:1',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=2000; SELECT @r;")
    assert cursor.fetchone()[0]>=0
    connection.rollback()
'''
            if service == 'restaurants':
                code += '''
from services.restaurants.seed import seed
seed();seed()
with connect(url) as connection:
    cursor=connection.cursor();cursor.execute('SELECT COUNT(*) FROM dbo.restaurants')
    assert cursor.fetchone()[0]==14
'''
            code += f'''
peer_url=url.rsplit('/',1)[0]+'/{peer}'
try:
    peer_connection=connect(peer_url)
except pymssql.DatabaseError:
    pass
else:
    peer_connection.close()
    raise AssertionError('Contained service user reached peer database')
print('Contained user: first/repeat migration, own read/write, app lock, non-owner and peer denial passed')
'''
            env = {**os.environ, 'DATABASE_URL': f'mssql://rolecheck_{service}:{passwords[service]}@sql:1433/{name}'}
            run(['docker', 'compose', 'run', '--rm', '--no-deps', '-T', '-e', 'DATABASE_URL', service, 'python', '-'],
                env=env, input=code, timeout=240)
            print(service + ': Azure-style least-privilege SQL checks passed', flush=True)
    finally:
        try:
            for name in reversed(created):
                sql(f'ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{name}];')
        finally:
            sql("EXEC sp_configure 'contained database authentication'," + str(original['contained database authentication'])
                + "; RECONFIGURE; EXEC sp_configure 'show advanced options'," + str(original['show advanced options']) + '; RECONFIGURE;')


if __name__ == '__main__':
    main()
