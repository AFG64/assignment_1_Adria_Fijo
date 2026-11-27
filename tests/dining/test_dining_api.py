from contextlib import contextmanager, closing
from io import BytesIO
from unittest.mock import MagicMock
import datetime
from decimal import Decimal

from flask import Flask
import pymssql
import pytest

from services.dining import api, store
from scripts.transfer_assignment1 import transfer_domain


@pytest.fixture
def client(monkeypatch):
    cursor = MagicMock()
    @contextmanager
    def transaction():
        yield cursor
    monkeypatch.setattr(store, 'transaction', transaction)
    app = Flask(__name__)
    api.register(app)
    return app.test_client(), cursor


def test_history(client):
    web, cursor = client
    cursor.fetchall.side_effect = [[dict(id=1, saved_restaurant_id=2, visit_date=datetime.date(2026, 1, 1), rating=4, notes=None)], [dict(unit_price=Decimal('2.00'), line_total=Decimal('6.00'))], []]
    response = web.get('/saved-restaurants/2/visits')
    assert response.status_code == 200
    assert response.json[0]['visit_date'] == '2026-01-01'
    assert response.json[0]['items'][0]['unit_price'] == 2
    assert response.json[0]['items'][0]['line_total'] == 6
    assert web.post('/saved-restaurants/2/visits', json={}).status_code == 400
    assert web.delete('/saved-restaurants/2/history').status_code == 204


@pytest.mark.parametrize('data', [{}, [], {'item_name':' '}, {'item_name':'x','extra':1}, {'item_name':'x','line_total':1}, {'item_name':'x','quantity':True}, {'item_name':'x','quantity':0}, {'item_name':'x','unit_price':-1}, {'item_name':'x','unit_price':'nan'}, {'item_name':'x','unit_price':float('inf')}, {'item_name':'x','unit_price':10**400}])
def test_invalid_item(client, data):
    assert client[0].post('/saved-restaurants/2/visits/1/items', json=data).status_code == 400


def test_items_and_ownership(client):
    web, cursor = client
    cursor.fetchone.side_effect = [dict(id=1), dict(id=3), dict(id=3,visit_id=1,item_name='Soup',quantity=1,unit_price=Decimal('2.00'),line_total=Decimal('2.00'))]
    result = web.post('/saved-restaurants/2/visits/1/items', json={'item_name':'Soup','unit_price':2})
    assert result.status_code == 201 and result.json['unit_price'] == 2 and result.json['line_total'] == 2
    cursor.fetchone.side_effect = lambda: None
    assert web.post('/saved-restaurants/9/visits/1/items', json={'item_name':'Soup'}).status_code == 404


@pytest.mark.parametrize('price,total', [(None,None), (Decimal('0.00'),Decimal('0.00')),
    (Decimal('0.10'),Decimal('0.30')), (Decimal('3.50'),Decimal('7.00')),
    (Decimal('9999999999.99'),Decimal('21474836469978525163.53'))])
def test_item_numbers_are_serialized_without_changing_the_database_row(price, total):
    row = {'id':1, 'unit_price':price, 'line_total':total}
    result = store.item_response(row)
    assert result == {'id':1, 'unit_price':None if price is None else float(price),
                      'line_total':None if total is None else float(total)}
    assert row == {'id':1, 'unit_price':price, 'line_total':total}


@pytest.mark.parametrize('content,media', [(b'%PDF-test','application/pdf'),(b'\xff\xd8\xfftest','image/jpeg'),(b'\x89PNG\r\n\x1a\ntest','image/png')])
def test_bill_roundtrip(client, content, media):
    web,cursor=client
    cursor.fetchone.side_effect=[dict(id=1),dict(id=3)]
    response=web.post('/saved-restaurants/2/visits/1/bills',data={'bill_file':(BytesIO(content),'bill.pdf')})
    assert response.status_code == 201
    assert cursor.execute.call_args.args[1][1:3] == (content.hex(),media)
    cursor.fetchone.side_effect=[dict(id=1),dict(content=content,media_type=media,original_name='bill.pdf')]
    response=web.get('/saved-restaurants/2/visits/1/bills/3')
    assert response.data == content and response.headers['Cache-Control']=='no-store'
    cursor.fetchone.side_effect=[dict(id=1),None]
    assert web.get('/saved-restaurants/2/visits/1/bills/9').status_code==404


def test_invalid_bills_and_sql_failure(client):
    web,cursor=client
    path='/saved-restaurants/2/visits/1/bills'
    assert web.post(path).status_code==400
    assert web.post(path,data={'bill_file':(BytesIO(b'bad'),'x')}).status_code==400
    assert web.post(path,data={'bill_file':(BytesIO(b'x'*(api.MAX_BILL_BYTES+1)),'x')}).status_code==413
    cursor.execute.side_effect=pymssql.OperationalError('secret')
    response=web.get('/saved-restaurants/2/visits')
    assert response.status_code==503 and 'secret' not in response.text
    assert response.json['retryable'] is True
    response=web.post(path,data={'bill_file':(BytesIO(b'%PDF-retry'),'test.pdf')})
    assert response.status_code==503 and response.json['retryable'] is False


def test_transaction(monkeypatch):
    connection=MagicMock()
    monkeypatch.setenv('DATABASE_URL','unused')
    monkeypatch.setattr(store,'connect',lambda _:connection)
    with store.transaction():
        pass
    connection.commit.assert_called_once()
    with pytest.raises(ValueError), store.transaction():
        raise ValueError()
    connection.rollback.assert_called_once()
    assert connection.close.call_count==2


def test_transfer_repeat_conflict_and_rollback():
    connection=MagicMock()
    cursor=connection.cursor.return_value
    snapshot={'visits':[{'id':1,'notes':'test'}]}
    cursor.fetchone.return_value=None
    transfer_domain(connection,['visits'],snapshot)
    assert any('INSERT INTO' in call.args[0] for call in cursor.execute.call_args_list)
    cursor.fetchone.return_value={'id':1,'notes':'test'}
    transfer_domain(connection,['visits'],snapshot)
    cursor.fetchone.return_value={'id':1,'notes':'different'}
    with pytest.raises(ValueError):
        transfer_domain(connection,['visits'],snapshot)
    connection.rollback.assert_called_once()


def test_snapshot_copy_integrity_and_bills(tmp_path):
    import sqlite3
    from pathlib import Path
    from scripts.transfer_assignment1 import load_snapshot
    source=tmp_path/'copy.sqlite3'
    with closing(sqlite3.connect(source)) as db, db:
        db.executescript(Path('database/schema.sql').read_text())
        db.execute("INSERT INTO restaurants (id,title) VALUES (1,'Test')")
        db.execute('INSERT INTO saved_restaurants (id,restaurant_id) VALUES (2,1)')
        db.execute('INSERT INTO visits (id,saved_restaurant_id) VALUES (3,2)')
        db.execute("INSERT INTO bills (id,visit_id,image_path) VALUES (4,3,'bills/test.pdf')")
    (tmp_path/'bills').mkdir()
    (tmp_path/'bills/test.pdf').write_bytes(b'%PDF-copy\x00\xff')
    snapshot=load_snapshot(source)
    assert snapshot['bills'][0]['content']==b'%PDF-copy\x00\xff'
    assert snapshot['visits'][0]['saved_restaurant_id']==2
    (tmp_path/'bills/test.pdf').unlink()
    with pytest.raises(FileNotFoundError):
        load_snapshot(source)
    with closing(sqlite3.connect(source)) as db, db:
        db.execute("UPDATE bills SET image_path='../outside.pdf'")
    with pytest.raises(ValueError):
        load_snapshot(source)


def test_record_visit():
    cursor=MagicMock()
    cursor.fetchone.return_value={'id':4}
    assert store.record_visit(cursor,2,'2026-01-01',4,'Nice')==4
    assert cursor.execute.call_args.args[1]==(2,'2026-01-01',4,'Nice')


@pytest.mark.parametrize('saved,date,rating,notes', [(True,'2026-01-01',None,None),(1,None,None,None),(1,'2026-1-1',None,None),(1,'9999-01-01',None,None),(1,'2026-01-01',True,None),(1,'2026-01-01',6,None),(1,'2026-01-01',None,7)])
def test_invalid_visit(saved,date,rating,notes):
    with pytest.raises(ValueError):
        store.record_visit(MagicMock(),saved,date,rating,notes)


def test_madrid_midnight_is_not_rejected_as_tomorrow_in_utc(monkeypatch):
    from services.dining import store
    instant = datetime.datetime(2026, 11, 19, 23, 30, tzinfo=datetime.timezone.utc)

    class Clock(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz)

    monkeypatch.setattr(store, 'datetime', Clock)
    assert store.journal_today() == datetime.date(2026, 11, 20)
    store.validate_visit(1, '2026-11-20')
    with pytest.raises(ValueError, match='future'):
        store.validate_visit(1, '2026-11-21')
