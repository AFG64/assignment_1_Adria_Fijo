"""Enforce independent floors for transitional domains and shared service runtime."""
import json
from pathlib import Path

report = json.loads(Path('coverage.json').read_text())
for name in ('restaurant_domain', 'dining_history'):
    filename = f'backend/{name}.py'
    percent = report['files'][filename]['summary']['percent_covered']
    print(f'{filename}: {percent:.2f}%')
    if percent < 70:
        raise SystemExit(f'{filename} is below 70% coverage')

for filename in ('service_runtime/application.py', 'service_runtime/database.py'):
    percent = report['files'][filename]['summary']['percent_covered']
    print(f'{filename}: {percent:.2f}%')
    if percent < 70:
        raise SystemExit(f'{filename} is below 70% coverage')

for module in ('api', 'catalog', 'geocoding', 'seed'):
    filename = f'services/restaurants/{module}.py'
    percent = report['files'][filename]['summary']['percent_covered']
    print(f'{filename}: {percent:.2f}%')
    if percent < 70:
        raise SystemExit(f'{filename} is below 70% coverage')
