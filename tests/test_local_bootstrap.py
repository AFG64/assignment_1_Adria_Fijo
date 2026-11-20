"""Credential persistence, isolation and local-only URL resolution contracts."""
from pathlib import Path
import stat

import pytest

from db.local_bootstrap import PASSWORDS, prepare
from service_runtime.local_start import MARKER, environment


@pytest.fixture
def private_root(tmp_path, monkeypatch):
    for name in PASSWORDS.values():
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr('os.chown', lambda *args: None)
    return tmp_path


def test_passwords_are_distinct_private_and_retained(private_root):
    first = prepare(private_root)
    assert len(set(first.values())) == 3
    assert prepare(private_root) == first
    for name in PASSWORDS:
        assert stat.S_IMODE((private_root / name).stat().st_mode) == 0o700
        assert stat.S_IMODE((private_root / name / 'password').stat().st_mode) == 0o600
    assert (private_root / 'sql/ready').exists()


def test_old_env_is_adopted_but_never_rotates_retained_passwords(private_root, monkeypatch):
    supplied = 'Aa1' + 'a' * 48
    monkeypatch.setenv('RESTAURANTS_PASSWORD', supplied)
    first = prepare(private_root)
    assert first['restaurants'] == supplied
    monkeypatch.setenv('RESTAURANTS_PASSWORD', 'Aa1' + 'b' * 48)
    with pytest.raises(ValueError, match='no password was changed'):
        prepare(private_root)
    assert (private_root / 'restaurants/password').read_text() == supplied


def test_invalid_input_does_not_partially_write_other_credentials(private_root, monkeypatch):
    monkeypatch.setenv('DINING_PASSWORD', 'unsafe-sql-substitution')
    with pytest.raises(ValueError, match='password format'):
        prepare(private_root)
    assert list(private_root.iterdir()) == []


@pytest.mark.parametrize('missing', PASSWORDS)
def test_existing_sql_never_generates_a_replacement_for_a_lost_password(private_root, missing):
    original = prepare(private_root)
    (private_root / missing / 'password').unlink()
    with pytest.raises(ValueError, match='Missing original'):
        prepare(private_root, existing_data=True)
    assert not (private_root / missing / 'password').exists()
    for name in PASSWORDS.keys() - {missing}:
        assert (private_root / name / 'password').read_text() == original[name]


def test_local_start_resolves_only_own_mounted_password(tmp_path):
    password = 'Aa1' + 'c' * 48
    path = tmp_path / 'password'
    path.write_text(password)
    source = {'DATABASE_URL': f'mssql://picky_dining:{MARKER}@sql:1433/picky_dining', 'VERSION': 'local'}
    resolved = environment(source, path)
    assert resolved['DATABASE_URL'] == f'mssql://picky_dining:{password}@sql:1433/picky_dining'
    assert MARKER in source['DATABASE_URL']
    assert resolved['VERSION'] == 'local'


def test_azure_url_does_not_read_local_files():
    source = {'DATABASE_URL': 'mssql://own:provided-secret@example.database.windows.net/own'}
    assert environment(source, Path('/nonexistent/password')) == source


@pytest.mark.parametrize('url', [
    f'mssql://picky_dining:{MARKER}@remote/own',
    f'mssql://sa:{MARKER}@sql/own',
    f'https://picky_dining:{MARKER}@sql/own',
])
def test_mounted_secret_cannot_be_sent_to_another_host_or_admin(url, tmp_path):
    with pytest.raises(ValueError, match='local SQL'):
        environment({'DATABASE_URL': url}, tmp_path / 'absent')


def test_missing_or_invalid_local_secret_fails_closed(tmp_path):
    source = {'DATABASE_URL': f'mssql://picky_dining:{MARKER}@sql/own'}
    path = tmp_path / 'password'
    with pytest.raises(FileNotFoundError):
        environment(source, path)
    path.write_text('invalid')
    with pytest.raises(ValueError, match='Invalid local'):
        environment(source, path)
