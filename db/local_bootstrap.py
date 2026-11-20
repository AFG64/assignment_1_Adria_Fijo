"""Local stock-SQL-container bootstrap; never used by Azure deployment."""
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

ROOT = Path('/run/picky')
SQLCMD = '/opt/mssql-tools18/bin/sqlcmd'
PASSWORDS = {'sql': 'MSSQL_SA_PASSWORD', 'restaurants': 'RESTAURANTS_PASSWORD', 'dining': 'DINING_PASSWORD'}


def prepare(root=ROOT, *, existing_data=False):
    """Retain each password with its database; accept the old private .env once."""
    values = {}
    for name, variable in PASSWORDS.items():
        path = root / name / 'password'
        supplied = os.getenv(variable, '')
        existing = path.read_text().strip() if path.exists() else ''
        if existing_data and not existing and not supplied:
            print('Existing SQL data needs its original private .env on first upgrade; nothing was reset.')
            raise ValueError('Missing original local credentials')
        if supplied and existing and supplied != existing:
            raise ValueError('Local credentials differ from the retained volume; no password was changed')
        value = existing or supplied or 'Aa1' + secrets.token_hex(24)
        if not re.fullmatch(r'Aa1[0-9a-f]{48}', value):
            raise ValueError('Local credentials must use the configure_local.py password format')
        values[name] = value
    # Validate all inputs before changing any credential volume.
    for name, value in values.items():
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        os.chown(directory, 10001, 10001)
        directory.chmod(0o700)
        path = directory / 'password'
        if not path.exists():
            with open(path, 'x', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
                stream.write(value)
        os.chown(path, 10001, 10001)
        path.chmod(0o600)
    (root / 'sql' / 'ready').touch()
    return values


def sql_environment():
    return {**os.environ, 'SQLCMDPASSWORD': (ROOT / 'sql/password').read_text().strip()}


def wait_for_credentials():
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if (ROOT / 'sql/ready').exists() and (ROOT / 'sql/password').exists():
            return
        time.sleep(0.2)
    raise RuntimeError('Local credential initialization did not finish')


def initialize():
    values = prepare(existing_data=Path('/var/opt/mssql/data/master.mdf').exists())
    environment = {**os.environ, 'SQLCMDPASSWORD': values['sql'],
                   'RESTAURANTS_PASSWORD': values['restaurants'], 'DINING_PASSWORD': values['dining']}
    args = [SQLCMD, '-S', 'sql', '-U', 'sa', '-C', '-b', '-l', '3', '-t', '5']
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        result = subprocess.run(args + ['-Q', 'SELECT 1', '-o', '/dev/null'], env=environment,
                                capture_output=True, timeout=12)
        if result.returncode == 0:
            break
        time.sleep(2)
    else:
        raise RuntimeError('Local SQL did not become ready; retained data and credentials were not reset')
    result = subprocess.run(args + ['-i', '/init.sql'], env=environment, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Local database initialization failed; SQL output suppressed to protect credentials')
    print('Local credentials retained; own databases and logins initialized.')


def main():
    mode = sys.argv[1]
    if mode == 'init':
        initialize()
    elif mode == 'server':
        wait_for_credentials()
        environment = {**os.environ, 'MSSQL_SA_PASSWORD': (ROOT / 'sql/password').read_text().strip()}
        os.execve('/opt/mssql/bin/sqlservr', ['sqlservr'], environment)
    elif mode in ('sql', 'health'):
        extra = ['-Q', 'SELECT 1', '-o', '/dev/null'] if mode == 'health' else sys.argv[2:]
        os.execve(SQLCMD, [SQLCMD, '-S', 'localhost', '-U', 'sa', '-C', '-b', *extra], sql_environment())
    else:
        raise ValueError('Unknown local bootstrap action')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        # Do not print exception details that could contain credentials/SQL.
        raise SystemExit('Local bootstrap failed; check configuration and retained volumes without resetting data.') from None
