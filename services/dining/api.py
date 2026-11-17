"""Own-domain dining API; new visits await milestone 5 coordination."""
from io import BytesIO
import math

from flask import Blueprint, abort, jsonify, request, send_file
import pymssql
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from . import store

api = Blueprint('dining', __name__)
MAX_BILL_BYTES = 5 * 1024 * 1024


def error(code, message, status):
    return jsonify(error=code, message=message, retryable=status == 503 and request.method == 'GET'), status


def register(app):
    app.config['MAX_CONTENT_LENGTH'] = MAX_BILL_BYTES + 64 * 1024
    app.register_blueprint(api)

    @app.errorhandler(ValueError)
    def invalid(exc):
        return error('invalid_input', 'Check the request fields and values.', 400)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return error('http_error', exc.description, exc.code)

    @app.errorhandler(pymssql.DatabaseError)
    def database_error(exc):
        app.logger.warning('dining database request failed')
        return error('database_unavailable', 'Dining data is temporarily unavailable.', 503)


def require_visit(cursor, saved_id, visit_id):
    if not store.visit(cursor, saved_id, visit_id):
        abort(404)


@api.get('/saved-restaurants/<int:saved_id>/visits')
def visits(saved_id):
    with store.transaction() as cursor:
        return jsonify(store.history(cursor, saved_id))


@api.post('/saved-restaurants/<int:saved_id>/visits')
def create_visit(saved_id):
    return error('coordination_pending', 'Recording visits awaits restaurant coordination.', 503)


@api.delete('/saved-restaurants/<int:saved_id>/history')
def delete_history(saved_id):
    # Keep deletion gated until the saved-entry concurrency protocol is implemented.
    return error('coordination_pending', 'Removal awaits restaurant coordination.', 503)


@api.post('/saved-restaurants/<int:saved_id>/visits/<int:visit_id>/items')
def add_item(saved_id, visit_id):
    data = request.get_json()
    if not isinstance(data, dict) or set(data) - {'item_name', 'quantity', 'unit_price'}:
        raise ValueError('Unknown fields')
    name = data.get('item_name')
    quantity = data.get('quantity', 1)
    price = data.get('unit_price')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 300:
        raise ValueError('Invalid item name')
    if type(quantity) is not int or not 1 <= quantity <= 2147483647:
        raise ValueError('Invalid quantity')
    if price is not None and (type(price) not in (int, float) or not 0 <= price <= 9999999999.99 or not math.isfinite(price)):
        raise ValueError('Invalid price')
    with store.transaction() as cursor:
        require_visit(cursor, saved_id, visit_id)
        cursor.execute('INSERT INTO dbo.visit_items (visit_id,item_name,quantity,unit_price) OUTPUT INSERTED.id VALUES (%s,%s,%s,%s)', (visit_id, name.strip(), quantity, price))
        item_id = cursor.fetchone()['id']
        cursor.execute('SELECT id,visit_id,item_name,quantity,unit_price FROM dbo.visit_items WHERE id=%s', (item_id,))
        row = cursor.fetchone()
        if row['unit_price'] is not None:
            row['unit_price'] = float(row['unit_price'])
        return jsonify(row), 201


@api.post('/saved-restaurants/<int:saved_id>/visits/<int:visit_id>/bills')
def upload(saved_id, visit_id):
    file = request.files.get('bill_file')
    if file is None or not file.filename:
        raise ValueError('Choose a bill')
    content = file.stream.read(MAX_BILL_BYTES + 1)
    if len(content) > MAX_BILL_BYTES:
        abort(413)
    media = store.bill_type(content)
    name = secure_filename(file.filename)[:255] or 'bill'
    with store.transaction() as cursor:
        require_visit(cursor, saved_id, visit_id)
        cursor.execute('INSERT INTO dbo.bills (visit_id,content,media_type,original_name) OUTPUT INSERTED.id VALUES (%s,CONVERT(varbinary(max),%s,2),%s,%s)', (visit_id, content.hex(), media, name))
        return jsonify(id=cursor.fetchone()['id'], visit_id=visit_id), 201


@api.get('/saved-restaurants/<int:saved_id>/visits/<int:visit_id>/bills/<int:bill_id>')
def download(saved_id, visit_id, bill_id):
    with store.transaction() as cursor:
        require_visit(cursor, saved_id, visit_id)
        cursor.execute('SELECT content,media_type,original_name FROM dbo.bills WHERE id=%s AND visit_id=%s', (bill_id, visit_id))
        row = cursor.fetchone()
        if row is None:
            abort(404)
    response = send_file(BytesIO(row['content']), mimetype=row['media_type'], as_attachment=True, download_name=row['original_name'])
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response
