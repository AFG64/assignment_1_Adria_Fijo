from pathlib import Path
from service_runtime.application import create_app
from services.restaurants.api import register
from services.restaurants.seed import seed

app = create_app("restaurants", Path('/app/migrations'))
register(app)
seed()
