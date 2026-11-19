"""Validate target contracts against the unchanged professor-provided system schema."""
import argparse
from pathlib import Path

import yaml
from jsonschema import FormatChecker, validators
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]


def validate_system(document, schema, contracts):
    """Check structure and links that JSON Schema cannot express across services."""
    validator = validators.validator_for(schema)
    validator.check_schema(schema)
    validator(schema, format_checker=FormatChecker()).validate(document)
    services = document['services']
    for target in document['ui']['calls']:
        if target not in services:
            raise ValueError(f'Unknown UI service: {target}')
    for name, service in services.items():
        for call in service.get('calls', []):
            target = call['service']
            if target not in services or target == name:
                raise ValueError(f'Invalid peer: {name} -> {target}')
            setting = service['env'].get(call['url_env'], {})
            if not isinstance(setting.get('default'), str) or setting.get('secret'):
                raise ValueError(f'Missing nonsecret peer URL configuration: {name}')
            for endpoint in call['endpoints']:
                method, path = endpoint.split(' ', 1)
                if method.lower() not in contracts[target]['paths'].get(path, {}):
                    raise ValueError(f'Undocumented peer endpoint: {target} {endpoint}')


def main():
    parser = argparse.ArgumentParser()
    # Retained for explicit CI intent; system validation is now always required.
    parser.add_argument('--require-system', action='store_true')
    parser.parse_args()
    system = yaml.safe_load((ROOT / 'system.yaml').read_text())
    schema = yaml.safe_load((ROOT / 'system.schema.json').read_text())
    contracts = {}
    for name, service in system['services'].items():
        path = (ROOT / service['openapi']).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('OpenAPI path must stay inside the repository')
        contracts[name] = yaml.safe_load(path.read_text())
        validate(contracts[name])
        print(f'Valid OpenAPI: {path.relative_to(ROOT)}')
    validate_system(system, schema, contracts)
    print('Valid system.yaml (official schema; deployment readiness checked separately)')


if __name__ == '__main__':
    main()
