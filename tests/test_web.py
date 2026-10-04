"""The visit item form connects to dining history for the selected restaurant."""

import pytest

from backend.dining_history import add_visit, list_visits
from backend.restaurant_domain import add_restaurant, get_restaurant_details, list_saved_restaurants, remove_restaurant
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


def test_saved_details_form_updates_restaurant(app):
    path = app.config["DATABASE_PATH"]
    restaurant_id = add_restaurant(path, "Corner Cafe")

    response = app.test_client().post(
        f"/restaurants/{restaurant_id}/saved-details",
        data={"rating": "4.5", "notes": "  Great soup  ", "would_go_back": "0"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your saved details were updated" in response.data
    details = get_restaurant_details(path, restaurant_id)
    assert details["personal_rating"] == 4.5
    assert details["personal_notes"] == "Great soup"
    assert details["would_go_back"] == 0


def test_saved_details_form_requires_saved_restaurant_and_valid_rating(app):
    path = app.config["DATABASE_PATH"]
    restaurant_id = add_restaurant(path, "Corner Cafe")
    client = app.test_client()

    invalid = client.post(
        f"/restaurants/{restaurant_id}/saved-details",
        data={"rating": "7", "notes": "Keep this", "would_go_back": "1"},
    )
    assert invalid.status_code == 400
    assert b"Rating must be from 0 to 5" in invalid.data
    assert get_restaurant_details(path, restaurant_id)["personal_rating"] is None

    saved_id = get_restaurant_details(path, restaurant_id)["saved_id"]
    remove_restaurant(path, saved_id)
    unsaved = client.post(
        f"/restaurants/{restaurant_id}/saved-details",
        data={"rating": "4", "notes": "", "would_go_back": ""},
    )
    assert unsaved.status_code == 404


def test_unsaved_detail_can_be_saved_without_leaving_page(app):
    path = app.config["DATABASE_PATH"]
    restaurant_id = add_restaurant(path, "Corner Cafe")
    saved_id = get_restaurant_details(path, restaurant_id)["saved_id"]
    remove_restaurant(path, saved_id)
    client = app.test_client()

    detail = client.get(f"/restaurants/{restaurant_id}")
    assert b"Save to my list" in detail.data
    assert b'name="return_to" value="details"' in detail.data

    response = client.post(
        f"/restaurants/{restaurant_id}/save",
        data={"status": "visited", "return_to": "details"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Save to my list" not in response.data
    assert b"Record a visit" in response.data
    assert get_restaurant_details(path, restaurant_id)["saved_status"] == "visited"
