"""Run inside the Dining image through check_item_migration.py; LOCAL SQL only."""
from contextlib import closing
from decimal import Decimal
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit

from service_runtime.database import connect, migrate, probe


def snapshot(url):
    result = {}
    with closing(connect(url)) as connection:
        cursor = connection.cursor()
        for table, fields in (
            ('visits', 'id,saved_restaurant_id,visit_date,rating,notes,total_amount,number_of_people,would_go_back,created_at'),
            ('visit_items', 'id,visit_id,item_name,quantity,unit_price,rating,notes'),
            ('bills', 'id,visit_id,content,media_type,original_name,extracted_total,extracted_text,uploaded_at'),
        ):
            cursor.execute(f'SELECT {fields} FROM dbo.{table} ORDER BY id')
            result[table] = cursor.fetchall()
    return result


def ledger(url):
    with closing(connect(url)) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT version,checksum,applied_at FROM dbo.schema_migrations ORDER BY version')
        return cursor.fetchall()


def main():
    name, bill_hex = sys.argv[1:]
    assert re.fullmatch(r'picky_item_migration_[0-9a-f]{32}', name)
    assert urlsplit(os.environ['DATABASE_URL']).hostname == 'sql', 'LOCAL SQL only'
    url = os.environ['DATABASE_URL'].rsplit('/', 1)[0] + '/' + name
    folder = Path('/app/migrations')
    assert sorted(path.name for path in folder.glob('*.sql')) == ['001_init.sql', '002_add_item_line_total.sql']
    cases = [('Baseline soup', 2, Decimal('3.50')), ('Unknown price', 1, None),
             ('Free item', 3, Decimal('0.00')), ('Fractional price', 3, Decimal('0.10')),
             ('Maximum inputs', 2147483647, Decimal('9999999999.99'))]

    with tempfile.TemporaryDirectory() as directory:
        first = Path(directory)
        shutil.copyfile(folder / '001_init.sql', first / '001_init.sql')
        assert migrate(url, first) == 1
        with closing(connect(url)) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO dbo.visits(saved_restaurant_id,visit_date,rating,notes) OUTPUT INSERTED.id VALUES (1,'2026-11-01',4,'Migration baseline')")
            visit_id = cursor.fetchone()[0]
            for label, quantity, price in cases:
                cursor.execute('INSERT INTO dbo.visit_items(visit_id,item_name,quantity,unit_price) VALUES (%s,%s,%s,%s)', (visit_id, label, quantity, price))
            cursor.execute("INSERT INTO dbo.bills(visit_id,content,media_type,original_name) VALUES (%s,CONVERT(varbinary(max),%s,2),'application/pdf','baseline.pdf')", (visit_id, bill_hex))
            connection.commit()
        before, original_ledger = snapshot(url), ledger(url)
        assert migrate(url, folder) == 1
        assert snapshot(url) == before, 'Upgrade changed original rows or bill bytes'
        expected = [(label, None if price is None else quantity * price) for label, quantity, price in cases]
        with closing(connect(url)) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT item_name,line_total FROM dbo.visit_items ORDER BY id')
            assert cursor.fetchall() == expected
            cursor.execute("SELECT is_persisted,precision,scale FROM sys.computed_columns WHERE object_id=OBJECT_ID('dbo.visit_items') AND name='line_total'")
            assert cursor.fetchone() == (True, 23, 2)
            cursor.execute("UPDATE dbo.visit_items SET quantity=3,unit_price=4.50 WHERE item_name='Baseline soup'")
            cursor.execute("SELECT line_total FROM dbo.visit_items WHERE item_name='Baseline soup'")
            assert cursor.fetchone()[0] == Decimal('13.50')
            connection.rollback()
            cursor.execute('INSERT INTO dbo.visit_items(visit_id,item_name,quantity,unit_price) OUTPUT INSERTED.line_total VALUES (%s,%s,4,2.75)', (visit_id, 'New item'))
            assert cursor.fetchone()[0] == Decimal('11.00')
            connection.rollback()
        applied = ledger(url)
        assert applied[:1] == original_ledger and len(applied) == 2
        assert migrate(url, folder) == 0
        assert snapshot(url) == before and ledger(url) == applied
        probe(url)
    print('Populated 001 to 002: original rows/PDF/ledger retained; persisted totals, null/zero/fraction/max inputs, new writes and repeat no-op passed')


if __name__ == '__main__':
    main()
