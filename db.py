"""Database location and connection handling."""

import sqlite3
from pathlib import Path

# Resolved from this file, so it's possible to run the app from any working
# directory.
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "flight_management.db"


def connect(db_path=DEFAULT_DB_PATH):
    """Open a connection to the database."""
    conn = sqlite3.connect(db_path)
    # SQLite only enforces foreign keys when this is switched on.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
