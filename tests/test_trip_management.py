
"""Tests for creating ski trips."""

import sqlite3

import pytest

from trip_management import create_trip


def test_create_trip(test_db):
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
    trip = test_db.execute(
        """
        SELECT name, destination, capacity
        FROM trips
        WHERE id = ?
        """,
        (trip_id,)
    ).fetchone()

    assert trip == ("Andorra 2027", "Grandvalira", 100)


def test_create_trip_with_invalid_capacity(test_db):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "Grandvalira",
            "2027-01-20",
            "2027-01-24",
            0
        )


def test_create_trip_with_empty_name(test_db):
    with pytest.raises(ValueError):
        create_trip(
            "",
            "Grandvalira",
            "2027-01-20",
            "2027-01-24",
            100
        )


def test_create_trip_with_empty_destination(test_db):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "",
            "2027-01-20",
            "2027-01-24",
            100
        )


def test_create_trip_with_invalid_dates(test_db):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "Grandvalira",
            "2027-01-24",
            "2027-01-20",
            100
        )


def test_create_trip_with_invalid_date_format(test_db):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "Grandvalira",
            "not-a-date",
            "2027-01-24",
            100
        )


def test_create_trip_with_boolean_capacity(test_db):
    with pytest.raises(ValueError):
        create_trip(
            "Andorra",
            "Grandvalira",
            "2027-01-20",
            "2027-01-24",
            True
        )
