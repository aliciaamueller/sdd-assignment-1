
"""Tests for creating ski trips."""

import sqlite3

import pytest

from trip_management import create_trip, register_student


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

    assert tuple(trip) == ("Andorra 2027", "Grandvalira", 100)


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


def test_registration_reserves_place_until_payment(test_db):
    trip_id = create_trip(
        "Andorra 2027",
        "Grandvalira",
        "2027-01-20",
        "2027-01-24",
        2
    )

    registration_id = register_student(
        trip_id,
        "Sofia",
        "SOFIA@example.com"
    )

    registration = test_db.execute(
        """
        SELECT status, email, payment_deadline
        FROM registrations
        WHERE id = ?
        """,
        (registration_id,)
    ).fetchone()

    assert registration["status"] == "pending_payment"
    assert registration["email"] == "sofia@example.com"
    assert registration["payment_deadline"] is not None


def test_registration_joins_waitlist_when_full(test_db):
    trip_id = create_trip(
        "Andorra 2027",
        "Grandvalira",
        "2027-01-20",
        "2027-01-24",
        1
    )

    register_student(trip_id, "Sofia", "sofia@example.com")
    second_id = register_student(
        trip_id,
        "Emma",
        "emma@example.com"
    )

    registration = test_db.execute(
        """
        SELECT status, payment_deadline
        FROM registrations
        WHERE id = ?
        """,
        (second_id,)
    ).fetchone()

    assert registration["status"] == "waitlisted"
    assert registration["payment_deadline"] is None


def test_registration_rejects_duplicate_email(test_db):
    trip_id = create_trip(
        "Andorra", "Grandvalira",
        "2027-01-20", "2027-01-24", 10
    )

    register_student(trip_id, "Sofia", "sofia@example.com")

    with pytest.raises(ValueError):
        register_student(trip_id, "Sofia", "SOFIA@example.com")


def test_registration_rejects_unknown_trip(test_db):
    with pytest.raises(ValueError, match="Trip not found"):
        register_student(999, "Sofia", "sofia@example.com")


def test_registration_rejects_empty_name(test_db):
    trip_id = create_trip(
        "Andorra", "Grandvalira",
        "2027-01-20", "2027-01-24", 10
    )

    with pytest.raises(ValueError):
        register_student(trip_id, "", "sofia@example.com")


def test_registration_rejects_empty_email(test_db):
    trip_id = create_trip(
        "Andorra", "Grandvalira",
        "2027-01-20", "2027-01-24", 10
    )

    with pytest.raises(ValueError):
        register_student(trip_id, "Sofia", "")
