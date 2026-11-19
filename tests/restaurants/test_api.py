from contextlib import contextmanager
from unittest.mock import MagicMock

from flask import Flask
import pymssql
import pytest

from services.restaurants import api, catalog, geocoding, seed


@pytest.fixture
def client(monkeypatch):
    cursor = MagicMock()
    row = dict(id=1, title='Place', category_name='Tapas', city='Madrid', price=2,
               address='Street', latitude=40., longitude=-3., saved_id=10,
               status='want_to_go', rating=None, notes=None, would_go_back=None)
    cursor.fetchone.side_effect = lambda: dict(row)
    cursor.fetchall.side_effect = lambda: [dict(row)]
    @contextmanager
    def transaction():
        yield cursor
    monkeypatch.setattr(api, 'call', MagicMock(return_value=None))
    monkeypatch.setattr(catalog, 'transaction', transaction)
    monkeypatch.setattr(seed, 'transaction', transaction)
    app = Flask(__name__)
    api.register(app)
    return app.test_client(), cursor


@pytest.mark.parametrize('method,path,data,code', [
 ('get','/restaurants',None,200),
 ('get','/restaurants?category=Tap&city=Mad&price=2&min_rating=0&status=visited',None,200),
 ('get','/restaurants?status=not_saved',None,200),
 ('get','/saved-restaurants',None,200),
 ('get','/restaurants/1',None,200),
 ('get','/saved-restaurants/10',None,200),
 ('post','/restaurants',{'title':'New'},201),
 ('post','/restaurants/1/saved-entry',{'status':'visited'},201),
 ('patch','/saved-restaurants/10',{'rating':4,'notes':'nice','would_go_back':True},200),
 ('put','/saved-restaurants/10/visited',None,200),
 ('put','/restaurants/1/location',{'mode':'manual','address':'Test','latitude':40,'longitude':-3},200),
 ('delete','/saved-restaurants/10',None,204),
])
def test_operations(client,method,path,data,code):
    web,cursor=client
    response=web.open(path,method=method,json=data)
    assert response.status_code == code, response.json
    assert cursor.execute.called


@pytest.mark.parametrize('method,path,data', [
 ('post','/restaurants',{}),('post','/restaurants',{'title':' '}),
 ('post','/restaurants',{'title':7}),('post','/restaurants',{'title':'x','extra':1}),
 ('post','/restaurants',{'title':'x','notes':'x'*2001}),
 ('post','/restaurants',{'title':'x','price':1.5}),
 ('post','/restaurants',{'title':'x','rating':True}),
 ('post','/restaurants',{'title':'x','rating':'nan'}),
 ('post','/restaurants',{'title':'x','rating':10**400}),
 ('post','/restaurants',{'title':'x','status':'unknown'}),
 ('get','/restaurants?price=5',None),('get','/restaurants?min_rating=nan',None),
 ('get','/restaurants?status=bad',None),('get','/restaurants?price=bad',None),
 ('patch','/saved-restaurants/1',{'rating':None,'notes':None,'would_go_back':1}),
 ('put','/restaurants/1/location',{'mode':'manual','address':'x','latitude':None,'longitude':3}),
 ('put','/restaurants/1/location',{'mode':'other','address':'x'}),
 ('put','/restaurants/1/location',{'mode':'manual','address':'x','latitude':91,'longitude':0}),
 ('post','/restaurants',[]),
])
def test_bad_input(client,method,path,data):
    assert client[0].open(path,method=method,json=data).status_code == 400


def test_missing_record_and_sql_errors(client):
    web,cursor=client
    cursor.fetchone.side_effect=lambda: None
    assert web.get('/restaurants/999').status_code == 404
    cursor.execute.side_effect=pymssql.IntegrityError('private')
    assert web.post('/restaurants',json={'title':'x'}).status_code==409
    cursor.execute.side_effect=pymssql.OperationalError('private')
    response=web.get('/restaurants')
    assert response.status_code==503 and 'private' not in response.text
    assert response.json['retryable'] is False


def test_geocoded_requests(client,monkeypatch):
    lookup=MagicMock(return_value={'latitude':40.,'longitude':-3.})
    monkeypatch.setattr(api,'locate',lookup)
    web,_=client
    assert web.post('/restaurants',json={'title':'x','address':'Test'}).status_code==201
    assert web.put('/restaurants/1/location',json={'mode':'search','address':'Test'}).status_code==200
    lookup.side_effect=ValueError('unavailable')
    assert web.post('/restaurants',json={'title':'x','address':'Test'}).status_code==400


def test_sql_transaction_commit_rollback_and_close(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','unused')
    connection=MagicMock()
    monkeypatch.setattr(catalog,'connect',MagicMock(return_value=connection))
    with catalog.transaction():
        pass
    connection.commit.assert_called_once()
    with pytest.raises(ValueError):
        with catalog.transaction():
            raise ValueError('bad')
    connection.rollback.assert_called_once()
    assert connection.close.call_count==2


def test_seed_reuses_parameterized_insert(client):
    seed.seed()
    assert client[1].execute.call_count == 14
    assert 'IF NOT EXISTS' in client[1].execute.call_args.args[0]


def test_unsaved_shape(client):
    cursor=client[1]
    row=cursor.fetchone()
    row['saved_id']=None
    assert catalog.shape(row)['saved'] is None


def test_geocoder_timeout_cache_and_failure(monkeypatch):
    geocoding.locate.cache_clear()
    response=MagicMock()
    response.__enter__.return_value=response
    monkeypatch.setattr(geocoding,'urlopen',MagicMock(return_value=response))
    monkeypatch.setattr(geocoding.json,'load',lambda _: [{'lat':'40','lon':'-3'}])
    monkeypatch.setattr(geocoding.time,'sleep',MagicMock())
    assert geocoding.locate('Test','Madrid')['latitude']==40
    geocoding.locate('Test','Madrid')
    assert geocoding.urlopen.call_count==1
    assert geocoding.urlopen.call_args.kwargs['timeout']==5
    monkeypatch.setattr(geocoding.json,'load',lambda _: [])
    with pytest.raises(ValueError):
        geocoding.locate('Other')
    geocoding.locate.cache_clear()
