"""Restaurant-owned SQL operations; never reads dining tables."""
from contextlib import contextmanager
import os

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


SELECT = '''SELECT r.id, r.title, r.category_name, r.city, r.price,
 r.address, r.latitude, r.longitude, r.description, r.street, r.postal_code,
 r.state, r.country_code, r.phone, r.website, r.total_score, r.reviews_count, r.menu, r.image_url,
 s.id AS saved_id, s.status,
 s.rating, s.notes, s.would_go_back
 FROM dbo.restaurants r LEFT JOIN dbo.saved_restaurants s ON s.restaurant_id=r.id'''


def shape(row):
    if row is None:
        return None
    row = dict(row)
    saved_id = row.pop('saved_id')
    saved = {key: row.pop(key) for key in ('status', 'rating', 'notes', 'would_go_back')}
    row['saved'] = dict(saved, id=saved_id, restaurant_id=row['id']) if saved_id else None
    return row


def get_restaurant(cursor, restaurant_id):
    cursor.execute(SELECT + ' WHERE r.id=%s', (restaurant_id,))
    return shape(cursor.fetchone())


def get_saved(cursor, saved_id):
    cursor.execute('SELECT id, restaurant_id, status, rating, notes, would_go_back FROM dbo.saved_restaurants WHERE id=%s', (saved_id,))
    return cursor.fetchone()


def listing(cursor, filters, saved_only=False):
    conditions, values = [], []
    for key in ('category', 'city'):
        value = filters.get(key)
        if value:
            column = 'category_name' if key == 'category' else key
            conditions.append(f'CHARINDEX(LOWER(%s), LOWER(r.{column})) > 0')
            values.append(value)
    for key, column in [('price', 'r.price'), ('min_rating', 's.rating')]:
        if filters.get(key) is not None:
            conditions.append(column + (' >= %s' if key == 'min_rating' else ' = %s'))
            values.append(filters[key])
    status = filters.get('status')
    if saved_only:
        conditions.append('s.id IS NOT NULL')
    if status == 'not_saved':
        conditions.append('s.id IS NULL')
    elif status:
        conditions.append('s.status=%s')
        values.append(status)
    where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
    cursor.execute(SELECT + where + ' ORDER BY LOWER(r.title), r.id', tuple(values))
    return [shape(row) for row in cursor.fetchall()]


def create(cursor, data):
    cursor.execute('''INSERT INTO dbo.restaurants (title, category_name, city, price, address, latitude, longitude)
        OUTPUT INSERTED.id VALUES (%s,%s,%s,%s,%s,%s,%s)''',
        tuple(data.get(key) for key in ('title', 'category_name', 'city', 'price', 'address', 'latitude', 'longitude')))
    restaurant_id = cursor.fetchone()['id']
    cursor.execute('''INSERT INTO dbo.saved_restaurants (restaurant_id,status,rating,notes)
        VALUES (%s,%s,%s,%s)''', (restaurant_id, data.get('status', 'want_to_go'), data.get('rating'), data.get('notes')))
    return get_restaurant(cursor, restaurant_id)
