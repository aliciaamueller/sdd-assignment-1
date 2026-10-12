"""Tests for trips, registrations, payments and the waiting list."""

from datetime import datetime, timedelta, timezone

import pytest

import trip_management
from trip_management import (
    cancel_registration,
    confirm_payment,
    create_trip,
    register_student,
)


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


def make_trip(capacity):
    return create_trip(
        "Andorra", "Grandvalira",
        "2027-01-20", "2027-01-24", capacity
    )


def get_status(conn, registration_id):
    return conn.execute(
        "SELECT status FROM registrations WHERE id = ?",
        (registration_id,)
    ).fetchone()["status"]


def move_clock(monkeypatch, hours):
    """Pretend the given number of hours have passed."""
    later = datetime.now(timezone.utc) + timedelta(hours=hours)
    monkeypatch.setattr(trip_management, "_now", lambda: later)


def test_confirm_payment(test_db):
    trip_id = make_trip(2)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")

    confirm_payment(sofia)

    assert get_status(test_db, sofia) == "confirmed"


def test_confirm_payment_rejects_waitlisted(test_db):
    trip_id = make_trip(1)
    register_student(trip_id, "Sofia", "sofia@example.com")
    emma = register_student(trip_id, "Emma", "emma@example.com")

    with pytest.raises(ValueError, match="not awaiting payment"):
        confirm_payment(emma)


def test_confirm_payment_rejects_unknown_registration(test_db):
    with pytest.raises(ValueError, match="Registration not found"):
        confirm_payment(999)


def test_late_payment_is_refused_and_place_goes_to_waitlist(test_db, monkeypatch):
    trip_id = make_trip(1)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")
    emma = register_student(trip_id, "Emma", "emma@example.com")

    move_clock(monkeypatch, 49)

    with pytest.raises(ValueError, match="not awaiting payment"):
        confirm_payment(sofia)

    # The refusal still saves the expiry and Emma's promotion.
    assert get_status(test_db, sofia) == "cancelled"
    assert get_status(test_db, emma) == "pending_payment"


def test_payment_inside_deadline_is_accepted(test_db, monkeypatch):
    trip_id = make_trip(1)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")

    move_clock(monkeypatch, 47)
    confirm_payment(sofia)

    assert get_status(test_db, sofia) == "confirmed"


def test_expired_reservation_frees_place_for_new_student(test_db, monkeypatch):
    trip_id = make_trip(1)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")

    move_clock(monkeypatch, 49)
    emma = register_student(trip_id, "Emma", "emma@example.com")

    assert get_status(test_db, sofia) == "cancelled"
    assert get_status(test_db, emma) == "pending_payment"


def test_cancel_promotes_first_waitlisted_student(test_db):
    trip_id = make_trip(1)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")
    emma = register_student(trip_id, "Emma", "emma@example.com")
    lucas = register_student(trip_id, "Lucas", "lucas@example.com")

    cancel_registration(sofia)

    assert get_status(test_db, sofia) == "cancelled"
    assert get_status(test_db, emma) == "pending_payment"
    assert get_status(test_db, lucas) == "waitlisted"

    # The promoted student gets their own payment deadline.
    deadline = test_db.execute(
        "SELECT payment_deadline FROM registrations WHERE id = ?",
        (emma,)
    ).fetchone()["payment_deadline"]
    assert deadline is not None


def test_cancel_waitlisted_student_does_not_promote_anyone(test_db):
    trip_id = make_trip(1)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")
    emma = register_student(trip_id, "Emma", "emma@example.com")

    cancel_registration(emma)

    assert get_status(test_db, sofia) == "pending_payment"
    assert get_status(test_db, emma) == "cancelled"


def test_cancel_rejects_already_cancelled(test_db):
    trip_id = make_trip(1)
    sofia = register_student(trip_id, "Sofia", "sofia@example.com")
    cancel_registration(sofia)

    with pytest.raises(ValueError, match="already cancelled"):
        cancel_registration(sofia)


def test_cancel_rejects_unknown_registration(test_db):
    with pytest.raises(ValueError, match="Registration not found"):
        cancel_registration(999)


def test_cancelled_student_can_register_again(test_db):
    trip_id = make_trip(2)
    first = register_student(trip_id, "Sofia", "sofia@example.com")
    cancel_registration(first)

    second = register_student(trip_id, "Sofia", "sofia@example.com")

    assert second != first
    assert get_status(test_db, second) == "pending_payment"
