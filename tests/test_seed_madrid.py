"""The sample catalog must be safe to import into an existing journal."""

import sqlite3

from backend.restaurant_domain import add_restaurant
from database.seed_madrid import RESTAURANTS, seed_madrid


def test_seed_is_repeatable_and_preserves_saved_places(tmp_path):
    database_file = tmp_path / "journal.sqlite3"
    assert seed_madrid(database_file) == len(RESTAURANTS)
    saved_id = add_restaurant(database_file, "My place", city="Madrid")
    assert seed_madrid(database_file) == 0

    with sqlite3.connect(database_file) as connection:
        assert connection.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0] == len(RESTAURANTS) + 1
        assert connection.execute("SELECT COUNT(*) FROM saved_restaurants").fetchone()[0] == 1
        assert connection.execute("SELECT restaurant_id FROM saved_restaurants").fetchone()[0] == saved_id
