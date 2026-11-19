"""Populate/check synthetic 001 baseline on the reviewed Azure target, on demand only.

Default is an offline description. This is not run by CI/CD and never imports
private local data. The user captures before evidence and confirms it separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_common import ROOT, SERVICES, SetupError, az, load_plan, verify_context, verify_manifest
from scripts.azure_deploy import https_origin, wait_health

MARKER = 'Picky Azure 001 synthetic baseline'
ITEM = 'Baseline soup'


def synthetic_bill():
    """Small valid one-page PDF fixture; no real receipt or personal information."""
    content = b'BT /F1 16 Tf 50 750 Td (Picky synthetic baseline - not a real receipt) Tj 0 -30 Td (Baseline soup: 2 x EUR 3.50 = EUR 7.00) Tj ET'
    objects = [b'<</Type/Catalog /Pages 2 0 R>>', b'<</Type/Pages /Kids[3 0 R] /Count 1>>',
               b'<</Type/Page /Parent 2 0 R /MediaBox[0 0 595 842] /Resources<</Font<</F1 5 0 R>>>> /Contents 4 0 R>>',
               b'<</Length ' + str(len(content)).encode() + b'>>\nstream\n' + content + b'\nendstream',
               b'<</Type/Font /Subtype/Type1 /BaseFont/Helvetica>>']
    result, offsets = b'%PDF-1.4\n', [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += str(index).encode() + b' 0 obj\n' + obj + b'\nendobj\n'
    start = len(result)
    result += b'xref\n0 6\n0000000000 65535 f \n'
    result += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return result + f'trailer\n<</Size 6 /Root 1 0 R>>\nstartxref\n{start}\n%%EOF\n'.encode()


BILL = synthetic_bill()


class Api:
    def __init__(self, urls, origin):
        self.urls, self.origin = urls, origin

    def call(self, service, method, path, body=None, *, expected=200, binary=False, content_type='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        request = Request(self.urls[service] + path, data=data, method=method,
                          headers={'Origin': self.origin, 'Content-Type': content_type})
        try:
            response = urlopen(request, timeout=30)
        except (HTTPError, URLError, OSError):
            raise SetupError(f'{service} {method} could not be confirmed; inspect current data before rerunning. No automatic retry.') from None
        with response:
            if response.status != expected or response.headers.get('Access-Control-Allow-Origin') != self.origin:
                raise SetupError('Unexpected API status or website CORS origin; no automatic retry')
            raw = response.read(5 * 1024 * 1024 + 1)
            if len(raw) > 5 * 1024 * 1024:
                raise SetupError('API response exceeded the check limit')
            return raw if binary else json.loads(raw) if raw else None


def only_match(rows, predicate, label):
    matches = [row for row in rows if predicate(row)]
    if len(matches) > 1:
        raise SetupError(f'Multiple synthetic {label} records found; inspect before changing anything')
    return matches[0] if matches else None


def exercise(api, *, populate=False, marker=MARKER):
    """Read current state before each optional write; never retry a POST blindly."""
    row = only_match(api.call('restaurants', 'GET', '/restaurants'), lambda r: r['title'] == marker, 'restaurant')
    if row is None and populate:
        row = api.call('restaurants', 'POST', '/restaurants',
                       {'title': marker, 'category_name': 'Synthetic baseline', 'city': 'Madrid',
                        'notes': 'Synthetic data retained for migration verification.'}, expected=201)
    if row is None or not row.get('saved'):
        raise SetupError('No saved synthetic baseline exists; populate explicitly before collecting before evidence')
    if row.get('city') != 'Madrid' or row.get('category_name') != 'Synthetic baseline':
        raise SetupError('Synthetic restaurant values changed; inspect before continuing')
    sid = row['saved']['id']
    history = f'/saved-restaurants/{sid}/visits'
    visit = only_match(api.call('dining', 'GET', history), lambda v: v['notes'] == marker, 'visit')
    if visit is None and populate:
        visit = api.call('dining', 'POST', history,
                         {'visit_date': '2026-11-01', 'rating': 4, 'notes': marker}, expected=201)
    if visit is None:
        raise SetupError('Synthetic visit missing from baseline')
    if visit['visit_date'] != '2026-11-01' or visit['rating'] != 4:
        raise SetupError('Synthetic visit values changed; inspect before continuing')
    path = history + '/' + str(visit['id'])
    item = only_match(visit['items'], lambda i: i['item_name'] == ITEM, 'item')
    if item is None and populate:
        item = api.call('dining', 'POST', path + '/items',
                        {'item_name': ITEM, 'quantity': 2, 'unit_price': 3.5}, expected=201)
    if item is None or item['quantity'] != 2 or item['unit_price'] != 3.5:
        raise SetupError('Synthetic item values missing/changed')
    bills = [bill for bill in visit['bills']
             if api.call('dining', 'GET', path + '/bills/' + str(bill['id']), binary=True) == BILL]
    if len(bills) > 1:
        raise SetupError('Duplicate synthetic bills; inspect uncertain earlier writes')
    bill = bills[0] if bills else None
    if bill is None and populate:
        boundary = 'picky-synthetic-baseline'
        data = (f'--{boundary}\r\nContent-Disposition: form-data; name="bill_file"; filename="synthetic.pdf"\r\n'
                'Content-Type: application/pdf\r\n\r\n').encode() + BILL + f'\r\n--{boundary}--\r\n'.encode()
        bill = api.call('dining', 'POST', path + '/bills', data, expected=201,
                        content_type='multipart/form-data; boundary=' + boundary)
    if bill is None or api.call('dining', 'GET', path + '/bills/' + str(bill['id']), binary=True) != BILL:
        raise SetupError('Synthetic bill bytes missing/changed')
    saved = api.call('restaurants', 'GET', f'/saved-restaurants/{sid}')
    if saved['status'] != 'visited':
        raise SetupError('Cross-service visited status was not retained')
    return {'restaurant_id': row['id'], 'saved_id': sid, 'visit_id': visit['id'],
            'item_id': item['id'], 'bill_id': bill['id'], 'bill_sha256': hashlib.sha256(BILL).hexdigest(),
            'status': saved['status'], 'visit_date': visit['visit_date'], 'rating': visit['rating']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'populate', 'inspect'), nargs='?', default='plan')
    args = parser.parse_args()
    if args.action == 'plan':
        print('Synthetic baseline: one saved restaurant, one visit, one item and one binary PDF bill.\n'
              'populate explicitly writes; inspect only reads. Neither captures your assignment evidence.\n'
              'Stop after population/verification until you confirm before evidence is captured.')
        return
    try:
        if args.action == 'populate':
            checkpoint = json.loads((ROOT / 'infra/azure/migration-checkpoint.json').read_text())
            if checkpoint != {'maximum_version': 1, 'before_evidence_confirmed': False}:
                raise SetupError('Baseline population is only allowed at the unconfirmed 001 checkpoint')
        plan = load_plan()
        system = verify_manifest(plan)
        verify_context(plan)
        origin = https_origin(system['public_url'], '.web.core.windows.net')
        with urlopen(origin + '/release.json', timeout=20) as response:
            sha = json.load(response)['version']
        urls = {}
        for service in SERVICES:
            app = az('containerapp', 'show', '--resource-group', plan['group'], '--name', plan['prefix'] + '-' + service,
                     label='Baseline service discovery')
            urls[service] = https_origin('https://' + app['properties']['configuration']['ingress']['fqdn'], '.azurecontainerapps.io')
            wait_health(urls[service], sha)
        print(json.dumps(exercise(Api(urls, origin), populate=args.action == 'populate'), indent=2))
        print('STOP: user must capture/confirm before evidence; this command never authorizes migration 002.')
    except SetupError as exc:
        raise SystemExit(str(exc)) from None
    except Exception:
        raise SystemExit('Baseline check failed; inspect the deployed state before rerunning; no write was retried automatically.') from None


if __name__ == '__main__':
    main()
