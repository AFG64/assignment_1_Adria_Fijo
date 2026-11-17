"""JSON collection API. Cross-service deletion is gated until milestone 5."""
import math

from flask import Blueprint, jsonify, request
import pymssql
from werkzeug.exceptions import HTTPException

from . import catalog
from .geocoding import locate

api = Blueprint('restaurants', __name__)


def text(value, limit, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise ValueError(f'Expected text of at most {limit} characters')
    return value.strip() or None


def number(value, minimum, maximum, integer=False, query=False):
    if value is None:
        return None
    if isinstance(value, bool) or (not query and not isinstance(value, (int, float))):
        raise ValueError('Expected a number')
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('Expected a finite number') from exc
    if not math.isfinite(result) or not minimum <= result <= maximum or (integer and result != int(result)):
        raise ValueError('Number outside allowed range')
    return int(result) if integer else result


def body(allowed, required=()):
    data = request.get_json()
    if not isinstance(data, dict) or set(data) - set(allowed) or set(required) - set(data):
        raise ValueError('Missing or unknown fields')
    return data


def status(value):
    if value not in ('want_to_go', 'visited'):
        raise ValueError('Invalid saved status')
    return value


def found(value):
    if value is None:
        from flask import abort
        abort(404)
    return value


def error(code, message, http_status, retryable=False):
    return jsonify(error=code, message=message, retryable=retryable), http_status


def register(app):
    app.register_blueprint(api)

    @app.errorhandler(ValueError)
    @app.errorhandler(TypeError)
    def invalid(exc):
        return error('invalid_input', 'Check the request fields and values.', 400)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return error('http_error', exc.description, exc.code)

    @app.errorhandler(pymssql.DatabaseError)
    def database_error(exc):
        app.logger.warning('restaurant database request failed')
        return error('database_unavailable', 'Restaurant data is temporarily unavailable.', 503)

    @app.errorhandler(pymssql.IntegrityError)
    def conflict(exc):
        return error('conflict', 'This restaurant is already saved or the record changed.', 409)


@api.get('/restaurants')
def list_restaurants():
    filters = {key: text(request.args.get(key), 200) for key in ('category', 'city')}
    filters['price'] = number(request.args.get('price'), 1, 4, True, query=True)
    filters['min_rating'] = number(request.args.get('min_rating'), 0, 5, query=True)
    filters['status'] = request.args.get('status')
    if filters['status'] not in (None, 'not_saved', 'want_to_go', 'visited'):
        raise ValueError('Invalid saved filter')
    with catalog.transaction() as cursor:
        return jsonify(catalog.listing(cursor, filters))


@api.get('/saved-restaurants')
def saved_restaurants():
    with catalog.transaction() as cursor:
        return jsonify(catalog.listing(cursor, {}, saved_only=True))


@api.get('/restaurants/<int:restaurant_id>')
def detail(restaurant_id):
    with catalog.transaction() as cursor:
        return jsonify(found(catalog.get_restaurant(cursor, restaurant_id)))


@api.post('/restaurants')
def create():
    data = body(['title', 'category_name', 'city', 'price', 'rating', 'notes', 'status', 'address'], ['title'])
    data['title'] = text(data['title'], 300, True)
    for key, limit in [('category_name', 200), ('city', 200), ('notes', 2000), ('address', 300)]:
        data[key] = text(data.get(key), limit)
    data['price'] = number(data.get('price'), 1, 4, True)
    data['rating'] = number(data.get('rating'), 0, 5)
    data['status'] = status(data.get('status', 'want_to_go'))
    if data['address']:
        data.update(locate(data['address'], data['city']))
    with catalog.transaction() as cursor:
        return jsonify(catalog.create(cursor, data)), 201


@api.post('/restaurants/<int:restaurant_id>/saved-entry')
def save(restaurant_id):
    data = body(['status'], ['status'])
    value = status(data['status'])
    with catalog.transaction() as cursor:
        found(catalog.get_restaurant(cursor, restaurant_id))
        cursor.execute('INSERT INTO dbo.saved_restaurants (restaurant_id,status) VALUES (%s,%s)', (restaurant_id, value))
        return jsonify(catalog.get_restaurant(cursor, restaurant_id)['saved']), 201


@api.get('/saved-restaurants/<int:saved_id>')
def saved_entry(saved_id):
    with catalog.transaction() as cursor:
        return jsonify(found(catalog.get_saved(cursor, saved_id)))


@api.patch('/saved-restaurants/<int:saved_id>')
def update_saved(saved_id):
    data = body(['rating', 'notes', 'would_go_back'], ['rating', 'notes', 'would_go_back'])
    rating = number(data['rating'], 0, 5)
    notes = text(data['notes'], 2000)
    preference = data['would_go_back']
    if preference is not None and not isinstance(preference, bool):
        raise ValueError('Expected boolean or null')
    with catalog.transaction() as cursor:
        found(catalog.get_saved(cursor, saved_id))
        cursor.execute('UPDATE dbo.saved_restaurants SET rating=%s,notes=%s,would_go_back=%s WHERE id=%s', (rating, notes, preference, saved_id))
        return jsonify(catalog.get_saved(cursor, saved_id))


@api.put('/saved-restaurants/<int:saved_id>/visited')
def visited(saved_id):
    with catalog.transaction() as cursor:
        found(catalog.get_saved(cursor, saved_id))
        cursor.execute("UPDATE dbo.saved_restaurants SET status='visited' WHERE id=%s", (saved_id,))
        return jsonify(catalog.get_saved(cursor, saved_id))


@api.put('/restaurants/<int:restaurant_id>/location')
def location(restaurant_id):
    data = body(['mode', 'address', 'latitude', 'longitude'], ['mode', 'address'])
    address = text(data['address'], 300, True)
    with catalog.transaction() as cursor:
        restaurant = found(catalog.get_restaurant(cursor, restaurant_id))
    if data['mode'] == 'search' and set(data) == {'mode', 'address'}:
        coordinates = locate(address, restaurant['city'])
    elif data['mode'] == 'manual' and set(data) == {'mode', 'address', 'latitude', 'longitude'}:
        coordinates = {'latitude': number(data['latitude'], -90, 90), 'longitude': number(data['longitude'], -180, 180)}
        if None in coordinates.values():
            raise ValueError('Both coordinates required')
    else:
        raise ValueError('Invalid location mode or fields')
    with catalog.transaction() as cursor:
        found(catalog.get_restaurant(cursor, restaurant_id))
        cursor.execute('UPDATE dbo.restaurants SET address=%s,latitude=%s,longitude=%s WHERE id=%s', (address, coordinates['latitude'], coordinates['longitude'], restaurant_id))
    return jsonify(address=address, **coordinates)


@api.delete('/saved-restaurants/<int:saved_id>')
def remove(saved_id):
    # Never silently orphan dining data while HTTP coordination is not implemented.
    with catalog.transaction() as cursor:
        found(catalog.get_saved(cursor, saved_id))
    return error('coordination_pending', 'Removal is unavailable until dining cleanup is connected.', 503)
