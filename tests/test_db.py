"""Tests for starting up against an existing database."""

import sqlite3

import db

# registrations as it was before the pending_payment status was added.
OLD_REGISTRATIONS = """
CREATE TABLE trips (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, destination TEXT NOT NULL,
    start_date TEXT NOT NULL, end_date TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);
CREATE TABLE registrations (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE,
    status TEXT NOT NULL
        CHECK (status IN ('confirmed', 'waitlisted', 'cancelled')),
    registered_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_registrations_active_email
    ON registrations (trip_id, email)
    WHERE status IN ('confirmed', 'waitlisted');
INSERT INTO trips VALUES (1, 'Andorra', 'Grandvalira', '2027-01-20', '2027-01-24', 10);
INSERT INTO registrations VALUES (1, 1, 'Sofia', 'sofia@example.com', 'confirmed', '2026-10-01');
"""


def test_init_db_twice_keeps_data(test_db):
    test_db.execute(
        "INSERT INTO trips (name, destination, start_date, end_date, capacity)"
        " VALUES ('Andorra', 'Grandvalira', '2027-01-20', '2027-01-24', 10)"
    )
    test_db.commit()

    db.init_db()

    assert test_db.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == 1


def test_init_db_upgrades_old_registrations_table(tmp_path, monkeypatch):
    db_path = tmp_path / "old.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))

    old = sqlite3.connect(db_path)
    old.executescript(OLD_REGISTRATIONS)
    old.close()

    db.init_db()

    conn = db.get_connection()
    try:
        # The old row survived the upgrade.
        row = conn.execute("SELECT name, status FROM registrations").fetchone()
        assert tuple(row) == ("Sofia", "confirmed")

        # The new status and column are accepted now.
        conn.execute(
            "INSERT INTO registrations"
            " (trip_id, name, email, status, registered_at, payment_deadline)"
            " VALUES (1, 'Emma', 'emma@example.com', 'pending_payment',"
            " '2026-10-11', '2026-10-13')"
        )

        # The new unique index covers pending_payment rows too.
        index_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'idx_registrations_active_email'"
        ).fetchone()["sql"]
        assert "pending_payment" in index_sql

        # The temporary copy is gone.
        leftover = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'registrations_old'"
        ).fetchone()[0]
        assert leftover == 0
    finally:
        conn.close()
