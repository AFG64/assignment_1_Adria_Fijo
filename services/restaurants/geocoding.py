"""Bounded Nominatim-compatible lookup; one worker, rate limit and bounded cache."""
from functools import lru_cache
import json
import os
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_last_lookup = 0.0


@lru_cache(maxsize=256)
def locate(address, city=None):
    global _last_lookup
    query = address if ',' in address or not city else f'{address}, {city}'
    time.sleep(max(0, 1 - (time.monotonic() - _last_lookup)))
    _last_lookup = time.monotonic()
    url = os.getenv('GEOCODER_BASE_URL', 'https://nominatim.openstreetmap.org').rstrip('/')
    request = Request(url + '/search?' + urlencode({'q': query, 'format': 'jsonv2', 'limit': 1}),
                      headers={'User-Agent': 'Picky-assignment/2 (restaurant address lookup)'})
    try:
        with urlopen(request, timeout=float(os.getenv('GEOCODER_TIMEOUT_S', '5'))) as response:
            results = json.load(response)
        latitude, longitude = float(results[0]['lat']), float(results[0]['lon'])
        from .api import number
        return {'latitude': number(latitude, -90, 90), 'longitude': number(longitude, -180, 180)}
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise ValueError('Address lookup unavailable; use manual coordinates.') from exc
