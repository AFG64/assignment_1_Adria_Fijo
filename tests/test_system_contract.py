"""Positive and negative acceptance cases for the milestone 1 system contract."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

from scripts.validate_contracts import validate_system

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'system.schema.json').read_text())
SYSTEM = yaml.safe_load((ROOT / 'system.yaml').read_text())
CONTRACTS = {
    name: yaml.safe_load((ROOT / service['openapi']).read_text())
    for name, service in SYSTEM['services'].items()
}


def test_target_system_passes():
    validate_system(SYSTEM, SCHEMA, CONTRACTS)


@pytest.mark.parametrize('case', [
    'missing_service_field', 'zero_port', 'large_port', 'string_port',
    'secret_default', 'secret_false_without_default', 'no_default',
    'zero_timeout', 'unknown_field', 'third_service', 'bad_url',
    'unknown_ui_peer', 'unknown_peer', 'missing_url_env', 'missing_endpoint',
    'http_public_url', 'bad_storage_name', 'missing_port_env', 'large_timeout', 'null_default', 'old_swa_field',
])
def test_invalid_system_fails(case):
    document = deepcopy(SYSTEM)
    restaurant = document['services']['restaurants']
    if case == 'missing_service_field':
        del restaurant['migrations']
    elif case in ('zero_port', 'large_port', 'string_port'):
        restaurant['port_default'] = {'zero_port': 0, 'large_port': 65536, 'string_port': '8000'}[case]
    elif case == 'secret_default':
        restaurant['env']['DATABASE_URL']['default'] = 'must-not-store-secrets'
    elif case == 'secret_false_without_default':
        restaurant['env']['DATABASE_URL']['secret'] = False
    elif case == 'no_default':
        del restaurant['env']['PORT']['default']
    elif case == 'zero_timeout':
        restaurant['calls'][0]['timeout_s'] = 0
    elif case == 'unknown_field':
        restaurant['unexpected'] = True
    elif case == 'third_service':
        document['services']['extra'] = deepcopy(restaurant)
    elif case == 'bad_url':
        document['public_url'] = 'not a URL'
    elif case == 'unknown_ui_peer':
        document['ui']['calls'].append('unknown')
    elif case == 'unknown_peer':
        restaurant['calls'][0]['service'] = 'unknown'
    elif case == 'missing_url_env':
        restaurant['calls'][0]['url_env'] = 'UNDECLARED_URL'
    elif case == 'http_public_url':
        document['public_url'] = 'http://localhost:8080'
    elif case == 'bad_storage_name':
        document['ui']['storage_account'] = 'Invalid-Storage'
    elif case == 'missing_port_env':
        del restaurant['env']['PORT']
    elif case == 'large_timeout':
        restaurant['calls'][0]['timeout_s'] = 31
    elif case == 'null_default':
        restaurant['env']['PORT']['default'] = None
    elif case == 'old_swa_field':
        document['ui']['static_web_app'] = 'old-ui'
    elif case == 'missing_endpoint':
        restaurant['calls'][0]['endpoints'] = ['DELETE /not-documented']
    with pytest.raises((ValidationError, ValueError)):
        validate_system(document, SCHEMA, CONTRACTS)


def test_official_schema_is_unchanged():
    import hashlib
    assert hashlib.sha256((ROOT / 'system.schema.json').read_bytes()).hexdigest() == 'a6d6b1f8cca72724cdcbf24a0ceaaa7d7ad94210d17456791ab5854bdf94fa05'


def test_official_optional_service_fields_are_optional():
    document = deepcopy(SYSTEM)
    for service in document['services'].values():
        for field in ('description', 'health', 'calls'):
            service.pop(field)
    validate_system(document, SCHEMA, CONTRACTS)
