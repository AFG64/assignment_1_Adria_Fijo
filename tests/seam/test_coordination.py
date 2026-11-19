"""Boundary tests: real Flask routes with a peer stub and isolated own transactions."""
from contextlib import contextmanager
from unittest.mock import MagicMock

from flask import Flask
import pymssql
import pytest

from services.dining import api as dining
from services.restaurants import api as restaurants
from service_runtime import peer


@pytest.fixture
def web(monkeypatch):
    cursor = MagicMock()
    state = {'commits': 0, 'rollbacks': 0}
    @contextmanager
    def transaction():
        try:
            yield cursor
            state['commits'] += 1
        except Exception:
            state['rollbacks'] += 1
            raise
    monkeypatch.setattr(dining.store, 'transaction', transaction)
    monkeypatch.setattr(restaurants.catalog, 'transaction', transaction)
    monkeypatch.setattr(dining.store, 'history', lambda *_: [dict(id=31, saved_restaurant_id=2)])
    cursor.fetchone.return_value = {'id': 31}
    boundary = MagicMock(side_effect=[{'id':2}, {'id':2,'status':'visited'}])
    monkeypatch.setattr(dining, 'call', boundary)
    app=Flask('dining');dining.register(app)
    restaurant=Flask('restaurants');restaurants.register(restaurant)
    return app.test_client(), restaurant.test_client(), boundary, state, cursor


def test_visit_success_calls_peer_then_commits(web):
    dining_web, _, call, state, _ = web
    response=dining_web.post('/saved-restaurants/2/visits',json={'visit_date':'2026-01-01'})
    assert response.status_code == 201
    assert response.json['id']==31
    assert [c.args[0] for c in call.call_args_list]==['GET','PUT']
    assert state['commits']==1


@pytest.mark.parametrize('failure,code',[(peer.PeerMissing(),404),(peer.PeerUnavailable(),503)])
def test_peer_failure_rolls_back_without_visit(web,failure,code):
    dining_web,_,call,state,cursor=web
    call.side_effect=failure
    response=dining_web.post('/saved-restaurants/2/visits',json={'visit_date':'2026-01-01'})
    assert response.status_code==code and response.json['retryable'] is False
    assert state['rollbacks']==1 and state['commits']==0
    assert not any('INSERT INTO dbo.visits' in c.args[0] for c in cursor.execute.call_args_list)


def test_mark_timeout_does_not_insert_or_blindly_retry(web):
    dining_web,_,call,state,cursor=web
    call.side_effect=[{'id':2},peer.PeerUnavailable()]
    result=dining_web.post('/saved-restaurants/2/visits',json={'visit_date':'2026-01-01'})
    assert result.status_code==503 and not result.json['retryable']
    assert call.call_count==2 and state['rollbacks']==1
    assert not any('INSERT INTO dbo.visits' in c.args[0] for c in cursor.execute.call_args_list)


def test_wrong_peer_identity_is_rejected(web):
    web[2].side_effect=[{'id':9}]
    assert web[0].post('/saved-restaurants/2/visits',json={'visit_date':'2026-01-01'}).status_code==503


def test_database_failure_after_mark_is_explicit(web,monkeypatch):
    monkeypatch.setattr(dining.store,'record_visit',MagicMock(side_effect=pymssql.OperationalError('private')))
    result=web[0].post('/saved-restaurants/2/visits',json={'visit_date':'2026-01-01'})
    assert result.status_code==503 and result.json['error']=='visit_outcome_uncertain'
    assert 'private' not in result.text and not result.json['retryable']


def test_delete_commits_revocation_then_retries_cleanup(web,monkeypatch):
    _,restaurant,_,state,_=web
    def cleanup(*args,**kwargs):
        assert state['commits']>=1
        raise peer.PeerUnavailable()
    monkeypatch.setattr(restaurants,'call',cleanup)
    result=restaurant.delete('/saved-restaurants/2')
    assert result.status_code==503 and result.json['error']=='cleanup_pending'
    assert result.json['retryable'] is True
    monkeypatch.setattr(restaurants,'call',lambda *a,**k:None)
    assert restaurant.delete('/saved-restaurants/2').status_code==204
    assert restaurant.delete('/saved-restaurants/2').status_code==204


def test_peer_transport_timeout_and_no_retry(monkeypatch):
    monkeypatch.setenv('RESTAURANTS_URL','http://peer')
    monkeypatch.setenv('RESTAURANTS_TIMEOUT_S','0.1')
    opener=MagicMock();opener.open.side_effect=TimeoutError()
    monkeypatch.setattr(peer,'build_opener',lambda *_:opener)
    with pytest.raises(peer.PeerUnavailable):
        peer.call('GET','/test','RESTAURANTS_URL','RESTAURANTS_TIMEOUT_S')
    assert opener.open.call_count==1
    assert opener.open.call_args.kwargs['timeout']==0.1


@pytest.mark.parametrize('status,body,expected',[(200,b'{"id":2}',200),(204,b'',204),(200,b'[]',200),(200,b'broken',200),(201,b'{}',200),(200,b'x'*65537,200)])
def test_peer_response_validation(monkeypatch,status,body,expected):
    monkeypatch.setenv('URL','http://peer')
    response=MagicMock();response.__enter__.return_value=response
    response.status=status;response.read.return_value=body
    opener=MagicMock();opener.open.return_value=response
    monkeypatch.setattr(peer,'build_opener',lambda *_:opener)
    if status==expected and (expected==204 or body.startswith(b'{')):
        peer.call('GET','/','URL','TIMEOUT',expected)
    else:
        with pytest.raises(peer.PeerUnavailable):
            peer.call('GET','/','URL','TIMEOUT',expected)


def test_peer_http_errors_and_redirects(monkeypatch):
    from urllib.error import HTTPError
    monkeypatch.setenv('URL','http://peer')
    opener=MagicMock();monkeypatch.setattr(peer,'build_opener',lambda *_:opener)
    for code,exception in [(404,peer.PeerMissing),(503,peer.PeerUnavailable),(302,peer.PeerUnavailable)]:
        opener.open.side_effect=HTTPError('http://peer',code,'error',{},None)
        with pytest.raises(exception):
            peer.call('GET','/','URL','TIMEOUT')
    assert peer.NoRedirect().redirect_request(None,None,302,'',{},'http://other') is None


@pytest.mark.parametrize('url,timeout',[('', '2'),('file:///tmp/a','2'),('http://peer','nan'),('http://peer','0'),('http://peer','bad')])
def test_bad_peer_configuration_is_unavailable(monkeypatch,url,timeout):
    monkeypatch.setenv('URL',url);monkeypatch.setenv('TIMEOUT',timeout)
    with pytest.raises(peer.PeerUnavailable):
        peer.call('GET','/','URL','TIMEOUT')


def test_bad_status_confirmation_rolls_back(web):
    web[2].side_effect=[{'id':2}, {'id':2,'status':'want_to_go'}]
    result=web[0].post('/saved-restaurants/2/visits',json={'visit_date':'2026-01-01'})
    assert result.status_code==503 and web[3]['rollbacks']==1
