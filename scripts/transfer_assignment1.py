"""Offline, repeatable split from an SQLite COPY into isolated service databases.

Run with writes stopped. Existing differing IDs are rejected, never overwritten.
Each domain commits independently; rerunning safely completes an interrupted split.
Connection URLs come only from environment variables, never CLI arguments.
"""
import argparse
from contextlib import closing
from decimal import Decimal
import datetime
import os
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service_runtime.database import connect

GROUPS = {
    'RESTAURANTS_DATABASE_URL': ['restaurants', 'saved_restaurants', 'restaurant_images', 'restaurant_emails'],
    'DINING_DATABASE_URL': ['visits', 'visit_items', 'bills'],
}


def normalize(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat(sep=' ') if isinstance(value, datetime.datetime) else value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def load_snapshot(source):
    """Read a copied SQLite database read-only and validate all source relations."""
    from services.dining.store import bill_type

    source = Path(source).resolve()
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Source integrity check failed')
        result = {table: [dict(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY id')]
                  for tables in GROUPS.values() for table in tables}
    for row in result['bills']:
        relative = Path(row.pop('image_path'))
        candidate = source.parent / relative
        if candidate.is_symlink():
            raise ValueError('Bill symlinks are not supported')
        path = candidate.resolve()
        root = (source.parent / 'bills').resolve()
        if path.parent != root or path.is_symlink():
            raise ValueError('Bill must be inside copied bills directory')
        content = path.read_bytes()
        if not 1 <= len(content) <= 5242880:
            raise ValueError('Bill exceeds size limit')
        row.update(content=content, media_type=bill_type(content), original_name=path.name)
    return result


def transfer_domain(connection, tables, snapshot):
    """Compare every field on repeats, including bill bytes; preserve original IDs."""
    cursor = connection.cursor(as_dict=True)
    try:
        cursor.execute("DECLARE @r int; EXEC @r=sp_getapplock @Resource='picky-transfer', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=30000; IF @r<0 THROW 50000,'Transfer lock unavailable',1;")
        for table in tables:
            cursor.execute(f'SET IDENTITY_INSERT dbo.{table} ON')
            try:
                for row in snapshot[table]:
                    columns = list(row)
                    cursor.execute(f"SELECT {','.join(columns)} FROM dbo.{table} WITH (UPDLOCK,HOLDLOCK) WHERE id=%s", (row['id'],))
                    existing = cursor.fetchone()
                    if existing is not None:
                        if any(normalize(existing[key]) != normalize(value) for key, value in row.items()):
                            raise ValueError(f'Conflicting existing ID in {table}: {row["id"]}')
                        continue
                    placeholders = ['CONVERT(varbinary(max),%s,2)' if key == 'content' else '%s' for key in columns]
                    values = tuple(value.hex() if key == 'content' else value for key, value in row.items())
                    cursor.execute(f"INSERT INTO dbo.{table} ({','.join(columns)}) VALUES ({','.join(placeholders)})", values)
            finally:
                cursor.execute(f'SET IDENTITY_INSERT dbo.{table} OFF')
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path, help='SQLite backup beside a copied bills/ directory')
    parser.add_argument('--apply', action='store_true', help='Write to configured, quiescent targets; default only validates source')
    args = parser.parse_args()
    snapshot = load_snapshot(args.snapshot)
    print({table: len(rows) for table, rows in snapshot.items()})
    if args.apply:
        for variable, tables in GROUPS.items():
            with closing(connect(os.environ[variable])) as connection:
                transfer_domain(connection, tables, snapshot)
        print('Both domains transferred; repeated IDs and contents verified.')


if __name__ == '__main__':
    main()
