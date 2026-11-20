"""Compose-only entry point: resolve the own mounted password, then exec the command.

Azure uses the image's original command and complete secret-backed DATABASE_URL.
Compose exec checks invoke this module explicitly because exec starts a new process.
"""
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

MARKER = 'LOCAL_PASSWORD_FROM_VOLUME'


def environment(source=None, password_file=Path('/run/picky/password')):
    result = dict(os.environ if source is None else source)
    url = result.get('DATABASE_URL', '')
    if urlsplit(url).password == MARKER:
        parsed = urlsplit(url)
        if parsed.scheme != 'mssql' or parsed.hostname != 'sql' or parsed.username not in ('picky_restaurants', 'picky_dining'):
            raise ValueError('Mounted local credentials may only connect to the local SQL service')
        password = password_file.read_text().strip()
        if not re.fullmatch(r'Aa1[0-9a-f]{48}', password):
            raise ValueError('Invalid local credential file')
        result['DATABASE_URL'] = url.replace(':' + MARKER + '@', ':' + password + '@', 1)
    return result


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Provide the local service command')
    try:
        configured = environment()
    except (OSError, ValueError):
        raise SystemExit('Own local password is unavailable; start the compose initialization first.') from None
    os.execvpe(sys.argv[1], sys.argv[1:], configured)


if __name__ == '__main__':
    main()
