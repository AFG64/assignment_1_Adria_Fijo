import json

import pytest

from backend import geocoding


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _size):
        return self.body


def test_lookup_uses_identifying_header_and_persistent_cache(tmp_path, monkeypatch):
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeResponse(json.dumps([{
            "lat": "41.4036", "lon": "2.1744", "display_name": "Barcelona, Spain",
        }]).encode())

    monkeypatch.setattr(geocoding, "urlopen", fake_urlopen)
    monkeypatch.setattr(geocoding, "_last_request_at", 0.0)
    database_path = tmp_path / "restaurants.sqlite3"

    first = geocoding.geocode_address(database_path, "Carrer de Mallorca 401, Barcelona")
    second = geocoding.geocode_address(database_path, "carrer de mallorca 401, barcelona")

    assert first == second == {
        "latitude": 41.4036, "longitude": 2.1744,
        "display_name": "Barcelona, Spain",
    }
    assert len(requests) == 1
    assert requests[0][0].get_header("User-agent") == geocoding.USER_AGENT
    assert "format=jsonv2" in requests[0][0].full_url
    assert "limit=1" in requests[0][0].full_url
    assert requests[0][1] == 5
    assert (tmp_path / "geocoding_cache.json").is_file()


def test_missing_result_is_cached(tmp_path, monkeypatch):
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return FakeResponse(b"[]")

    monkeypatch.setattr(geocoding, "urlopen", fake_urlopen)
    monkeypatch.setattr(geocoding, "_last_request_at", 0.0)
    database_path = tmp_path / "restaurants.sqlite3"

    for _ in range(2):
        with pytest.raises(geocoding.GeocodingError, match="Location not found"):
            geocoding.geocode_address(database_path, "Unknown location")
    assert len(requests) == 1


def test_query_includes_city_once():
    assert geocoding.search_query("Main Street 1", "Madrid") == "Main Street 1, Madrid"
    assert geocoding.search_query("Main Street 1, Madrid", "Madrid") == "Main Street 1, Madrid"
    assert geocoding.search_query("Calle de Velázquez 25, Madrid", "Andorra") == "Calle de Velázquez 25, Madrid"
    assert geocoding.search_query("Calle de Velázquez 25, Madrid, 28001", "Andorra") == "Calle de Velázquez 25, Madrid, 28001"


def test_new_search_waits_for_one_request_per_second(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr(geocoding, "_last_request_at", 10.0)
    monkeypatch.setattr(geocoding, "monotonic", lambda: 10.2)
    monkeypatch.setattr(geocoding, "sleep", waits.append)
    monkeypatch.setattr(geocoding, "urlopen", lambda *_args, **_kwargs: FakeResponse(b"[]"))

    with pytest.raises(geocoding.GeocodingError, match="Location not found"):
        geocoding.geocode_address(tmp_path / "restaurants.sqlite3", "Another location")

    assert waits == [pytest.approx(0.85)]
