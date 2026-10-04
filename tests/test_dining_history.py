"""Business rules for visits and their bills."""

import sqlite3
from contextlib import closing

import pytest

from backend.dining_history import (
    add_bill,
    add_visit,
    add_visit_item,
    get_bill_path,
    get_visit,
    list_bill_paths,
    list_visits,
)
from backend.restaurant_domain import (
    add_restaurant,
    get_restaurant_details,
    list_saved_restaurants,
    remove_restaurant,
)
from database import initialize_database


@pytest.fixture
def database_file(tmp_path):
    path = tmp_path / "restaurants.sqlite3"
    initialize_database(path)
    return path


def add_saved_restaurant(database_file, title):
    restaurant_id = add_restaurant(database_file, title)
    saved_id = list_saved_restaurants(database_file)[0]["saved_id"]
    return restaurant_id, saved_id


def test_recording_visit_marks_restaurant_visited(database_file):
    restaurant_id, saved_id = add_saved_restaurant(database_file, "Corner Cafe")
    assert get_restaurant_details(database_file, restaurant_id)["saved_status"] == "want_to_go"

    visit_id = add_visit(database_file, saved_id, "2026-10-01", rating=4.5, notes="Good lunch")

    assert visit_id > 0
    assert get_restaurant_details(database_file, restaurant_id)["saved_status"] == "visited"
    assert list_visits(database_file, saved_id) == [{
        "id": visit_id,
        "visit_date": "2026-10-01",
        "rating": 4.5,
        "notes": "Good lunch",
        "bills": [],
        "items": [],
    }]


def test_visits_and_bills_are_grouped_newest_first(database_file):
    _, saved_id = add_saved_restaurant(database_file, "Corner Cafe")
    old_visit = add_visit(database_file, saved_id, "2026-09-01")
    new_visit = add_visit(database_file, saved_id, "2026-10-01")
    first_bill = add_bill(database_file, new_visit, "bills/first.pdf")
    second_bill = add_bill(database_file, new_visit, "bills/second.pdf")

    visits = list_visits(database_file, saved_id)

    assert [visit["id"] for visit in visits] == [new_visit, old_visit]
    assert [bill["id"] for bill in visits[0]["bills"]] == [second_bill, first_bill]
    assert visits[1]["bills"] == []
    assert set(list_bill_paths(database_file, saved_id)) == {
        "bills/first.pdf", "bills/second.pdf",
    }


def test_bill_and_visit_lookups_check_restaurant_ownership(database_file):
    _, first_saved_id = add_saved_restaurant(database_file, "First Cafe")
    _, other_saved_id = add_saved_restaurant(database_file, "Other Cafe")
    visit_id = add_visit(database_file, first_saved_id, "2026-10-01")
    bill_id = add_bill(database_file, visit_id, "bills/receipt.pdf")

    assert get_visit(database_file, first_saved_id, visit_id)[0] == visit_id
    assert get_visit(database_file, other_saved_id, visit_id) is None
    assert get_bill_path(database_file, first_saved_id, visit_id, bill_id) == "bills/receipt.pdf"
    assert get_bill_path(database_file, other_saved_id, visit_id, bill_id) is None
    assert get_bill_path(database_file, first_saved_id, visit_id, 999) is None
    assert list_bill_paths(database_file, other_saved_id) == []


def test_ordered_items_stay_with_their_visit(database_file):
    _, saved_id = add_saved_restaurant(database_file, "Corner Cafe")
    first_visit = add_visit(database_file, saved_id, "2026-09-01")
    second_visit = add_visit(database_file, saved_id, "2026-10-01")
    add_visit_item(database_file, first_visit, "Coffee")
    item_id = add_visit_item(database_file, second_visit, "  Pasta  ", 2, "12.50")

    visits = list_visits(database_file, saved_id)
    assert visits[0]["items"] == [{
        "id": item_id, "item_name": "Pasta", "quantity": 2, "unit_price": 12.5,
    }]
    assert visits[1]["items"][0]["item_name"] == "Coffee"


@pytest.mark.parametrize("values", [
    ("", 1, None),
    ("Pasta", 0, None),
    ("Pasta", "half", None),
    ("Pasta", 1, "-1"),
    ("Pasta", 1, "nan"),
])
def test_invalid_ordered_item_is_not_saved(database_file, values):
    _, saved_id = add_saved_restaurant(database_file, "Corner Cafe")
    visit_id = add_visit(database_file, saved_id, "2026-10-01")
    with pytest.raises(ValueError):
        add_visit_item(database_file, visit_id, *values)
    assert list_visits(database_file, saved_id)[0]["items"] == []


def test_removing_saved_restaurant_cascades_to_visits_and_bills(database_file):
    restaurant_id, saved_id = add_saved_restaurant(database_file, "Corner Cafe")
    visit_id = add_visit(database_file, saved_id, "2026-10-01")
    add_bill(database_file, visit_id, "bills/receipt.pdf")

    remove_restaurant(database_file, saved_id)

    assert get_restaurant_details(database_file, restaurant_id)["saved_id"] is None
    assert list_visits(database_file, saved_id) == []
    assert list_bill_paths(database_file, saved_id) == []
    with closing(sqlite3.connect(database_file)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM visits").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM bills").fetchone()[0] == 0


def test_visits_require_an_existing_saved_restaurant(database_file):
    with pytest.raises(ValueError, match="Saved restaurant ID is required"):
        add_visit(database_file, 0, "2026-10-01")
    with pytest.raises(sqlite3.IntegrityError):
        add_visit(database_file, 999, "2026-10-01")


def test_bills_require_a_visit_and_path(database_file):
    with pytest.raises(ValueError, match="visit id is needed"):
        add_bill(database_file, 0, "bills/receipt.pdf")
    with pytest.raises(ValueError, match="Image path is required"):
        add_bill(database_file, 1, "")
    with pytest.raises(sqlite3.IntegrityError):
        add_bill(database_file, 999, "bills/receipt.pdf")
