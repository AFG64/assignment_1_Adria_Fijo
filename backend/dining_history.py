from contextlib import closing
import sqlite3

from database import connect_database


def add_visit(database_path, saved_restaurant_id, visit_date, rating=None, notes=None):
    if not saved_restaurant_id:
        raise ValueError("Saved restaurant ID is required.")

    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO visits (saved_restaurant_id, visit_date, rating, notes)
            VALUES (?, ?, ?, ?)
            """,
            (saved_restaurant_id, visit_date, rating, notes),
        )
        connection.execute(
            "UPDATE saved_restaurants SET status = 'visited' WHERE id = ?",
            (saved_restaurant_id,),
        )

    return cursor.lastrowid


def list_visits(database_path, saved_restaurant_id):
    """Return a saved restaurant's visits and attached bills, newest first."""
    with closing(connect_database(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT v.id, v.visit_date, v.rating, v.notes,
                   b.id AS bill_id, b.image_path, b.uploaded_at
            FROM visits AS v
            LEFT JOIN bills AS b ON b.visit_id = v.id
            WHERE v.saved_restaurant_id = ?
            ORDER BY v.visit_date DESC, v.id DESC, b.id DESC
            """,
            (saved_restaurant_id,),
        ).fetchall()

    visits = []
    by_id = {}
    for row in rows:
        visit = by_id.get(row["id"])
        if visit is None:
            visit = {
                "id": row["id"],
                "visit_date": row["visit_date"],
                "rating": row["rating"],
                "notes": row["notes"],
                "bills": [],
            }
            by_id[row["id"]] = visit
            visits.append(visit)
        if row["bill_id"] is not None:
            visit["bills"].append({
                "id": row["bill_id"],
                "image_path": row["image_path"],
                "uploaded_at": row["uploaded_at"],
            })
    return visits


def get_visit(database_path, saved_restaurant_id, visit_id):
    """Find a visit only when it belongs to this saved restaurant."""
    with closing(connect_database(database_path)) as connection:
        return connection.execute(
            "SELECT id FROM visits WHERE id = ? AND saved_restaurant_id = ?",
            (visit_id, saved_restaurant_id),
        ).fetchone()


def get_bill_path(database_path, saved_restaurant_id, visit_id, bill_id):
    """Find a bill only when its visit belongs to this saved restaurant."""
    with closing(connect_database(database_path)) as connection:
        row = connection.execute(
            """
            SELECT b.image_path FROM bills AS b
            JOIN visits AS v ON v.id = b.visit_id
            WHERE b.id = ? AND v.id = ? AND v.saved_restaurant_id = ?
            """,
            (bill_id, visit_id, saved_restaurant_id),
        ).fetchone()
    return row[0] if row else None


def list_bill_paths(database_path, saved_restaurant_id):
    """List files attached to a saved restaurant before it is removed."""
    with closing(connect_database(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT b.image_path FROM bills AS b
            JOIN visits AS v ON v.id = b.visit_id
            WHERE v.saved_restaurant_id = ?
            """,
            (saved_restaurant_id,),
        ).fetchall()
    return [row[0] for row in rows]


def add_bill(database_path, visit_id, image_path):
    if not visit_id:
        raise ValueError("visit id is needed")

    if not image_path:
        raise ValueError("Image path is required.")

    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """INSERT INTO bills (visit_id, image_path)
            VALUES (?, ?)
            """,
            (visit_id, image_path),
        )
    return cursor.lastrowid
