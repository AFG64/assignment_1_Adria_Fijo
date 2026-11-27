"""Dining-owned SQL operations. Saved IDs are external references."""
from contextlib import contextmanager
from datetime import datetime
import os
from zoneinfo import ZoneInfo

from service_runtime.database import connect


@contextmanager
def transaction():
    connection = connect(os.environ['DATABASE_URL'])
    try:
        yield connection.cursor(as_dict=True)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def visit(cursor, saved_id, visit_id):
    cursor.execute('SELECT id FROM dbo.visits WHERE id=%s AND saved_restaurant_id=%s', (visit_id, saved_id))
    return cursor.fetchone()


def item_response(row):
    result = dict(row)
    for field in ('unit_price', 'line_total'):
        if result[field] is not None:
            result[field] = float(result[field])
    return result


def history(cursor, saved_id):
    cursor.execute('SELECT id,saved_restaurant_id,visit_date,rating,notes FROM dbo.visits WHERE saved_restaurant_id=%s ORDER BY visit_date DESC,id DESC', (saved_id,))
    visits = cursor.fetchall()
    for row in visits:
        row['visit_date'] = row['visit_date'].isoformat()
        for table, fields in [('visit_items', 'id,visit_id,item_name,quantity,unit_price,line_total'), ('bills', 'id,visit_id')]:
            cursor.execute(f'SELECT {fields} FROM dbo.{table} WHERE visit_id=%s ORDER BY id', (row['id'],))
            rows = cursor.fetchall()
            if table == 'visit_items':
                rows = [item_response(item) for item in rows]
            row['items' if table == 'visit_items' else 'bills'] = rows
    return visits


def bill_type(content):
    for signature, media in [(b'\x89PNG\r\n\x1a\n', 'image/png'), (b'\xff\xd8\xff', 'image/jpeg'), (b'%PDF-', 'application/pdf')]:
        if content.startswith(signature):
            return media
    raise ValueError('Upload a PNG, JPEG or PDF bill')


def journal_today():
    return datetime.now(ZoneInfo('Europe/Madrid')).date()


def validate_visit(saved_id, visit_date, rating=None, notes=None):
    """Validate the visit payload before any peer side effect."""
    import datetime
    import math
    if type(saved_id) is not int or not 1 <= saved_id <= 2147483647:
        raise ValueError('Invalid saved ID')
    if not isinstance(visit_date, str):
        raise ValueError('Expected ISO date')
    date = datetime.date.fromisoformat(visit_date)
    if date.isoformat() != visit_date or date > journal_today():
        raise ValueError('Visit date must not be in the future')
    if rating is not None and (type(rating) not in (int, float) or not 0 <= rating <= 5 or not math.isfinite(rating)):
        raise ValueError('Invalid rating')
    if notes is not None and (not isinstance(notes, str) or len(notes) > 2000):
        raise ValueError('Invalid notes')


def record_visit(cursor, saved_id, visit_date, rating=None, notes=None):
    validate_visit(saved_id, visit_date, rating, notes)
    cursor.execute('INSERT INTO dbo.visits (saved_restaurant_id,visit_date,rating,notes) OUTPUT INSERTED.id VALUES (%s,%s,%s,%s)', (saved_id, visit_date, rating, notes))
    return cursor.fetchone()['id']


def lock_saved(cursor, saved_id):
    cursor.execute("DECLARE @r int; EXEC @r=sp_getapplock @Resource=%s, @LockMode='Exclusive', "
                   "@LockOwner='Transaction', @LockTimeout=2000; "
                   "IF @r<0 THROW 50001, 'Saved entry busy; retry later', 1;", (f'saved:{saved_id}',))
