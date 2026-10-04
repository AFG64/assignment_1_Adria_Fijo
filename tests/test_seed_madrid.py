"""The sample catalog must be safe to import into an existing journal."""

from contextlib import closing
import sqlite3

from backend.restaurant_domain import add_restaurant, list_all_restaurants
from database.seed_madrid import RESTAURANTS, seed_madrid


def test_seed_is_repeatable_and_preserves_saved_places(tmp_path):
    database_file = tmp_path / "journal.sqlite3"
    assert seed_madrid(database_file) == len(RESTAURANTS)
    assert next(place for place in list_all_restaurants(database_file) if place["title"] == "Botín")["street"] == "Calle de Cuchilleros, 17"
    saved_id = add_restaurant(database_file, "My place", city="Madrid")
    assert seed_madrid(database_file) == 0

    with closing(sqlite3.connect(database_file)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0] == len(RESTAURANTS) + 1
        assert connection.execute("SELECT COUNT(*) FROM saved_restaurants").fetchone()[0] == 1
        assert connection.execute("SELECT restaurant_id FROM saved_restaurants").fetchone()[0] == saved_id
