"""Initial Azure setup only. Default prints a plan; apply requires explicit authorization.

Passwords are prompted securely or read from environment; never written in the repo.
Application images are deployed only by main's pipeline, not by this bootstrap.
"""
import argparse
from contextlib import closing
import getpass
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_common import (ROOT, PROVIDERS, SERVICES, SetupError, az, command,
                                  database_url, load_plan, private_json, verify_context,
                                  verify_manifest, verify_regions)


def public_plan(plan):
    return {**plan, 'resources': {
        'storage': plan['storage'], 'environment': plan['prefix'] + '-env',
        'logs': plan['prefix'] + '-logs', 'identity': plan['prefix'] + '-github',
        'sql_server': plan['prefix'] + '-sql',
        'apps': [plan['prefix'] + '-' + s for s in SERVICES],
        'databases': [plan['prefix'] + '-' + s + '-db' for s in SERVICES],
    }, 'database_sku': 'GP_S_Gen5_1; min 0.5; free limit AutoPause; local backups',
        'container_scale': 'Consumption; 0–1 replicas; 0.25 CPU / 0.5 GiB each',
        'grants': 'identity: RG Contributor + storage Blob Data Contributor; setup user: storage Blob Data Contributor; professors: RG Reader'}


def github_ids(plan):
    repo = json.loads(command(['gh', 'api', 'repos/' + plan['repository']], label='GitHub repository identity check'))
    if repo['id'] != plan['repository_id'] or repo['owner']['id'] != plan['owner_id']:
        raise SetupError('GitHub owner/repository numeric IDs changed; review the federation plan')
    return [az('ad', 'user', 'show', '--id', email, label='Professor directory lookup')['id'] for email in plan['readers']]


def check_names(plan):
    names = az('storage', 'account', 'check-name', '--name', plan['storage'], label='Storage name availability')
    if not names['nameAvailable']:
        raise SetupError('Proposed storage name is unavailable; review the plan before creating resources')
    sql = az('rest', '--method', 'post', '--url',
             f'https://management.azure.com/subscriptions/{plan["subscription_id"]}/providers/Microsoft.Sql/checkNameAvailability?api-version=2023-08-01',
             '--body', json.dumps({'name': plan['prefix'] + '-sql', 'type': 'Microsoft.Sql/servers'}),
             label='SQL server name availability')
    if not sql['available']:
        raise SetupError('Proposed SQL name is unavailable; review the plan')


def preflight(plan):
    verify_manifest(plan)
    verify_context(plan)
    verify_regions(plan)
    readers = github_ids(plan)
    check_names(plan)
    print('Subscription, regions, manifest, repository IDs, Reader identities and names verified.', flush=True)
    print('Free-offer acceptance remains an Azure deployment-time check; never substitute a paid SKU.')
    return readers


def secret(name):
    value = os.environ.get(name) or getpass.getpass(name + ': ')
    # A bounded strong alphabet also prevents interpolation in CREATE USER SQL.
    if (not 16 <= len(value) <= 128 or not re.fullmatch(r'[A-Za-z0-9!@#%_+=.-]+', value)
            or not all(re.search(pattern, value) for pattern in (r'[a-z]', r'[A-Z]', r'[0-9]'))):
        raise SetupError(f'{name} must be 16–128 characters with upper/lower/digits; allowed punctuation !@#%_+=.-')
    return value


def create_users(plan, passwords, admin_password, client_ip):
    from service_runtime.database import connect
    firewall = 'temporary-bootstrap'
    args = ['--resource-group', plan['group'], '--server', plan['prefix'] + '-sql', '--name', firewall]
    try:
        az('sql', 'server', 'firewall-rule', 'create', *args, '--start-ip-address', client_ip,
           '--end-ip-address', client_ip, label='Temporary SQL firewall creation')
        for service in SERVICES:
            user = 'picky_' + service
            with closing(connect(database_url(plan, service, admin_password, admin=True), attempts=12)) as connection:
                cursor = connection.cursor()
                cursor.execute(f"IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name='{user}') "
                               f"CREATE USER [{user}] WITH PASSWORD='{passwords[service]}';")
                for role in ('db_ddladmin', 'db_datareader', 'db_datawriter'):
                    cursor.execute(f"IF IS_ROLEMEMBER('{role}','{user}') <> 1 ALTER ROLE [{role}] ADD MEMBER [{user}]")
                connection.commit()
            # Verify the supplied password matches on a resumed partial setup; never silently rotate.
            with closing(connect(database_url(plan, service, passwords[service]), attempts=12)) as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT DB_NAME()')
                if cursor.fetchone()[0] != plan['prefix'] + '-' + service + '-db':
                    raise SetupError('Contained user connected to an unexpected database')
            print(f'{service}: own contained user verified; roles granted.', flush=True)
    finally:
        az('sql', 'server', 'firewall-rule', 'delete', *args, label='Temporary SQL firewall removal')


def apply(plan, client_ip):
    # All local validation/password prompts happen before the first cloud write.
    verify_manifest(plan)
    verify_context(plan)
    verify_regions(plan)
    readers = github_ids(plan)
    setup_id = az('ad', 'signed-in-user', 'show', label='Bootstrap user identity lookup')['id']
    passwords = {s: secret(s.upper() + '_DB_PASSWORD') for s in SERVICES}
    admin_password = secret('AZURE_SQL_ADMIN_PASSWORD')
    if len(set([admin_password, *passwords.values()])) != 3:
        raise SetupError('Use distinct admin and service passwords')
    groups = az('group', 'list', label='Existing resource group check')
    existing = next((g for g in groups if g['name'] == plan['group']), None)
    if existing and existing.get('tags', {}).get('project') != 'picky-assignment-2':
        raise SetupError('Refusing to modify an existing group without the Picky ownership tag')
    if not existing:
        # Fresh names must be free; on a partial resume Bicep addresses only named owned resources.
        for provider in PROVIDERS:
            print(f'Registering {provider}...', flush=True)
            az('provider', 'register', '--namespace', provider, '--wait', label='Provider registration')
        check_names(plan)
        az('group', 'create', '--name', plan['group'], '--location', plan['location'],
           '--tags', 'project=picky-assignment-2', 'student=' + plan['prefix'], label='Personal group creation')
    params = {'prefix': plan['prefix'], 'location': plan['location'], 'sqlLocation': plan['sql_location'],
              'storageName': plan['storage'], 'repository': plan['repository'], 'repositoryId': plan['repository_id'],
              'ownerId': plan['owner_id'], 'readerObjectIds': readers, 'setupObjectId': setup_id, 'sqlAdminPassword': admin_password}
    with private_json({'parameters': {k: {'value': v} for k, v in params.items()}}) as path:
        deployment = az('deployment', 'group', 'create', '--resource-group', plan['group'],
                        '--name', 'picky-initial-setup', '--template-file', str(ROOT / 'infra/azure/main.bicep'),
                        '--parameters', '@' + str(path), label='Bicep resource setup')
    outputs = {k: v['value'] for k, v in deployment['properties']['outputs'].items()}
    # Allow bounded propagation time for the new storage data-plane role.
    for attempt in range(12):
        try:
            az('storage', 'blob', 'service-properties', 'update', '--account-name', plan['storage'],
               '--auth-mode', 'login', '--static-website', '--index-document', 'index.html',
               label='Static website enablement')
            break
        except SetupError:
            if attempt == 11:
                raise
            time.sleep(10)
    for service in SERVICES:
        name = plan['prefix'] + '-' + service
        apps = az('containerapp', 'list', '--resource-group', plan['group'], label='Existing apps check')
        if any(app['name'] == name for app in apps):
            continue # Never replace an already-deployed application with the placeholder.
        az('containerapp', 'create', '--name', name, '--resource-group', plan['group'],
           '--environment', outputs['environmentId'], '--image', 'mcr.microsoft.com/k8se/quickstart:latest',
           '--ingress', 'external', '--target-port', '80', '--min-replicas', '0', '--max-replicas', '1',
           '--cpu', '0.25', '--memory', '0.5Gi', '--revisions-mode', 'single',
           '--workload-profile-name', 'Consumption', label='Placeholder Container App creation')
    create_users(plan, passwords, admin_password, client_ip)
    values = {'AZURE_CLIENT_ID': outputs['clientId'], 'AZURE_TENANT_ID': plan['tenant_id'],
              'AZURE_SUBSCRIPTION_ID': plan['subscription_id'],
              **{s.upper() + '_DB_PASSWORD': passwords[s] for s in SERVICES}}
    for name, value in values.items():
        command(['gh', 'secret', 'set', name, '--repo', plan['repository']], input=value, label='GitHub secret configuration')
    for name, value in {'PREFIX': plan['prefix'], 'RESOURCE_GROUP': plan['group'], 'UI_STORAGE': plan['storage']}.items():
        command(['gh', 'variable', 'set', name, '--repo', plan['repository'], '--body', value], label='GitHub variable configuration')
    storage = az('storage', 'account', 'show', '--resource-group', plan['group'], '--name', plan['storage'],
                 label='Enabled website endpoint discovery')
    print('Initial setup finished. Applications still require the approved main deployment pipeline.', flush=True)
    print('Public website origin: ' + storage['primaryEndpoints']['web'].rstrip('/'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'preflight', 'apply'), nargs='?', default='plan')
    parser.add_argument('--client-ip', type=ipaddress.IPv4Address, help='Own public IPv4, temporary SQL bootstrap only')
    args = parser.parse_args()
    plan = load_plan()
    try:
        verify_manifest(plan)
        if args.action == 'plan':
            print(json.dumps(public_plan(plan), indent=2))
        elif args.action == 'preflight':
            preflight(plan)
        elif not args.client_ip or not args.client_ip.is_global:
            parser.error('apply requires your explicit public --client-ip')
        else:
            apply(plan, str(args.client_ip))
    except (SetupError, ValueError) as exc:
        raise SystemExit(str(exc)) from None
    except Exception:
        raise SystemExit('Setup failed; no exception details printed because they may contain credentials. '
                         'Check resource state; retain the same passwords to resume, and verify temporary firewall removal.') from None


if __name__ == '__main__':
    main()
