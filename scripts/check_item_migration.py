"""Check populated Dining migrations using a disposable LOCAL SQL database."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_baseline import BILL


def sql(statement):
    result = subprocess.run(
        ['docker', 'compose', 'exec', '-T', 'sql', 'python3', '/local/bootstrap.py', 'sql'],
        input=statement, text=True, capture_output=True, timeout=120,
    )
    if result.returncode:
        raise RuntimeError('Local fixture setup failed; SQL output suppressed')


def main():
    config = json.loads(subprocess.check_output(['docker', 'compose', 'config', '--format', 'json'], text=True))
    if config['services']['sql']['image'] != 'mcr.microsoft.com/mssql/server:2022-latest':
        raise RuntimeError('This check requires the project LOCAL SQL container')
    name = 'picky_item_migration_' + uuid4().hex
    created = False
    try:
        sql(f'CREATE DATABASE [{name}];')
        created = True
        sql(f'USE [{name}]; CREATE USER picky_dining FOR LOGIN picky_dining; '
            'ALTER ROLE db_owner ADD MEMBER picky_dining;')
        subprocess.run(
            ['docker', 'compose', 'run', '--rm', '--no-deps', '-T', 'dining', 'python', '-', name, BILL.hex()],
            input=Path(__file__).with_name('sql_item_migration.py').read_text(), text=True, check=True, timeout=240,
        )
    finally:
        if created:
            sql(f'ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [{name}];')


if __name__ == '__main__':
    main()
