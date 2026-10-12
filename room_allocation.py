
"""Room Allocation domain: rooms, assignments and roommate preferences.

Facade: create_room, assign_student, remove_assignment,
add_roommate_preference, get_rooms and check_room_on_trip are this
domain's public interface, and would be the endpoints of the Room
Allocation service in Assignment 2.
"""

import sqlite3

from db import get_connection
from trip_management import on_registration_cancelled


# Adapter: the two functions below are the only code in Room Allocation that
# reads Trip Management's tables. They turn that data into the simple values
# this domain needs (does the trip exist, which trip and status does a
# registration have). Today they query the shared database; in Assignment 2
# only these two functions change, to ask the Trip Management service.

def _trip_exists(conn, trip_id):
    """Adapter: True if Trip Management has a trip with this ID."""
    row = conn.execute(
        "SELECT id FROM trips WHERE id = ?", (trip_id,)
    ).fetchone()
    return row is not None


def _get_registration(conn, registration_id):
    """Adapter: a registration as {"trip_id", "status"}, or None."""
    row = conn.execute(
        "SELECT trip_id, status FROM registrations WHERE id = ?",
        (registration_id,)
    ).fetchone()

    if row is None:
        return None
    return {"trip_id": row["trip_id"], "status": row["status"]}


def create_room(trip_id, name, capacity):
    """Create a room for an existing trip and return its ID."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Room name cannot be empty")

    if type(capacity) is not int or not 1 <= capacity <= 6:
        raise ValueError("Room capacity must be between 1 and 6")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        if not _trip_exists(conn, trip_id):
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

        student = _get_registration(conn, registration_id)

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

        student = _get_registration(conn, registration_id)
        preferred = _get_registration(conn, preferred_registration_id)

        if student is None or preferred is None:
            raise ValueError("Both registrations must exist")

        if student["status"] != "confirmed" or preferred["status"] != "confirmed":
            raise ValueError("Both students must be confirmed")

        if student["trip_id"] != preferred["trip_id"]:
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
        if not _trip_exists(conn, trip_id):
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


def check_room_on_trip(trip_id, room_id):
    """Raise ValueError unless the room belongs to this trip."""
    conn = get_connection()
    try:
        room = conn.execute(
            "SELECT trip_id FROM rooms WHERE id = ?", (room_id,)
        ).fetchone()

        if room is None or room["trip_id"] != trip_id:
            raise ValueError("Room not found on this trip")
    finally:
        conn.close()


def _release_student_on_cancel(conn, registration_id):
    """Observer: free a cancelled student's bed and drop their roommate
    preferences, inside the caller's transaction."""
    conn.execute(
        "DELETE FROM room_assignments WHERE registration_id = ?",
        (registration_id,)
    )

    # Remove requests made by the student and requests naming them, so no
    # one keeps asking to share with someone who is no longer coming.
    conn.execute(
        """
        DELETE FROM roommate_preferences
        WHERE registration_id = ? OR preferred_registration_id = ?
        """,
        (registration_id, registration_id)
    )


# Subscribe once, when this module is first imported.
on_registration_cancelled(_release_student_on_cancel)
