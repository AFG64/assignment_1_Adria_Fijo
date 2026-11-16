"""Bounded SQL connections and atomic, checksummed forward migrations."""
import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pymssql

LOG = logging.getLogger(__name__)


def connect(database_url, *, attempts=1):
    url = urlsplit(database_url)
    if url.scheme != 'mssql' or not url.hostname or not url.username or not url.password or not url.path.strip('/'):
        raise ValueError('DATABASE_URL must be mssql://user:password@host:port/database')
    for attempt in range(attempts):
        try:
            return pymssql.connect(
                server=url.hostname, port=str(url.port or 1433),
                user=unquote(url.username), password=unquote(url.password),
                database=unquote(url.path.lstrip('/')), login_timeout=5, timeout=5,
                tds_version='7.4', encryption='require', autocommit=False,
            )
        except pymssql.OperationalError:
            if attempt + 1 == attempts:
                raise
            delay = min(2 ** attempt, 8)
            LOG.warning('database connection retry attempt=%d delay_s=%d', attempt + 1, delay)
            time.sleep(delay)
    raise ValueError('Connection attempts must be positive')


def migrate(database_url, directory):
    connection = connect(database_url, attempts=12)
    try:
        cursor = connection.cursor()
        # Transaction-owned lock also protects local accidental concurrent starts.
        cursor.execute("DECLARE @result int; EXEC @result = sp_getapplock "
                       "@Resource='picky-migrations', @LockMode='Exclusive', "
                       "@LockOwner='Transaction', @LockTimeout=30000; "
                       "IF @result < 0 THROW 50000, 'Migration lock unavailable', 1;")
        cursor.execute("IF OBJECT_ID('dbo.schema_migrations', 'U') IS NULL "
                       "CREATE TABLE dbo.schema_migrations (version nvarchar(200) PRIMARY KEY, "
                       "checksum char(64) NOT NULL, applied_at datetime2 NOT NULL DEFAULT SYSUTCDATETIME());")
        cursor.execute('SELECT version, checksum FROM dbo.schema_migrations')
        applied = dict(cursor.fetchall())
        files = sorted(Path(directory).glob('[0-9][0-9][0-9]_*.sql'))
        if not files:
            raise ValueError('No versioned migrations found')
        available = {file.name for file in files}
        if set(applied) - available:
            raise ValueError('Applied migration missing from image')
        count = 0
        for file in files:
            sql = file.read_text()
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            if file.name in applied:
                if applied[file.name] != checksum:
                    raise ValueError(f'Applied migration changed: {file.name}')
                continue
            if applied and file.name < max(applied):
                raise ValueError('Cannot insert an older migration after an applied migration')
            cursor.execute(sql)
            cursor.execute('INSERT INTO dbo.schema_migrations (version, checksum) VALUES (%s, %s)',
                           (file.name, checksum))
            count += 1
        connection.commit()
        LOG.info('migrations committed applied=%d', count)
        for file in files:
            if file.name not in applied:
                LOG.info('migration applied version=%s', file.name)
        return count
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def probe(database_url):
    connection = connect(database_url)
    try:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO dbo.health_probe (token) OUTPUT INSERTED.id VALUES (%s)', ('probe',))
        row_id = cursor.fetchone()[0]
        cursor.execute('SELECT token FROM dbo.health_probe WHERE id = %s', (row_id,))
        if cursor.fetchone()[0] != 'probe':
            raise RuntimeError('Health read/write mismatch')
    finally:
        # Rollback leaves no probe data behind.
        connection.rollback()
        connection.close()
