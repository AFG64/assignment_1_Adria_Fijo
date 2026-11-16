from pathlib import Path

from service_runtime.application import create_app

app = create_app("dining", Path(__file__).parent / "migrations")
