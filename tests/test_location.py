import sqlite3

import pytest

from backend.restaurant_domain import add_restaurant, update_restaurant_location
from database import initialize_database


@pytest.fixture
def database_file(tmp_path):
    path = tmp_path / "restaurants.sqlite3"
    initialize_database(path)
    return path


def test_new_restaurant_keeps_address_and_coordinates(database_file):
    restaurant_id = add_restaurant(
        database_file,
        "Test cafe",
        city="Barcelona",
        address="Carrer de Mallorca 401, Barcelona",
        latitude=41.4036,
        longitude=2.1744,
    )

    with sqlite3.connect(database_file) as connection:
        row = connection.execute(
            "SELECT address, latitude, longitude FROM restaurants WHERE id = ?",
            (restaurant_id,),
        ).fetchone()
    assert row == ("Carrer de Mallorca 401, Barcelona", 41.4036, 2.1744)


def test_existing_restaurant_can_gain_a_location(database_file):
    restaurant_id = add_restaurant(database_file, "Test cafe")

    update_restaurant_location(
        database_file, restaurant_id, "Plaça de Catalunya, Barcelona", 41.387, 2.17,
    )

    with sqlite3.connect(database_file) as connection:
        row = connection.execute(
            "SELECT address, latitude, longitude FROM restaurants WHERE id = ?",
            (restaurant_id,),
        ).fetchone()
        saved_count = connection.execute(
            "SELECT COUNT(*) FROM saved_restaurants WHERE restaurant_id = ?",
            (restaurant_id,),
        ).fetchone()[0]
    assert row == ("Plaça de Catalunya, Barcelona", 41.387, 2.17)
    assert saved_count == 1


@pytest.mark.parametrize(
    "latitude, longitude",
    [(91, 2), (41, -181), (float("nan"), 2), (41, None)],
)
def test_invalid_coordinates_do_not_create_a_restaurant(database_file, latitude, longitude):
    with pytest.raises(ValueError):
        add_restaurant(
            database_file, "Invalid place", address="Somewhere",
            latitude=latitude, longitude=longitude,
        )

    with sqlite3.connect(database_file) as connection:
        assert connection.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0] == 0


def test_missing_restaurant_cannot_be_updated(database_file):
    with pytest.raises(ValueError, match="Restaurant not found"):
        update_restaurant_location(database_file, 999, "Somewhere", 41, 2)
