"""The location forms use the restaurant domain without making live map requests."""

import sqlite3

import pytest

from backend.geocoding import GeocodingError
from backend.restaurant_domain import add_restaurant
from backend.web import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    application = create_app()
    application.config.update(TESTING=True)
    return application


def test_create_restaurant_with_location(app, monkeypatch):
    lookups = []

    def fake_geocode(_database_path, query):
        lookups.append(query)
        return {"latitude": 41.4036, "longitude": 2.1744}

    monkeypatch.setattr("backend.web.geocode_address", fake_geocode)
    response = app.test_client().post("/restaurants", data={
        "title": "Test cafe", "city": "Barcelona", "address": "Carrer de Mallorca 401",
    })

    assert response.status_code == 302
    assert lookups == ["Carrer de Mallorca 401, Barcelona"]
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        row = connection.execute(
            "SELECT address, latitude, longitude FROM restaurants WHERE title = ?",
            ("Test cafe",),
        ).fetchone()
    assert row == ("Carrer de Mallorca 401", 41.4036, 2.1744)


def test_create_without_location_does_not_geocode(app, monkeypatch):
    monkeypatch.setattr("backend.web.geocode_address", lambda *_: pytest.fail("Unexpected geocode"))
    response = app.test_client().post("/restaurants", data={"title": "No address"})
    assert response.status_code == 302


def test_location_lookup_error_preserves_form_without_inserting(app, monkeypatch):
    def no_match(*_):
        raise GeocodingError("Location not found.")

    monkeypatch.setattr("backend.web.geocode_address", no_match)
    response = app.test_client().post("/restaurants", data={
        "title": "Test cafe", "address": "Unknown address",
    })
    assert response.status_code == 400
    assert b"Location not found." in response.data
    assert b'Unknown address' in response.data
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        assert connection.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0] == 0


def test_existing_restaurant_location_can_be_changed(app, monkeypatch):
    restaurant_id = add_restaurant(app.config["DATABASE_PATH"], "Test cafe")
    monkeypatch.setattr("backend.web.geocode_address", lambda *_: {
        "latitude": 41.4036, "longitude": 2.1744,
    })

    response = app.test_client().post(
        f"/restaurants/{restaurant_id}/location",
        data={"address": "Carrer de Mallorca 401, Barcelona"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Location and coordinates saved." in response.data
    assert b"41.4036" in response.data
    assert b"2.1744" in response.data
    assert b"openstreetmap.org/?mlat=" in response.data
    assert b"OpenStreetMap contributors" in response.data


def test_complete_address_is_not_combined_with_old_city(app, monkeypatch):
    restaurant_id = add_restaurant(app.config["DATABASE_PATH"], "Test cafe", city="Andorra")
    lookups = []

    def fake_geocode(_database_path, query):
        lookups.append(query)
        return {"latitude": 40.427, "longitude": -3.684}

    monkeypatch.setattr("backend.web.geocode_address", fake_geocode)
    response = app.test_client().post(
        f"/restaurants/{restaurant_id}/location",
        data={"address": "Calle de Velázquez 25, Madrid, 28001"},
    )

    assert response.status_code == 302
    assert lookups == ["Calle de Velázquez 25, Madrid, 28001"]


def test_failed_location_change_preserves_existing_coordinates(app, monkeypatch):
    restaurant_id = add_restaurant(
        app.config["DATABASE_PATH"], "Test cafe", address="Original",
        latitude=40.0, longitude=3.0,
    )

    def no_match(*_):
        raise GeocodingError("Location not found.")

    monkeypatch.setattr("backend.web.geocode_address", no_match)
    response = app.test_client().post(
        f"/restaurants/{restaurant_id}/location", data={"address": "Unknown address"},
    )
    assert response.status_code == 400
    assert b"Location not found." in response.data
    assert b"Unknown address" in response.data
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        row = connection.execute(
            "SELECT address, latitude, longitude FROM restaurants WHERE id = ?",
            (restaurant_id,),
        ).fetchone()
    assert row == ("Original", 40.0, 3.0)


def test_missing_restaurant_location_route_returns_404(app):
    response = app.test_client().post("/restaurants/999/location", data={"address": "Anywhere"})
    assert response.status_code == 404
