"""Look up a user-entered restaurant address with a cached Nominatim search."""

import json
import math
import os
from pathlib import Path
from threading import Lock
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


DEFAULT_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "Picky/1.0 (+https://github.com/AFG64/devops-food)"
_request_lock = Lock()
_last_request_at = 0.0


class GeocodingError(ValueError):
    """An address could not be resolved to usable coordinates."""


def search_query(address, city=None):
    """Use a full address as entered; add the saved city only to short queries."""
    address = (address or "").strip()
    city = (city or "").strip()
    if not address:
        raise GeocodingError("Enter a street address or place to find coordinates.")
    if city and "," not in address and city.casefold() not in address.casefold():
        return f"{address}, {city}"
    return address


def _read_cache(path):
    if not path.exists():
        return {}
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GeocodingError("The location cache could not be read. Try again later.") from error
    if not isinstance(cache, dict):
        raise GeocodingError("The location cache could not be read. Try again later.")
    return cache


def _write_cache(path, cache):
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    except OSError as error:
        raise GeocodingError("The location cache could not be saved. Try again later.") from error
    finally:
        temporary.unlink(missing_ok=True)


def geocode_address(database_path, query):
    """Return a cached {latitude, longitude, display_name} result for one query."""
    global _last_request_at

    query = query.strip()
    if not query or len(query) > 400:
        raise GeocodingError("Enter a location of 400 characters or fewer.")
    base_url = os.environ.get("GEOCODER_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if not base_url.startswith(("https://", "http://")):
        raise GeocodingError("The geocoding service URL is invalid.")
    cache_path = Path(database_path).parent / "geocoding_cache.json"
    key = f"{base_url}|{query.casefold()}"

    # The single Flask process shares this lock, cache, and request limit.
    with _request_lock:
        cache = _read_cache(cache_path)
        if key in cache:
            result = cache[key]
        else:
            if _last_request_at:
                delay = 1.05 - (monotonic() - _last_request_at)
                if delay > 0:
                    sleep(delay)
            parameters = urlencode({"q": query, "format": "jsonv2", "limit": 1})
            request = Request(
                f"{base_url}/search?{parameters}",
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            _last_request_at = monotonic()
            try:
                with urlopen(request, timeout=5) as response:
                    body = response.read(65537)
                if len(body) > 65536:
                    raise GeocodingError("The location service returned too much data.")
                matches = json.loads(body)
            except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
                raise GeocodingError("The location service is unavailable. Try again later.") from error
            if not isinstance(matches, list):
                raise GeocodingError("The location service returned an invalid result.")
            if not matches:
                result = None
            else:
                try:
                    first = matches[0]
                    latitude = float(first["lat"])
                    longitude = float(first["lon"])
                    if (not math.isfinite(latitude) or not -90 <= latitude <= 90
                            or not math.isfinite(longitude) or not -180 <= longitude <= 180):
                        raise ValueError("Coordinates outside valid range")
                    result = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "display_name": str(first.get("display_name", query)),
                    }
                except (KeyError, TypeError, ValueError, AttributeError) as error:
                    raise GeocodingError("The location service returned invalid coordinates.") from error
            cache[key] = result
            _write_cache(cache_path, cache)

    if result is None:
        raise GeocodingError("Location not found. Try a full address with city and postal code, or enter coordinates manually below.")
    return result
