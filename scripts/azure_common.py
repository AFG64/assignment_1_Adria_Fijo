"""Shared nonsecret Azure plan and bounded, quiet CLI calls (no shell expansion)."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ('restaurants', 'dining')
PROVIDERS = ('Microsoft.App', 'Microsoft.OperationalInsights', 'Microsoft.Sql',
             'Microsoft.Storage', 'Microsoft.ManagedIdentity')


class SetupError(RuntimeError):
    pass


def command(args, *, input=None, timeout=1800, label='CLI operation'):
    """Never echo command arguments, stdout or stderr on failure: they may be secret."""
    try:
        result = subprocess.run(args, input=input, text=True, capture_output=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise SetupError(f'{label} could not finish; inspect the operation in Azure/GitHub') from None
    if result.returncode:
        # Retain only an Azure symbolic error code, never arbitrary error content.
        match = re.search(r'\(([A-Za-z][A-Za-z0-9]+)\)', result.stderr)
        known_codes = {'SubscriptionNotFound', 'AuthorizationFailed', 'AuthenticationFailed',
                       'ResourceGroupNotFound', 'MissingSubscriptionRegistration', 'BadRequest',
                       'RequestDisallowedByPolicy', 'RequestDisallowedByAzure', 'StorageAccountAlreadyTaken'}
        code = f' ({match[1]})' if match and match[1] in known_codes else ''
        raise SetupError(f'{label} failed{code}; no secret-bearing CLI output printed')
    return result.stdout


def az(*args, **kwargs):
    output = command(['az', *args, '--only-show-errors', '-o', 'json'], **kwargs)
    return json.loads(output) if output.strip() else None


@contextmanager
def private_json(value):
    """Secure temporary parameter/payload file outside the repository; always remove."""
    with tempfile.TemporaryDirectory(prefix='picky-azure-') as directory:
        path = Path(directory) / 'parameters.json'
        with open(path, 'x', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
            json.dump(value, stream)
        yield path


def load_plan(path=ROOT / 'infra/azure/plan.json'):
    plan = json.loads(Path(path).read_text())
    for key in ('subscription_id', 'tenant_id'):
        UUID(plan[key])
    if plan['prefix'] != plan['student'].replace('.', '-') or not re.fullmatch(r'[a-z][a-z0-9-]{2,18}', plan['prefix']):
        raise ValueError('Prefix must derive from the actual IE username and fit all resource names')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', plan['repository']):
        raise ValueError('Expected owner/repository')
    for key in ('location', 'sql_location'):
        if not re.fullmatch(r'[a-z]+', plan[key]):
            raise ValueError('Use Azure region identifiers')
    if any(type(plan[key]) is not int or plan[key] < 1 for key in ('repository_id', 'owner_id')):
        raise ValueError('Real GitHub numeric IDs required')
    if len(plan['readers']) != 2 or any(not re.fullmatch(r'[a-z]+@faculty\.ie\.edu', value) for value in plan['readers']):
        raise ValueError('Two explicit professor Reader identities required')
    plan['group'] = 'rg-' + plan['prefix']
    plan['storage'] = plan['prefix'].replace('-', '') + 'ui'
    return plan


def database_url(plan, service, password, *, admin=False):
    if service not in SERVICES or not password:
        raise ValueError('Explicit service and nonempty password required')
    user = 'pickyadmin' if admin else 'picky_' + service
    return (f'mssql://{user}:{quote(password, safe="")}@{plan["prefix"]}-sql.database.windows.net:1433/'
            f'{plan["prefix"]}-{service}-db')


def verify_context(plan):
    """Every cloud operation checks exact subscription/tenant and Students offer."""
    account = az('account', 'show', label='Azure account check')
    if account['id'] != plan['subscription_id'] or account['tenantId'] != plan['tenant_id']:
        raise SetupError('Select the exact personal subscription/tenant in infra/azure/plan.json first')
    metadata = az('rest', '--method', 'get', '--url',
                  f'https://management.azure.com/subscriptions/{plan["subscription_id"]}?api-version=2022-12-01',
                  label='Students offer verification')
    if metadata['state'] != 'Enabled' or not metadata['subscriptionPolicies']['quotaId'].startswith('AzureForStudents_'):
        raise SetupError('Refusing a disabled or non-Students subscription')


def verify_regions(plan):
    policies = az('policy', 'assignment', 'list', '--subscription', plan['subscription_id'], label='Region policy check')
    allowed_sets = [set(p['parameters']['listOfAllowedLocations']['value']) for p in policies
                    if 'listOfAllowedLocations' in p.get('parameters', {}) and p.get('enforcementMode') != 'DoNotEnforce']
    if not allowed_sets or any(plan[key] not in allowed for allowed in allowed_sets for key in ('location', 'sql_location')):
        raise SetupError('Both proposed regions must be permitted by the live subscription policy')


def verify_manifest(plan):
    import yaml
    system = yaml.safe_load((ROOT / 'system.yaml').read_text())
    expected = {'resource_group': plan['group'], 'container_apps_environment': plan['prefix'] + '-env',
                'sql_server': plan['prefix'] + '-sql', 'registry': 'ghcr.io/' + plan['repository'].split('/')[0].lower()}
    if (system['student'] != plan['student'] or system['prefix'] != plan['prefix']
            or system['ui']['storage_account'] != plan['storage'] or system['azure'] != expected
            or set(system['services']) != set(SERVICES)):
        raise SetupError('system.yaml and the Azure plan disagree')
    for service in SERVICES:
        if system['services'][service]['azure'] != {
                'container_app': plan['prefix'] + '-' + service, 'sql_database': plan['prefix'] + '-' + service + '-db'}:
            raise SetupError('Service resource names disagree with the Azure plan')
    return system
