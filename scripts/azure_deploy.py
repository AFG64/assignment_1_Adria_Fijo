"""Main-only release: secret-backed Container Apps, bounded own health, static UI.

validate is offline and safe in CI. deploy is restricted to the trusted main
push context and never creates databases, applies SQL directly or copies data.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_common import (ROOT, SERVICES, SetupError, az, database_url, load_plan,
                                  private_json, verify_context, verify_manifest)


def migration_checkpoint(root=ROOT):
    checkpoint = json.loads((root / 'infra/azure/migration-checkpoint.json').read_text())
    version = checkpoint['maximum_version']
    if type(version) is not int or version < 1 or (version > 1 and checkpoint['before_evidence_confirmed'] is not True):
        raise SetupError('Migration 002+ requires explicit user confirmation of populated-baseline before evidence')
    for service in SERVICES:
        migrations = list((root / f'services/{service}/migrations').glob('*.sql'))
        if not migrations or any(not re.fullmatch(r'\d{3}_[a-z0-9_]+\.sql', path.name) for path in migrations):
            raise SetupError('Expected numbered forward SQL migrations for each service')
        if any(int(path.name[:3]) > version for path in migrations):
            raise SetupError('Migration exceeds the approved evidence checkpoint')


def release_context(plan, env=os.environ):
    sha = env.get('GITHUB_SHA', '')
    expected = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF': 'refs/heads/main',
                'GITHUB_REPOSITORY': plan['repository'], 'PREFIX': plan['prefix'],
                'RESOURCE_GROUP': plan['group'], 'UI_STORAGE': plan['storage']}
    if not re.fullmatch(r'[0-9a-f]{40}', sha) or any(env.get(k) != v for k, v in expected.items()):
        raise SetupError('Deployment requires this repository’s main push and the exact reviewed resource variables')
    for service in SERVICES:
        if not env.get(service.upper() + '_DB_PASSWORD'):
            raise SetupError('Both service password secrets must be configured before deployment')
    return sha


def https_origin(value, suffix):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith(suffix)
            or parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment
            or parsed.path not in ('', '/')):
        raise SetupError('Azure returned an unexpected public endpoint')
    return value.rstrip('/')


def image_tag(plan, service, sha):
    return f'ghcr.io/{plan["repository"].split("/")[0].lower()}/picky-{service}:{sha}'


def container_document(plan, service, sha, urls, ui_origin, password, environment_id):
    peer = 'dining' if service == 'restaurants' else 'restaurants'
    settings = {'PORT': '8000', 'VERSION': sha, 'UI_ORIGIN': ui_origin,
                peer.upper() + '_URL': urls[peer], peer.upper() + '_TIMEOUT_S': '2'}
    if service == 'restaurants':
        settings.update(GEOCODER_BASE_URL='https://nominatim.openstreetmap.org', GEOCODER_TIMEOUT_S='5')
    # Only the startup HTTP probe and bounded release check touch SQL. Ongoing
    # TCP probes do not keep an otherwise idle serverless database awake.
    probes = [{'type': kind, 'tcpSocket': {'port': 8000}, 'periodSeconds': period,
               'timeoutSeconds': 2, 'failureThreshold': failures}
              for kind, period, failures in [('Startup', 5, 60), ('Readiness', 10, 3), ('Liveness', 30, 3)]]
    probes[0].pop('tcpSocket')
    probes[0]['httpGet'] = {'path': '/health', 'port': 8000, 'scheme': 'HTTP'}
    return {'name': plan['prefix'] + '-' + service, 'type': 'Microsoft.App/containerApps',
            'location': plan['location'], 'properties': {
                'environmentId': environment_id, 'workloadProfileName': 'Consumption',
                'configuration': {
                    'activeRevisionsMode': 'Single',
                    'secrets': [{'name': 'database-url', 'value': database_url(plan, service, password)}],
                    'ingress': {'external': True, 'allowInsecure': False, 'targetPort': 8000, 'transport': 'auto',
                                'traffic': [{'latestRevision': True, 'weight': 100}]}},
                'template': {'containers': [{
                    'name': service, 'image': image_tag(plan, service, sha),
                    'resources': {'cpu': 0.25, 'memory': '0.5Gi'}, 'probes': probes,
                    'env': [{'name': 'DATABASE_URL', 'secretRef': 'database-url'},
                            *[{'name': k, 'value': v} for k, v in settings.items()]]}],
                    'scale': {'minReplicas': 0, 'maxReplicas': 1}}}}


def wait_health(url, sha, *, budget=360, fetch=urlopen, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + budget
    while clock() < deadline:
        try:
            with fetch(url + '/health', timeout=min(10, max(0.1, deadline - clock()))) as response:
                body = json.loads(response.read(65537))
                if (response.status == 200 and isinstance(body, dict) and body.get('status') == 'ok'
                        and body.get('db') == 'ok' and body.get('version') == sha):
                    return
        except (OSError, URLError, ValueError, TimeoutError):
            pass
        sleep(min(5, max(0, deadline - clock())))
    raise SetupError('Service failed own SQL read/write and exact-SHA health deadline; inspect startup logs')


def require_public_images(plan, sha):
    """Use a clean Docker config so runner's authenticated login cannot hide private packages."""
    from scripts.azure_common import command
    with tempfile.TemporaryDirectory(prefix='picky-anonymous-pull-') as directory:
        for service in SERVICES:
            command(['docker', '--config', directory, 'manifest', 'inspect', image_tag(plan, service, sha)],
                    timeout=90, label='Anonymous GHCR pull check; make both packages public if private')


def deploy(plan):
    migration_checkpoint()
    verify_manifest(plan)
    sha = release_context(plan)
    verify_context(plan)
    require_public_images(plan, sha)
    group = plan['group']
    storage = az('storage', 'account', 'show', '--resource-group', group, '--name', plan['storage'], label='Website endpoint discovery')
    origin = https_origin(storage['primaryEndpoints']['web'], '.web.core.windows.net')
    system = verify_manifest(plan)
    if system['public_url'] != origin:
        raise SetupError('Commit the discovered website public_url to system.yaml before the first application release')
    environment = az('containerapp', 'env', 'show', '--resource-group', group, '--name', plan['prefix'] + '-env',
                     label='Container environment discovery')
    urls = {}
    for service in SERVICES:
        app = az('containerapp', 'show', '--resource-group', group, '--name', plan['prefix'] + '-' + service,
                 label='Service endpoint discovery')
        urls[service] = https_origin('https://' + app['properties']['configuration']['ingress']['fqdn'], '.azurecontainerapps.io')
    for service in SERVICES:
        document = container_document(plan, service, sha, urls, origin,
                                      os.environ[service.upper() + '_DB_PASSWORD'], environment['id'])
        with private_json(document) as path:
            az('containerapp', 'update', '--resource-group', group, '--name', plan['prefix'] + '-' + service,
               '--yaml', str(path), label=f'{service} SHA deployment')
        print(f'{service}: image update accepted for {sha}', flush=True)
    # Each domain is checked independently; no health dependency on the peer.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(wait_health, urls[s], sha) for s in SERVICES]
        for future in futures:
            future.result()
    with tempfile.TemporaryDirectory(prefix='picky-public-ui-') as directory:
        target = Path(directory) / 'ui'
        shutil.copytree(ROOT / 'ui', target)
        config = {'restaurants': urls['restaurants'], 'dining': urls['dining']}
        (target / 'config.js').write_text('window.PICKY_CONFIG = ' + json.dumps(config) + ';\n')
        (target / 'release.json').write_text(json.dumps({'version': sha}) + '\n')
        az('storage', 'blob', 'upload-batch', '--account-name', plan['storage'], '--auth-mode', 'login',
           '--destination', '$web', '--source', str(target), '--overwrite', 'true',
           '--content-cache-control', 'no-store', label='Static website upload')
    # Never report success from API health alone: check browser config and published SHA.
    for path, expected in [('release.json', sha), ('config.js', urls['restaurants']), ('config.js', urls['dining'])]:
        request = Request(origin + '/' + path + '?sha=' + sha, headers={'Cache-Control': 'no-cache'})
        with urlopen(request, timeout=20) as response:
            if response.status != 200 or expected not in response.read(131072).decode():
                raise SetupError('Published UI configuration/version check failed')
    print('Release healthy at ' + origin, flush=True)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as stream:
            stream.write(f'Released `{sha}`: [Picky]({origin}). Both own SQL health checks passed.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'deploy'))
    args = parser.parse_args()
    try:
        plan = load_plan()
        verify_manifest(plan)
        migration_checkpoint()
        if args.action == 'validate':
            print('Azure plan/manifest agree; migration evidence checkpoint passes (offline).')
        else:
            deploy(plan)
    except (SetupError, ValueError) as exc:
        raise SystemExit(str(exc)) from None
    except Exception:
        raise SystemExit('Release failed; secret-bearing exception details suppressed. Inspect Azure/GitHub run state.') from None


if __name__ == '__main__':
    main()
