from contextlib import closing
import sqlite3

from storage import connect_database


def add_restaurant(
    database_path,
    title,
    category_name=None,
    city=None,
    price=None,
    rating=None,
    notes=None,
    status="want_to_go",
):

    title = title.strip() if title else ""
    if not title:
        raise ValueError("Restaurant name is required.")

    if price not in (None, ""):
        price = int(price)
        if price < 1 or price > 4:
            raise ValueError("Price must be from 1 to 4.")
    else:
        price = None

    if rating not in (None, ""):
        rating = float(rating)
        if rating < 0 or rating > 5:
            raise ValueError("Rating must be from 0 to 5.")
    else:
        rating = None

    if status not in ("want_to_go", "visited"):
        raise ValueError("Status must be 'want_to_go' or 'visited'.")

    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO restaurants (title, category_name, city, price)
            VALUES (?, ?, ?, ?)
            """,
            (title, category_name, city, price),
        )
        restaurant_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO saved_restaurants
                (restaurant_id, status, rating, notes)
            VALUES (?, ?, ?, ?)
            """,
            (restaurant_id, status, rating, notes),
        )

    return restaurant_id


def list_restaurants(database_path):
    """Return the saved collection for the home page, newest first."""
    with closing(connect_database(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT r.id, r.title, r.category_name, r.city, r.price,
                   s.status, s.rating
            FROM restaurants AS r
            JOIN saved_restaurants AS s ON s.restaurant_id = r.id
            ORDER BY s.saved_at DESC, s.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]
