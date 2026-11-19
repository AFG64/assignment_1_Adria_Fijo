"""Public static config validation: avoid accidentally publishing credentials."""
import argparse

import pytest

from scripts.configure_ui import api_url


@pytest.mark.parametrize('url',['http://localhost:8001/','https://api.example.org','https://api.example.org/prefix/'])
def test_public_base_urls(url):
    assert api_url(url)==url.rstrip('/')


@pytest.mark.parametrize('url',['file:///tmp/private','javascript:alert(1)','http://user:secret@example.org','http://example.org?secret=value','http://example.org/#token','http://localhost:99999','not-a-url'])
def test_invalid_or_secret_urls_are_rejected(url):
    with pytest.raises(argparse.ArgumentTypeError):
        api_url(url)
