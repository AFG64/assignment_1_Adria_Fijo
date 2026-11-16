"""Exercise startup safety, own health, logs, CORS and bounded connection retries."""
from pathlib import Path
from unittest.mock import MagicMock

import pymssql
import pytest

from service_runtime import application, database


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'mssql://user:pass@sql/db')
    monkeypatch.setenv('VERSION', 'tested-sha')
    monkeypatch.setattr(application, 'migrate', MagicMock())
    monkeypatch.setattr(application, 'probe', MagicMock())
    return application.create_app('test', Path('/migrations'))


def test_health_logs_and_origin(app, caplog):
    with caplog.at_level('INFO'):
        response = app.test_client().get('/health', headers={'Origin': 'http://localhost:8080'})
    assert response.json == {'status': 'ok', 'db': 'ok', 'version': 'tested-sha'}
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:8080'
    assert '"method": "GET"' in caplog.text
    assert '"duration_ms"' in caplog.text
    assert '"version": "tested-sha"' in caplog.text
    assert 'Access-Control-Allow-Origin' not in app.test_client().get('/health', headers={'Origin': 'https://other.invalid'}).headers


def test_failed_health_hides_driver_details(app, monkeypatch):
    monkeypatch.setattr(application, 'probe', MagicMock(side_effect=RuntimeError('private password')))
    response = app.test_client().get('/health')
    assert response.status_code == 503
    assert response.json['db'] == 'unavailable'
    assert b'private' not in response.data


def test_connection_retry_and_timeouts(monkeypatch):
    connection = MagicMock()
    driver = MagicMock(side_effect=[pymssql.OperationalError('paused'), connection])
    sleep = MagicMock()
    monkeypatch.setattr(database.pymssql, 'connect', driver)
    monkeypatch.setattr(database.time, 'sleep', sleep)
    assert database.connect('mssql://u:p%40ss@sql:1444/db', attempts=2) is connection
    assert driver.call_args.kwargs['password'] == 'p@ss'
    assert driver.call_args.kwargs['login_timeout'] == 5
    assert driver.call_args.kwargs['timeout'] == 5
    sleep.assert_called_once_with(1)
    driver.side_effect = pymssql.OperationalError('still paused')
    with pytest.raises(pymssql.OperationalError):
        database.connect('mssql://u:p@sql/db')


@pytest.mark.parametrize('url', ['sqlite:///db', 'mssql://sql/db', 'mssql://u:p@sql/'])
def test_invalid_database_url(url):
    with pytest.raises(ValueError):
        database.connect(url)


def migration_connection(monkeypatch, rows):
    connection = MagicMock()
    connection.cursor.return_value.fetchall.return_value = rows
    monkeypatch.setattr(database, 'connect', MagicMock(return_value=connection))
    return connection


def test_migration_commits_once_then_skips(tmp_path, monkeypatch):
    file = tmp_path / '001_init.sql'
    file.write_text('CREATE TABLE example (id int);')
    connection = migration_connection(monkeypatch, [])
    assert database.migrate('url', tmp_path) == 1
    connection.commit.assert_called_once()
    checksum = database.hashlib.sha256(file.read_text().encode()).hexdigest()
    connection = migration_connection(monkeypatch, [(file.name, checksum)])
    assert database.migrate('url', tmp_path) == 0
    assert all('CREATE TABLE example' not in str(call) for call in connection.cursor.return_value.execute.call_args_list)


def test_edited_migration_rolls_back(tmp_path, monkeypatch):
    (tmp_path / '001_init.sql').write_text('changed')
    connection = migration_connection(monkeypatch, [('001_init.sql', 'old-checksum')])
    with pytest.raises(ValueError, match='changed'):
        database.migrate('url', tmp_path)
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_sql_error_rolls_back(tmp_path, monkeypatch):
    (tmp_path / '001_init.sql').write_text('bad sql')
    connection = migration_connection(monkeypatch, [])
    connection.cursor.return_value.execute.side_effect = RuntimeError('bad sql')
    with pytest.raises(RuntimeError):
        database.migrate('url', tmp_path)
    connection.rollback.assert_called_once()


def test_health_rolls_back_its_write(monkeypatch):
    connection = MagicMock()
    connection.cursor.return_value.fetchone.side_effect = [(17,), ('probe',)]
    monkeypatch.setattr(database, 'connect', MagicMock(return_value=connection))
    database.probe('url')
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
