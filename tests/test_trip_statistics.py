import pytest

from trip_statistics import get_trip_statistics


def add_trip(conn, capacity):
    conn.execute(
        """
        INSERT INTO trips
        (id, name, destination, start_date, end_date, capacity)
        VALUES (1, 'Andorra', 'Andorra', '2027-01-20', '2027-01-24', ?)
        """,
        (capacity,)
    )


def add_student(conn, registration_id, name, status):
    conn.execute(
        """
        INSERT INTO registrations
        (id, trip_id, name, email, status, registered_at)
        VALUES (?, 1, ?, ?, ?, '2026-10-11T15:00:00')
        """,
        (registration_id, name, f"{name.lower()}@example.com", status)
    )


def assign_room(conn, registration_id):
    conn.execute(
        "INSERT INTO room_assignments (room_id, registration_id) VALUES (1, ?)",
        (registration_id,)
    )


def test_empty_trip_statistics(test_db):
    # Create a trip with 100 available places.
    add_trip(test_db, 100)
    test_db.commit()

    # Check that an empty trip shows the correct numbers.
    result = get_trip_statistics(1)

    assert result["capacity"] == 100
    assert result["confirmed"] == 0
    assert result["pending_payment"] == 0
    assert result["waitlisted"] == 0
    assert result["places_remaining"] == 100
    assert result["room_assigned"] == 0
    assert result["need_room"] == 0
    assert result["occupancy_percent"] == 0.0


def test_trip_statistics_with_students(test_db):
    # Create a trip with 5 places.
    add_trip(test_db, 5)

    # Register three confirmed students and one waitlisted student.
    add_student(test_db, 1, "Sofia", "confirmed")
    add_student(test_db, 2, "Emma", "confirmed")
    add_student(test_db, 3, "Lucas", "confirmed")
    add_student(test_db, 4, "Daniel", "waitlisted")

    # Create a room and assign Sofia and Emma.
    test_db.execute(
        "INSERT INTO rooms (id, trip_id, name, capacity) VALUES (1, 1, 'Room A', 4)"
    )
    assign_room(test_db, 1)
    assign_room(test_db, 2)
    test_db.commit()

    result = get_trip_statistics(1)

    assert result["capacity"] == 5
    assert result["confirmed"] == 3
    assert result["waitlisted"] == 1
    assert result["places_remaining"] == 2
    assert result["room_assigned"] == 2
    assert result["need_room"] == 1
    assert result["occupancy_percent"] == 60.0


def test_cancelled_and_waitlisted_students_with_rooms_are_not_counted(test_db):
    add_trip(test_db, 5)
    add_student(test_db, 1, "Sofia", "confirmed")
    add_student(test_db, 2, "Emma", "cancelled")
    add_student(test_db, 3, "Daniel", "waitlisted")

    # All three have a room, but only Sofia is confirmed.
    test_db.execute(
        "INSERT INTO rooms (id, trip_id, name, capacity) VALUES (1, 1, 'Room A', 4)"
    )
    assign_room(test_db, 1)
    assign_room(test_db, 2)
    assign_room(test_db, 3)
    test_db.commit()

    result = get_trip_statistics(1)

    assert result["confirmed"] == 1
    assert result["waitlisted"] == 1
    assert result["room_assigned"] == 1
    assert result["need_room"] == 0


def test_unpaid_reservations_still_take_places(test_db):
    add_trip(test_db, 4)
    add_student(test_db, 1, "Sofia", "confirmed")
    add_student(test_db, 2, "Emma", "pending_payment")
    add_student(test_db, 3, "Lucas", "pending_payment")
    test_db.commit()

    result = get_trip_statistics(1)

    assert result["confirmed"] == 1
    assert result["pending_payment"] == 2
    # Only one place is left, because unpaid reservations hold theirs.
    assert result["places_remaining"] == 1
    assert result["occupancy_percent"] == 75.0
    # Only paid students need a room yet.
    assert result["need_room"] == 1


def test_unknown_trip_raises_error(test_db):
    with pytest.raises(ValueError, match="Trip not found"):
        get_trip_statistics(999)
