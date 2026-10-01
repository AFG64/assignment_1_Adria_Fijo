from contextlib import closing
import sqlite3

from database import connect_database


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


def list_saved_restaurants(database_path):
    """Return the saved collection for the home page, newest first."""
    with closing(connect_database(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT r.id, r.title, r.category_name, r.city, r.price,
                   s.id AS saved_id, s.status, s.rating
            FROM restaurants AS r
            JOIN saved_restaurants AS s ON s.restaurant_id = r.id
            ORDER BY s.saved_at DESC, s.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_all_restaurants(database_path):
    """Return all restaurant rows, whether or not they are saved."""
    with closing(connect_database(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT r.id, r.title, r.category_name, r.city, r.price,
                   r.total_score, s.id AS saved_id,
                   s.status AS saved_status, s.rating AS personal_rating
            FROM restaurants AS r
            LEFT JOIN saved_restaurants AS s ON s.restaurant_id = r.id
            ORDER BY r.title COLLATE NOCASE, r.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def remove_restaurant(database_path, saved_restaurant_id: int) -> None:
    """Remove a saved entry while keeping its restaurant row."""

    if not saved_restaurant_id:
        raise ValueError("Saved restaurant ID is required.")

    with connect_database(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM saved_restaurants WHERE id = ?",
            (saved_restaurant_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError("Saved restaurant not found.")





def save_existing_restaurant(database_path, restaurant_id, status="want_to_go"):
    "save restaurant to the personal list and makr wanted to go or visited"

    if not restaurant_id:
        raise ValueError("Restaurant ID is required.")

    if status not in ("want_to_go", "visited"):
        raise ValueError("Invalid status.")

    with connect_database(database_path) as connection:
        connection.execute(
            """
            INSERT INTO saved_restaurants (restaurant_id, status)
            VALUES (?, ?)
            """,
            (restaurant_id, status),
        )



def get_restaurant_details(database_path, restaurant_id):

    "get the details from exisitng restaurant"

    if not restaurant_id:
            raise ValueError("Restaurant ID is required.")

    with connect_database(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """SELECT r.*,
                   s.id AS saved_id,
                   s.status AS saved_status,
                   s.rating AS personal_rating,
                   s.notes AS personal_notes,
                   s.would_go_back,
                   s.saved_at
            FROM restaurants AS r
            LEFT JOIN saved_restaurants AS s
                ON s.restaurant_id = r.id
            WHERE r.id = ?
            """,
            (restaurant_id,),
        ).fetchone()

    return dict(row) if row else None
