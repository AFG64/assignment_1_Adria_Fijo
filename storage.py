"""SQLite connection and schema setup for the single-user app."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path


def database_path():
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    return data_dir / "devops_food.sqlite3"


def connect_database(path):
    """Open a connection with foreign-key checks enabled for this connection."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with closing(connect_database(path)) as connection:
        existing_restaurants = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'restaurants'"
        ).fetchone()
        if existing_restaurants:
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(restaurants)")
            }
            if "title" not in columns:
                raise RuntimeError(
                    "Existing database uses the earlier scaffold schema. "
                    "Use an empty DATA_DIR or migrate the existing database."
                )
        connection.executescript(schema)
