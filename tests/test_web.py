"""The visit item form connects to dining history for the selected restaurant."""

import pytest

from backend.dining_history import add_visit, list_visits
from backend.restaurant_domain import add_restaurant, list_saved_restaurants
from backend.web import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    application = create_app()
    application.config.update(TESTING=True)
    return application


def test_add_ordered_item_from_visit_page(app):
    path = app.config["DATABASE_PATH"]
    restaurant_id = add_restaurant(path, "Corner Cafe")
    saved_id = list_saved_restaurants(path)[0]["saved_id"]
    visit_id = add_visit(path, saved_id, "2026-10-01")

    response = app.test_client().post(
        f"/restaurants/{restaurant_id}/visits/{visit_id}/items",
        data={"item_name": "Pasta", "quantity": "2", "unit_price": "12.50"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Pasta" in response.data
    assert list_visits(path, saved_id)[0]["items"][0]["quantity"] == 2


def test_item_form_rejects_visit_from_another_restaurant(app):
    path = app.config["DATABASE_PATH"]
    first_id = add_restaurant(path, "First Cafe")
    first_saved_id = list_saved_restaurants(path)[0]["saved_id"]
    second_id = add_restaurant(path, "Second Cafe")
    visit_id = add_visit(path, first_saved_id, "2026-10-01")

    response = app.test_client().post(
        f"/restaurants/{second_id}/visits/{visit_id}/items",
        data={"item_name": "Pasta", "quantity": "1"},
    )

    assert first_id != second_id
    assert response.status_code == 404
    assert list_visits(path, first_saved_id)[0]["items"] == []
