"""Small helpers for working with the SQLite database."""

import os
import sqlite3

from config import DATA_DIR, DB_PATH


def get_connection():
    """Open a connection to the database with foreign keys enforced."""
    conn = sqlite3.connect(DB_PATH)
    # Let rows be read by column name, e.g. row["name"].
    conn.row_factory = sqlite3.Row
    # SQLite ignores foreign keys unless this is turned on for each connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Make sure the data folder exists before the database is used."""
    os.makedirs(DATA_DIR, exist_ok=True)
