from pathlib import Path

from service_runtime.application import create_app

from services.dining.api import register

app = create_app("dining", Path(__file__).parent / "migrations")

register(app)
