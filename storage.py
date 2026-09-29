"""SQLite path and initial schema shared by the two planned domains."""

import os
import sqlite3
from pathlib import Path


def database_path():
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    return data_dir / "devops_food.sqlite3"


def initialize_database(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                city TEXT NOT NULL,
                price_level INTEGER NOT NULL CHECK (price_level BETWEEN 1 AND 4),
                saved_status TEXT NOT NULL CHECK (saved_status IN ('want', 'visited')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY,
                restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
                visit_date TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                notes TEXT NOT NULL DEFAULT '',
                would_return INTEGER NOT NULL CHECK (would_return IN (0, 1)),
                bill_filename TEXT,
                bill_mime TEXT,
                bill_data BLOB,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ordered_items (
                id INTEGER PRIMARY KEY,
                visit_id INTEGER NOT NULL REFERENCES visits(id),
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0)
            );
            """
        )
