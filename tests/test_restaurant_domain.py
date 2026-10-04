"""Business rules for the restaurant collection."""

import sqlite3
from contextlib import closing

import pytest

from backend.restaurant_domain import (
    add_restaurant,
    get_restaurant_details,
    list_all_restaurants,
    list_saved_restaurants,
    remove_restaurant,
    save_existing_restaurant,
    update_saved_details,
)
from database import initialize_database


@pytest.fixture
def database_file(tmp_path):
    path = tmp_path / "restaurants.sqlite3"
    initialize_database(path)
    return path


def test_add_restaurant_saves_general_and_personal_details(database_file):
    restaurant_id = add_restaurant(
        database_file, "  Corner Cafe  ", category_name="Cafe", city="Madrid",
        price=2, rating=4.5, notes="Good coffee", status="visited",
    )

    details = get_restaurant_details(database_file, restaurant_id)
    assert details["title"] == "Corner Cafe"
    assert details["category_name"] == "Cafe"
    assert details["city"] == "Madrid"
    assert details["price"] == 2
    assert details["saved_status"] == "visited"
    assert details["personal_rating"] == 4.5
    assert details["personal_notes"] == "Good coffee"


@pytest.mark.parametrize("changes", [
    {"title": "  "},
    {"price": 0},
    {"price": 5},
    {"rating": -1},
    {"rating": 6},
    {"status": "maybe"},
])
def test_invalid_restaurant_is_not_saved(database_file, changes):
    fields = {"title": "Corner Cafe", **changes}
    with pytest.raises(ValueError):
        add_restaurant(database_file, **fields)

    assert list_all_restaurants(database_file) == []


def test_removing_saved_entry_keeps_catalog_restaurant(database_file):
    first_id = add_restaurant(database_file, "Zebra Cafe")
    second_id = add_restaurant(database_file, "Alpha Cafe")
    saved = list_saved_restaurants(database_file)
    assert [place["title"] for place in saved] == ["Alpha Cafe", "Zebra Cafe"]

    first_saved_id = next(place["saved_id"] for place in saved if place["id"] == first_id)
    remove_restaurant(database_file, first_saved_id)

    assert [place["id"] for place in list_saved_restaurants(database_file)] == [second_id]
    catalog = list_all_restaurants(database_file)
    assert [place["title"] for place in catalog] == ["Alpha Cafe", "Zebra Cafe"]
    assert catalog[1]["saved_id"] is None
    assert get_restaurant_details(database_file, first_id)["saved_id"] is None


def test_existing_catalog_restaurant_can_be_saved_again(database_file):
    restaurant_id = add_restaurant(database_file, "Corner Cafe")
    saved_id = list_saved_restaurants(database_file)[0]["saved_id"]
    remove_restaurant(database_file, saved_id)

    save_existing_restaurant(database_file, restaurant_id, status="visited")

    assert get_restaurant_details(database_file, restaurant_id)["saved_status"] == "visited"
    with pytest.raises(sqlite3.IntegrityError):
        save_existing_restaurant(database_file, restaurant_id, status="visited")
    assert len(list_saved_restaurants(database_file)) == 1


def test_missing_saved_entry_cannot_be_removed(database_file):
    with pytest.raises(ValueError, match="Saved restaurant not found"):
        remove_restaurant(database_file, 999)
    with pytest.raises(ValueError, match="Saved restaurant ID is required"):
        remove_restaurant(database_file, 0)


def test_saved_details_can_be_changed_and_cleared(database_file):
    restaurant_id = add_restaurant(database_file, "Corner Cafe", rating=4, notes="Old note")
    saved_id = get_restaurant_details(database_file, restaurant_id)["saved_id"]

    update_saved_details(database_file, saved_id, "4.5", "  Try the soup  ", "1")
    details = get_restaurant_details(database_file, restaurant_id)
    assert (details["personal_rating"], details["personal_notes"], details["would_go_back"]) == (
        4.5, "Try the soup", 1,
    )

    update_saved_details(database_file, saved_id, "", "", "")
    details = get_restaurant_details(database_file, restaurant_id)
    assert details["personal_rating"] is None
    assert details["personal_notes"] is None
    assert details["would_go_back"] is None


@pytest.mark.parametrize("values", [
    ("bad", "", ""), ("nan", "", ""), ("6", "", ""),
    ("4", "", "maybe"), ("4", "x" * 2001, "1"),
])
def test_invalid_saved_details_do_not_change_existing_values(database_file, values):
    restaurant_id = add_restaurant(database_file, "Corner Cafe", rating=3, notes="Keep this")
    saved_id = get_restaurant_details(database_file, restaurant_id)["saved_id"]

    with pytest.raises(ValueError):
        update_saved_details(database_file, saved_id, *values)

    details = get_restaurant_details(database_file, restaurant_id)
    assert details["personal_rating"] == 3
    assert details["personal_notes"] == "Keep this"


def test_missing_saved_details_cannot_be_updated(database_file):
    with pytest.raises(ValueError, match="Saved restaurant ID is required"):
        update_saved_details(database_file, 0, "", "", "")
    with pytest.raises(ValueError, match="Saved restaurant not found"):
        update_saved_details(database_file, 999, "", "", "")


def test_missing_restaurant_details_returns_none(database_file):
    assert get_restaurant_details(database_file, 999) is None
    with pytest.raises(ValueError, match="Restaurant ID is required"):
        get_restaurant_details(database_file, 0)


def test_saved_entry_requires_existing_restaurant_and_valid_status(database_file):
    with pytest.raises(ValueError, match="Invalid status"):
        save_existing_restaurant(database_file, 1, status="maybe")
    with pytest.raises(sqlite3.IntegrityError):
        save_existing_restaurant(database_file, 999)
    with closing(sqlite3.connect(database_file)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM saved_restaurants").fetchone()[0] == 0


def test_catalog_filters_can_be_combined(database_file):
    first_id = add_restaurant(
        database_file, "Alpha", category_name="Italian", city="Madrid",
        price=2, rating=4.5, status="visited",
    )
    add_restaurant(
        database_file, "Beta", category_name="Sushi", city="Barcelona",
        price=3, rating=3, status="want_to_go",
    )
    unsaved_id = add_restaurant(
        database_file, "Gamma", category_name="Italian", city="Madrid", price=1,
    )
    saved_id = next(
        place["saved_id"] for place in list_saved_restaurants(database_file)
        if place["id"] == unsaved_id
    )
    remove_restaurant(database_file, saved_id)

    def ids(**filters):
        return [place["id"] for place in list_all_restaurants(database_file, **filters)]

    assert ids(category="ital") == [first_id, unsaved_id]
    assert ids(city="MAD") == [first_id, unsaved_id]
    assert ids(price="2") == [first_id]
    assert ids(min_rating="4") == [first_id]
    assert ids(status="visited") == [first_id]
    assert ids(status="unsaved") == [unsaved_id]
    assert ids(category="%") == []
    assert ids(city="Madrid", price="2", min_rating="4", status="visited") == [first_id]
    assert ids(city="Madrid", status="want_to_go") == []


@pytest.mark.parametrize("filters", [
    {"price": "0"},
    {"min_rating": "bad"},
    {"min_rating": "nan"},
    {"min_rating": "6"},
    {"status": "saved"},
])
def test_invalid_catalog_filter_is_rejected(database_file, filters):
    with pytest.raises(ValueError):
        list_all_restaurants(database_file, **filters)
