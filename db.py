"""Small helpers for working with the SQLite database."""

import os
import sqlite3

from config import DATA_DIR, DB_PATH

# schema.sql sits next to this file, wherever the app is run from.
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_connection():
    """Open a connection to the database with foreign keys enforced."""
    conn = sqlite3.connect(DB_PATH)
    # Let rows be read by column name, e.g. row["name"].
    conn.row_factory = sqlite3.Row
    # SQLite ignores foreign keys unless this is turned on for each connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the data folder and any missing tables. Safe to run every boot."""
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(SCHEMA_PATH) as schema_file:
        schema = schema_file.read()

    conn = get_connection()
    try:
        conn.executescript(schema)
    finally:
        conn.close()
