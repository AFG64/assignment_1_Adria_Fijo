"""The catalog page passes filters to the restaurant collection."""

import pytest

from backend.restaurant_domain import add_restaurant, list_saved_restaurants, remove_restaurant
from backend.web import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    application = create_app()
    application.config.update(TESTING=True)
    database_file = application.config["DATABASE_PATH"]
    add_restaurant(database_file, "Alpha Cafe", category_name="Italian", city="Madrid",
                   price=2, rating=4.5, status="visited")
    add_restaurant(database_file, "Beta Cafe", category_name="Sushi", city="Barcelona",
                   price=3, rating=3, status="want_to_go")
    unsaved_id = add_restaurant(database_file, "Gamma Cafe", category_name="Italian", city="Madrid")
    saved_id = next(
        place["saved_id"] for place in list_saved_restaurants(database_file)
        if place["id"] == unsaved_id
    )
    remove_restaurant(database_file, saved_id)
    return application


def test_catalog_form_filters_and_keeps_choices(app):
    response = app.test_client().get("/restaurants", query_string={
        "category": "ital", "city": "madrid", "price": "2",
        "min_rating": "4", "status": "visited",
    })
    assert response.status_code == 200
    assert b"Alpha Cafe" in response.data
    assert b"Beta Cafe" not in response.data
    assert b"Gamma Cafe" not in response.data
    assert b"1 restaurant matches your filters" in response.data
    assert b'value="madrid"' in response.data
    assert b'<details class="filter-panel" open>' in response.data


def test_catalog_filters_start_collapsed(app):
    response = app.test_client().get("/restaurants")
    assert b'<details class="filter-panel" >' in response.data
    assert b'<summary>Filters' in response.data


def test_catalog_can_show_only_unsaved_restaurants(app):
    response = app.test_client().get("/restaurants?status=unsaved")
    assert response.status_code == 200
    assert b"Gamma Cafe" in response.data
    assert b"Alpha Cafe" not in response.data
    assert b"Clear filters" in response.data


def test_no_matches_has_clear_message(app):
    response = app.test_client().get("/restaurants?city=Paris")
    assert response.status_code == 200
    assert b"No restaurants match these filters" in response.data


def test_invalid_filter_returns_helpful_error(app):
    response = app.test_client().get("/restaurants?min_rating=99")
    assert response.status_code == 400
    assert b"Minimum rating must be from 0 to 5" in response.data
    assert b"Alpha Cafe" in response.data
