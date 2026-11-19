"""Offline acceptance checks for cloud targeting and credential handling. No Azure SQL."""
from copy import deepcopy
import json
import subprocess
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit

import pytest

from scripts import azure_common as common
from scripts import azure_setup as setup


def test_manifest_and_guide_derived_plan_agree():
    plan = common.load_plan()
    assert common.verify_manifest(plan)['student'] == 'afijo.ieu2024'
    assert plan['storage'] == 'afijoieu2024ui'
    assert len(setup.public_plan(plan)['resources']['apps']) == 2


def test_inconsistent_identity_is_rejected(tmp_path):
    plan = json.loads((common.ROOT / 'infra/azure/plan.json').read_text())
    plan['prefix'] = 'someone-else'
    path = tmp_path / 'plan.json'
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match='Prefix'):
        common.load_plan(path)


@pytest.mark.parametrize('wrong', ['subscription', 'tenant', 'offer', 'disabled'])
def test_wrong_cloud_context_cannot_proceed(monkeypatch, wrong):
    plan = common.load_plan()
    account = {'id': plan['subscription_id'], 'tenantId': plan['tenant_id']}
    meta = {'state': 'Enabled', 'subscriptionPolicies': {'quotaId': 'AzureForStudents_2018-01-01'}}
    if wrong == 'subscription':
        account['id'] = 'enterprise-subscription'
    elif wrong == 'tenant':
        account['tenantId'] = 'another-tenant'
    elif wrong == 'offer':
        meta['subscriptionPolicies']['quotaId'] = 'EnterpriseAgreement_2014-09-01'
    else:
        meta['state'] = 'Disabled'
    monkeypatch.setattr(common, 'az', lambda *args, **kw: account if args[0] == 'account' else meta)
    with pytest.raises(common.SetupError):
        common.verify_context(plan)


def test_regions_must_satisfy_all_enforced_allowlists(monkeypatch):
    plan = common.load_plan()
    policies = [{'parameters': {'listOfAllowedLocations': {'value': ['francecentral']}}}]
    monkeypatch.setattr(common, 'az', lambda *args, **kw: policies)
    common.verify_regions(plan)
    policies.append({'parameters': {'listOfAllowedLocations': {'value': ['spaincentral']}}})
    with pytest.raises(common.SetupError, match='regions'):
        common.verify_regions(plan)
    policies[-1]['enforcementMode'] = 'DoNotEnforce'
    common.verify_regions(plan)
    policies.clear()
    with pytest.raises(common.SetupError):
        common.verify_regions(plan)


def test_cli_failure_and_timeout_cannot_disclose_secrets(monkeypatch):
    marker = 'credential-that-must-not-appear'
    monkeypatch.setattr(common.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=1, stdout=marker, stderr='ERROR: (SubscriptionNotFound) ' + marker))
    with pytest.raises(common.SetupError) as exc:
        common.command(['az', marker])
    assert marker not in str(exc.value)
    assert 'SubscriptionNotFound' in str(exc.value)
    monkeypatch.setattr(common.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=1, stdout='', stderr='Unrecognized response (Aa1SecretValue)'))
    with pytest.raises(common.SetupError) as exc:
        common.command(['az'])
    assert 'Aa1SecretValue' not in str(exc.value)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(marker, 1, output=marker)

    monkeypatch.setattr(common.subprocess, 'run', timeout)
    with pytest.raises(common.SetupError) as exc:
        common.command(['az', marker])
    assert marker not in str(exc.value)


def test_private_parameters_are_outside_repo_restricted_and_removed():
    with common.private_json({'password': 'test-only'}) as path:
        assert not path.is_relative_to(common.ROOT)
        assert path.stat().st_mode & 0o777 == 0o600
        assert json.loads(path.read_text())['password'] == 'test-only'
    assert not path.exists()


def test_database_credentials_encoded_once_and_scoped_to_service():
    plan = common.load_plan()
    password = 'aB3!@#%_+=.-'
    urls = [urlsplit(common.database_url(plan, s, password)) for s in common.SERVICES]
    assert all(unquote(url.password) == password for url in urls)
    assert urls[0].username != urls[1].username
    assert urls[0].path != urls[1].path
    with pytest.raises(ValueError):
        common.database_url(plan, 'unknown', password)


def test_manifest_mismatch_fails_before_bootstrap(monkeypatch):
    plan = deepcopy(common.load_plan())
    plan['storage'] = 'anotherstorage'
    with pytest.raises(common.SetupError, match='disagree'):
        common.verify_manifest(plan)


@pytest.mark.parametrize('value', ['short', "Untrusted1'SQL_injection", 'lowercase-without-digit', 'A1' * 70])
def test_bootstrap_password_validation(monkeypatch, value):
    monkeypatch.setenv('TEST_PASSWORD', value)
    with pytest.raises(common.SetupError):
        setup.secret('TEST_PASSWORD')


def test_temporary_firewall_removed_if_sql_connection_fails(monkeypatch):
    import service_runtime.database
    calls = []
    monkeypatch.setattr(setup, 'az', lambda *args, **kw: calls.append(args))

    def fail(*args, **kwargs):
        raise RuntimeError('test connection failure')

    monkeypatch.setattr(service_runtime.database, 'connect', fail)
    with pytest.raises(RuntimeError):
        setup.create_users(common.load_plan(), {'restaurants': 'test'}, 'test', '8.8.8.8')
    assert calls[-1][:4] == ('sql', 'server', 'firewall-rule', 'delete')
