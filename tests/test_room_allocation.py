
"""Tests for the Room Allocation domain."""

import pytest

from trip_management import create_trip, register_student, cancel_registration
from room_allocation import (
    create_room,
    assign_student,
    remove_assignment,
    add_roommate_preference,
    get_rooms,
)


def make_trip():
    return create_trip(
        "Andorra 2027", "Grandvalira",
        "2027-01-20", "2027-01-24", 10
    )


def make_confirmed_student(test_db, trip_id, name, email):
    registration_id = register_student(trip_id, name, email)

    # Simulate a completed payment for Room Allocation tests.
    test_db.execute(
        """
        UPDATE registrations
        SET status = 'confirmed', payment_deadline = NULL
        WHERE id = ?
        """,
        (registration_id,)
    )
    test_db.commit()

    return registration_id


def test_create_room(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 4)

    assert room_id == 1
    assert get_rooms(trip_id) == [
        {"id": 1, "name": "Room 101", "capacity": 4, "occupied": 0}
    ]


def test_reject_invalid_room_capacity(test_db):
    trip_id = make_trip()

    with pytest.raises(ValueError):
        create_room(trip_id, "Too large", 7)

    with pytest.raises(ValueError):
        create_room(trip_id, "Too small", 0)


def test_reject_unknown_trip(test_db):
    with pytest.raises(ValueError, match="Trip not found"):
        create_room(999, "Room 101", 4)


def test_reject_duplicate_room_name(test_db):
    trip_id = make_trip()
    create_room(trip_id, "Room 101", 4)

    with pytest.raises(ValueError):
        create_room(trip_id, "Room 101", 4)


def test_assign_confirmed_student(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 2)
    student_id = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )

    assignment_id = assign_student(room_id, student_id)

    assert assignment_id == 1
    assert get_rooms(trip_id)[0]["occupied"] == 1


def test_reject_unpaid_student(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 2)
    student_id = register_student(
        trip_id, "Sofia", "sofia@example.com"
    )

    with pytest.raises(ValueError, match="confirmed"):
        assign_student(room_id, student_id)


def test_reject_full_room(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 1)
    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )
    emma = make_confirmed_student(
        test_db, trip_id, "Emma", "emma@example.com"
    )

    assign_student(room_id, sofia)

    with pytest.raises(ValueError, match="full"):
        assign_student(room_id, emma)


def test_reject_double_assignment(test_db):
    trip_id = make_trip()
    room_one = create_room(trip_id, "Room 101", 2)
    room_two = create_room(trip_id, "Room 102", 2)
    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )

    assign_student(room_one, sofia)

    with pytest.raises(ValueError, match="already has a room"):
        assign_student(room_two, sofia)


def test_reject_different_trip(test_db):
    first_trip = make_trip()
    second_trip = create_trip(
        "Sierra Nevada", "Granada",
        "2027-02-06", "2027-02-09", 10
    )
    room_id = create_room(first_trip, "Room 101", 2)
    student_id = make_confirmed_student(
        test_db, second_trip, "Emma", "emma@example.com"
    )

    with pytest.raises(ValueError, match="different trips"):
        assign_student(room_id, student_id)


def test_remove_assignment_frees_bed(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 1)
    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )

    assign_student(room_id, sofia)

    assert remove_assignment(sofia) is True
    assert get_rooms(trip_id)[0]["occupied"] == 0
    assert remove_assignment(sofia) is False


def test_add_roommate_preference(test_db):
    trip_id = make_trip()
    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )
    emma = make_confirmed_student(
        test_db, trip_id, "Emma", "emma@example.com"
    )

    preference_id = add_roommate_preference(sofia, emma)

    assert preference_id == 1


def test_reject_self_preference(test_db):
    trip_id = make_trip()
    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )

    with pytest.raises(ValueError):
        add_roommate_preference(sofia, sofia)


def test_reject_duplicate_preference(test_db):
    trip_id = make_trip()
    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )
    emma = make_confirmed_student(
        test_db, trip_id, "Emma", "emma@example.com"
    )

    add_roommate_preference(sofia, emma)

    with pytest.raises(ValueError):
        add_roommate_preference(sofia, emma)


def test_cancellation_releases_room(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 2)

    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )

    assign_student(room_id, sofia)

    # Before cancellation, one bed is occupied.
    assert get_rooms(trip_id)[0]["occupied"] == 1

    # Cancelling the trip registration should free the bed.
    cancel_registration(sofia)

    assert get_rooms(trip_id)[0]["occupied"] == 0

    registration = test_db.execute(
        "SELECT status FROM registrations WHERE id = ?",
        (sofia,)
    ).fetchone()

    assert registration["status"] == "cancelled"


def test_cancellation_frees_room_and_promotes_waitlist(test_db):
    trip_id = create_trip(
        "Andorra", "Grandvalira",
        "2027-01-20", "2027-01-24", 1
    )
    room_id = create_room(trip_id, "Room 101", 1)

    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )

    # The trip is full, so Emma joins the waiting list.
    emma = register_student(trip_id, "Emma", "emma@example.com")

    assign_student(room_id, sofia)
    assert get_rooms(trip_id)[0]["occupied"] == 1

    cancel_registration(sofia)

    # Sofia's bed should be available again.
    assert get_rooms(trip_id)[0]["occupied"] == 0

    # Emma should receive the newly available place,
    # pending her payment.
    status = test_db.execute(
        "SELECT status FROM registrations WHERE id = ?",
        (emma,)
    ).fetchone()["status"]

    assert status == "pending_payment"


def test_reject_roommate_from_another_trip(test_db):
    first_trip = make_trip()
    second_trip = create_trip(
        "Sierra Nevada", "Granada",
        "2027-02-06", "2027-02-09", 10
    )

    sofia = make_confirmed_student(
        test_db, first_trip, "Sofia", "sofia@example.com"
    )
    emma = make_confirmed_student(
        test_db, second_trip, "Emma", "emma@example.com"
    )

    with pytest.raises(ValueError, match="same trip"):
        add_roommate_preference(sofia, emma)


def test_reject_unpaid_roommate_preference(test_db):
    trip_id = make_trip()

    sofia = make_confirmed_student(
        test_db, trip_id, "Sofia", "sofia@example.com"
    )
    emma = register_student(
        trip_id, "Emma", "emma@example.com"
    )

    with pytest.raises(ValueError, match="confirmed"):
        add_roommate_preference(sofia, emma)


def test_reject_empty_room_name(test_db):
    trip_id = make_trip()

    with pytest.raises(ValueError):
        create_room(trip_id, "   ", 4)


def test_reject_unknown_room_or_registration(test_db):
    trip_id = make_trip()
    room_id = create_room(trip_id, "Room 101", 4)
    student = make_confirmed_student(test_db, trip_id, "Ana", "ana@ie.edu")

    with pytest.raises(ValueError, match="Room not found"):
        assign_student(999, student)

    with pytest.raises(ValueError, match="Registration not found"):
        assign_student(room_id, 999)


def test_reject_preference_for_unknown_student(test_db):
    trip_id = make_trip()
    student = make_confirmed_student(test_db, trip_id, "Ana", "ana@ie.edu")

    with pytest.raises(ValueError, match="Both registrations must exist"):
        add_roommate_preference(student, 999)


def test_get_rooms_for_unknown_trip(test_db):
    with pytest.raises(ValueError, match="Trip not found"):
        get_rooms(999)
