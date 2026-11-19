"""Release behavior checked offline, including stale health and migration evidence gating."""
from contextlib import nullcontext
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import azure_deploy as release
from scripts.azure_common import SERVICES, SetupError, load_plan

SHA = 'a' * 40
URLS = {s: f'https://picky-{s}.example.azurecontainerapps.io' for s in SERVICES}
ORIGIN = 'https://picky.z1.web.core.windows.net'


def context():
    plan = load_plan()
    return {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF': 'refs/heads/main',
            'GITHUB_REPOSITORY': plan['repository'], 'GITHUB_SHA': SHA, 'PREFIX': plan['prefix'],
            'RESOURCE_GROUP': plan['group'], 'UI_STORAGE': plan['storage'],
            'RESTAURANTS_DB_PASSWORD': 'test-restaurant-secret', 'DINING_DB_PASSWORD': 'test-dining-secret'}


@pytest.mark.parametrize('key,value', [('GITHUB_REF', 'refs/heads/migrate-local-to-azure'),
                                      ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_SHA', 'latest'),
                                      ('UI_STORAGE', 'unrelated'), ('DINING_DB_PASSWORD', ''),
                                      ('GITHUB_REPOSITORY', 'someone/else')])
def test_untrusted_release_context_fails(key, value):
    env = context()
    assert release.release_context(load_plan(), env) == SHA
    env[key] = value
    with pytest.raises(SetupError):
        release.release_context(load_plan(), env)


def test_container_configuration_uses_only_own_secret_and_https_peers():
    plan = load_plan()
    for service in SERVICES:
        document = release.container_document(plan, service, SHA, URLS, ORIGIN, 'secret-with-@', 'environment-id')
        props = document['properties']
        container = props['template']['containers'][0]
        assert container['image'].endswith(':' + SHA)
        settings = {entry['name']: entry for entry in container['env']}
        assert settings['DATABASE_URL'] == {'name': 'DATABASE_URL', 'secretRef': 'database-url'}
        assert 'secret-with' not in json.dumps(container)
        secret_url = props['configuration']['secrets'][0]['value']
        assert f'picky_{service}:' in secret_url and f'/{plan["prefix"]}-{service}-db' in secret_url
        peer = 'dining' if service == 'restaurants' else 'restaurants'
        assert settings[peer.upper() + '_URL']['value'] == URLS[peer]
        assert settings['UI_ORIGIN']['value'] == ORIGIN
        assert props['template']['scale'] == {'minReplicas': 0, 'maxReplicas': 1}
        assert 'corsPolicy' not in props['configuration']['ingress']
        assert container['probes'][0]['httpGet']['path'] == '/health'
        assert all('tcpSocket' in p for p in container['probes'][1:])


@pytest.mark.parametrize('url', ['http://picky.z1.web.core.windows.net', 'https://attacker.example',
                                 'https://user:password@picky.z1.web.core.windows.net',
                                 'https://picky.z1.web.core.windows.net/unexpected',
                                 'https://picky.z1.web.core.windows.net?query=1'])
def test_unexpected_azure_origins_are_rejected(url):
    with pytest.raises(SetupError):
        release.https_origin(url, '.web.core.windows.net')


def checkpoint_tree(tmp_path):
    path = tmp_path / 'infra/azure'
    path.mkdir(parents=True)
    for service in SERVICES:
        folder = tmp_path / f'services/{service}/migrations'
        folder.mkdir(parents=True)
        (folder / '001_init.sql').write_text('test')
    return path / 'migration-checkpoint.json'


def test_002_is_rejected_until_user_checkpoint_is_recorded(tmp_path):
    path = checkpoint_tree(tmp_path)
    path.write_text(json.dumps({'maximum_version': 1, 'before_evidence_confirmed': False}))
    release.migration_checkpoint(tmp_path)
    (tmp_path / 'services/restaurants/migrations/002_new.sql').write_text('test')
    with pytest.raises(SetupError, match='checkpoint'):
        release.migration_checkpoint(tmp_path)
    path.write_text(json.dumps({'maximum_version': 2, 'before_evidence_confirmed': False}))
    with pytest.raises(SetupError, match='confirmation'):
        release.migration_checkpoint(tmp_path)
    path.write_text(json.dumps({'maximum_version': 2, 'before_evidence_confirmed': True}))
    release.migration_checkpoint(tmp_path)


def test_health_retries_cold_start_and_rejects_previous_sha():
    replies = [OSError('starting'), {'status': 'ok', 'db': 'ok', 'version': 'old'},
               {'status': 'ok', 'db': 'ok', 'version': SHA}]
    now = [0]
    requests = []

    def fetch(url, timeout):
        requests.append((url, timeout))
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return nullcontext(SimpleNamespace(status=200, read=lambda n: json.dumps(reply).encode()))

    release.wait_health(URLS['dining'], SHA, fetch=fetch, clock=lambda: now[0],
                        sleep=lambda seconds: now.__setitem__(0, now[0] + seconds))
    assert len(requests) == 3
    assert all(timeout <= 10 for _, timeout in requests)


def test_health_has_a_deadline_for_permanent_or_wrong_version_failure():
    now = [0]

    def fetch(url, timeout):
        return nullcontext(SimpleNamespace(status=503, read=lambda n: b'{}'))

    with pytest.raises(SetupError, match='deadline'):
        release.wait_health(URLS['restaurants'], SHA, budget=12, fetch=fetch,
                            clock=lambda: now[0], sleep=lambda seconds: now.__setitem__(0, now[0] + seconds))
    assert now[0] == 12


def test_no_ui_upload_if_either_service_health_fails(monkeypatch):
    plan = load_plan()
    calls = []
    monkeypatch.setattr(release, 'release_context', lambda p: SHA)
    monkeypatch.setattr(release, 'verify_context', lambda p: None)
    monkeypatch.setattr(release, 'require_public_images', lambda *a: None)
    monkeypatch.setattr(release, 'verify_manifest', lambda p: {'public_url': ORIGIN})
    monkeypatch.setenv('RESTAURANTS_DB_PASSWORD', 'test-only')
    monkeypatch.setenv('DINING_DB_PASSWORD', 'test-only')

    def az(*args, **kwargs):
        calls.append(args)
        if args[:3] == ('storage', 'account', 'show'):
            return {'primaryEndpoints': {'web': ORIGIN}}
        if args[:3] == ('containerapp', 'env', 'show'):
            return {'id': 'environment-id'}
        if args[:2] == ('containerapp', 'show'):
            return {'properties': {'configuration': {'ingress': {'fqdn': 'picky.example.azurecontainerapps.io'}}}}
        return {}

    def fail(*args):
        raise SetupError('own database unavailable')

    monkeypatch.setattr(release, 'az', az)
    monkeypatch.setattr(release, 'wait_health', fail)
    with pytest.raises(SetupError, match='unavailable'):
        release.deploy(plan)
    assert not any('upload-batch' in call for call in calls)


def test_private_ghcr_images_prevent_cloud_updates(monkeypatch):
    from scripts import azure_common
    calls = []

    def private_image(args, **kwargs):
        calls.append(args)
        raise SetupError('Anonymous GHCR pull denied')

    monkeypatch.setattr(azure_common, 'command', private_image)
    with pytest.raises(SetupError, match='Anonymous'):
        release.require_public_images(load_plan(), SHA)
    assert '--config' in calls[0]
    assert not Path(calls[0][2]).exists() # Isolated anonymous config cleaned on failure.
