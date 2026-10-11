
"""Tests for creating ski trips."""

import sqlite3

import pytest

import db
from trip_management import create_trip


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    """Create a fresh temporary database for each test."""

    db_path = tmp_path / "test.db"

    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))

    db.init_db()

    return db_path


def test_create_trip(test_database):
    trip_id = create_trip(
        "Andorra 2027",
        "Grandvalira",
        "2027-01-20",
        "2027-01-24",
        100
    )

    # The first trip should receive ID 1.
    assert trip_id == 1

    # Check that the correct information was saved.
    conn = sqlite3.connect(test_database)

    trip = conn.execute(
        "SELECT name, destination, capacity FROM trips WHERE id = ?",
        (trip_id,)
    ).fetchone()

    conn.close()

    assert trip == ("Andorra 2027", "Grandvalira", 100)


def test_create_trip_with_invalid_capacity(test_database):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "Grandvalira",
            "2027-01-20",
            "2027-01-24",
            0
        )


def test_create_trip_with_empty_name(test_database):
    with pytest.raises(ValueError):
        create_trip(
            "",
            "Grandvalira",
            "2027-01-20",
            "2027-01-24",
            100
        )


def test_create_trip_with_invalid_dates(test_database):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "Grandvalira",
            "2027-01-24",
            "2027-01-20",
            100
        )
