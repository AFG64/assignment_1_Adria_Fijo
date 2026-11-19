"""Small HTTP boundary: explicit timeout, bounded body, no redirects or retries."""
from http.client import HTTPException
import json
import math
import os
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class PeerUnavailable(Exception):
    pass


class PeerMissing(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(method, path, url_env, timeout_env, expected=200):
    try:
        base = os.getenv(url_env, '').rstrip('/')
        timeout = float(os.getenv(timeout_env, '2'))
        if urlsplit(base).scheme not in ('http', 'https') or not math.isfinite(timeout) or not 0 < timeout <= 10:
            raise ValueError('Invalid peer configuration')
    except ValueError as exc:
        raise PeerUnavailable() from exc
    request = Request(base + path, method=method, headers={'Accept': 'application/json'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            if response.status != expected:
                raise PeerUnavailable()
            if expected == 204:
                return None
            raw = response.read(65537)
            if len(raw) > 65536:
                raise PeerUnavailable()
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise PeerUnavailable()
            return result
    except HTTPError as exc:
        if exc.code == 404:
            raise PeerMissing() from exc
        raise PeerUnavailable() from exc
    except (OSError, HTTPException, ValueError) as exc:
        raise PeerUnavailable() from exc
