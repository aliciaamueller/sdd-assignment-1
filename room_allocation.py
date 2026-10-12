
"""Room Allocation domain: rooms, assignments and roommate preferences."""

import sqlite3

from db import get_connection


def create_room(trip_id, name, capacity):
    """Create a room for an existing trip and return its ID."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Room name cannot be empty")

    if type(capacity) is not int or not 1 <= capacity <= 6:
        raise ValueError("Room capacity must be between 1 and 6")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        trip = conn.execute(
            "SELECT id FROM trips WHERE id = ?", (trip_id,)
        ).fetchone()

        if trip is None:
            raise ValueError("Trip not found")

        cursor = conn.execute(
            "INSERT INTO rooms (trip_id, name, capacity) VALUES (?, ?, ?)",
            (trip_id, name.strip(), capacity)
        )
        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise ValueError("A room with this name already exists") from error
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def assign_student(room_id, registration_id):
    """Assign a confirmed student to a room on the same trip."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        room = conn.execute(
            "SELECT trip_id, capacity FROM rooms WHERE id = ?",
            (room_id,)
        ).fetchone()

        if room is None:
            raise ValueError("Room not found")

        student = conn.execute(
            "SELECT trip_id, status FROM registrations WHERE id = ?",
            (registration_id,)
        ).fetchone()

        if student is None:
            raise ValueError("Registration not found")

        if student["status"] != "confirmed":
            raise ValueError("Only confirmed students can receive rooms")

        if student["trip_id"] != room["trip_id"]:
            raise ValueError("Student and room belong to different trips")

        occupied = conn.execute(
            "SELECT COUNT(*) FROM room_assignments WHERE room_id = ?",
            (room_id,)
        ).fetchone()[0]

        if occupied >= room["capacity"]:
            raise ValueError("Room is full")

        cursor = conn.execute(
            """
            INSERT INTO room_assignments (room_id, registration_id)
            VALUES (?, ?)
            """,
            (room_id, registration_id)
        )

        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise ValueError("Student already has a room") from error
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def remove_assignment(registration_id):
    """Remove a student's room assignment, if one exists."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM room_assignments WHERE registration_id = ?",
            (registration_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def add_roommate_preference(registration_id, preferred_registration_id):
    """Record that one confirmed student wants to share with another."""
    if registration_id == preferred_registration_id:
        raise ValueError("A student cannot request themselves")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        students = conn.execute(
            """
            SELECT id, trip_id, status
            FROM registrations
            WHERE id IN (?, ?)
            """,
            (registration_id, preferred_registration_id)
        ).fetchall()

        if len(students) != 2:
            raise ValueError("Both registrations must exist")

        if any(student["status"] != "confirmed" for student in students):
            raise ValueError("Both students must be confirmed")

        if students[0]["trip_id"] != students[1]["trip_id"]:
            raise ValueError("Students must be on the same trip")

        cursor = conn.execute(
            """
            INSERT INTO roommate_preferences
                (registration_id, preferred_registration_id)
            VALUES (?, ?)
            """,
            (registration_id, preferred_registration_id)
        )
        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise ValueError("Roommate preference already exists") from error
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_rooms(trip_id):
    """Return rooms for a trip with their current occupancy."""
    conn = get_connection()
    try:
        trip = conn.execute(
            "SELECT id FROM trips WHERE id = ?", (trip_id,)
        ).fetchone()

        if trip is None:
            raise ValueError("Trip not found")

        rows = conn.execute(
            """
            SELECT rooms.id, rooms.name, rooms.capacity,
                   COUNT(room_assignments.id) AS occupied
            FROM rooms
            LEFT JOIN room_assignments
                ON room_assignments.room_id = rooms.id
            WHERE rooms.trip_id = ?
            GROUP BY rooms.id
            ORDER BY rooms.id
            """,
            (trip_id,)
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()
