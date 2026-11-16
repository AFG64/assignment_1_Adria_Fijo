"""Own-database health and structured request logs for both service processes."""
import json
import logging
import os
import sys
import time

from flask import Flask, g, request

from .database import migrate, probe


def create_app(service_name, migration_directory):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
    app = Flask(service_name)
    database_url = os.environ['DATABASE_URL']
    version = os.getenv('VERSION', 'local')
    ui_origin = os.getenv('UI_ORIGIN', 'http://localhost:8080')
    migrate(database_url, migration_directory)

    @app.before_request
    def start_request():
        g.started = time.monotonic()

    @app.after_request
    def finish_request(response):
        if request.headers.get('Origin') == ui_origin:
            response.headers['Access-Control-Allow-Origin'] = ui_origin
            response.headers.add('Vary', 'Origin')
        app.logger.info(json.dumps({
            'service': service_name, 'version': version,
            'method': request.method, 'path': request.path,
            'status': response.status_code,
            'duration_ms': round((time.monotonic() - g.started) * 1000, 2),
        }))
        return response

    @app.get('/health')
    def health():
        try:
            probe(database_url)
        except Exception:
            # Driver exceptions may contain connection information; never expose them.
            app.logger.warning('own database health probe failed')
            return {'status': 'unavailable', 'db': 'unavailable', 'version': version}, 503
        return {'status': 'ok', 'db': 'ok', 'version': version}

    return app
