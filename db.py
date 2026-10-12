"""Small helpers for working with the SQLite database."""

import os
import sqlite3

from config import DATA_DIR, DB_PATH

# schema.sql sits next to this file, wherever the app is run from.
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_connection():
    """Open a connection to the database with foreign keys enforced.

    Simple factory: every module gets its connection here, so every
    connection is set up the same way (named columns, foreign keys on).
    """
    conn = sqlite3.connect(DB_PATH)
    # Let rows be read by column name, e.g. row["name"].
    conn.row_factory = sqlite3.Row
    # SQLite ignores foreign keys unless this is turned on for each connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _needs_payment_upgrade(conn):
    """True if registrations was created before the pending_payment status.

    CREATE TABLE IF NOT EXISTS skips a table that already exists, so an
    older database would keep the old CHECK and reject every new
    registration.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'registrations'"
    ).fetchone()
    return row is not None and "pending_payment" not in row["sql"]


def init_db():
    """Create the data folder and any missing tables. Safe to run every boot."""
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(SCHEMA_PATH) as schema_file:
        schema = schema_file.read()

    conn = get_connection()
    try:
        if _needs_payment_upgrade(conn):
            # SQLite cannot change a CHECK in place, so move the old table
            # aside, let schema.sql create the new one, copy every row
            # across and only then drop the old copy. One transaction, so
            # a crash halfway leaves the old table untouched.
            conn.executescript(
                "BEGIN;"
                "ALTER TABLE registrations RENAME TO registrations_old;"
                "DROP INDEX IF EXISTS idx_registrations_active_email;"
                + schema +
                "INSERT INTO registrations"
                " (id, trip_id, name, email, status, registered_at)"
                " SELECT id, trip_id, name, email, status, registered_at"
                " FROM registrations_old;"
                "DROP TABLE registrations_old;"
                "COMMIT;"
            )
        else:
            conn.executescript(schema)
    finally:
        conn.close()
