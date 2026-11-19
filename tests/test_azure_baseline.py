"""Baseline checks must preserve data and stop after an uncertain write."""
import pytest

from scripts.azure_baseline import BILL, ITEM, MARKER, exercise, only_match
from scripts.azure_common import SetupError


class ExistingBaseline:
    def __init__(self):
        self.methods = []

    def call(self, service, method, path, *args, **kwargs):
        self.methods.append(method)
        assert method == 'GET', 'Read-only baseline inspection attempted a write'
        if path == '/restaurants':
            return [{'id': 1, 'title': MARKER, 'saved': {'id': 2}, 'city': 'Madrid', 'category_name': 'Synthetic baseline'}]
        if path.endswith('/visits'):
            return [{'id': 3, 'notes': MARKER, 'visit_date': '2026-11-01', 'rating': 4,
                     'items': [{'id': 4, 'item_name': ITEM, 'quantity': 2, 'unit_price': 3.5}],
                     'bills': [{'id': 5}]}]
        if '/bills/' in path:
            return BILL
        return {'status': 'visited'}


def test_existing_baseline_is_inspected_without_mutations():
    api = ExistingBaseline()
    result = exercise(api)
    assert result['saved_id'] == 2 and result['bill_id'] == 5
    assert len(result['bill_sha256']) == 64
    assert exercise(api, populate=True) == result # Repeat is also read-only.


def test_uncertain_write_is_never_automatically_retried():
    calls = []

    class Uncertain:
        def call(self, service, method, path, *args, **kwargs):
            calls.append(method)
            if method == 'GET':
                return []
            raise SetupError('Outcome uncertain')

    with pytest.raises(SetupError, match='uncertain'):
        exercise(Uncertain(), populate=True)
    assert calls == ['GET', 'POST']


def test_missing_baseline_is_not_created_by_inspect():
    class Empty:
        def call(self, service, method, path):
            assert method == 'GET'
            return []

    with pytest.raises(SetupError, match='populate explicitly'):
        exercise(Empty())


def test_duplicate_marker_is_not_silently_selected():
    with pytest.raises(SetupError, match='Multiple'):
        only_match([{'title': MARKER}, {'title': MARKER}], lambda row: row['title'] == MARKER, 'restaurant')
