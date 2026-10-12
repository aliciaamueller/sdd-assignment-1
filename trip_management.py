"""Functions for managing ski trips."""
import sqlite3
from datetime import date, datetime, timedelta, timezone

from db import get_connection

# How long a student has to pay before their reserved place is released.
PAYMENT_WINDOW = timedelta(hours=48)


def _now():
    """Current UTC time. Tests replace this to move the clock forward."""
    return datetime.now(timezone.utc)


def create_trip(name, destination, start_date, end_date, capacity):
    """Create a new ski trip and return its ID."""

    # Check that the trip has a name and destination.
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Trip name cannot be empty")

    if not isinstance(destination, str) or not destination.strip():
        raise ValueError("Destination cannot be empty")

    # Make sure the dates are valid and in the correct order.
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except (ValueError, TypeError):
        raise ValueError("Dates must use YYYY-MM-DD format")

    if end < start:
        raise ValueError("End date cannot be before start date")

    # Capacity must be a positive whole number.
    if type(capacity) is not int or capacity <= 0:
        raise ValueError("Capacity must be a positive integer")

    # Save the trip in the database.
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO trips
            (name, destination, start_date, end_date, capacity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                destination.strip(),
                start.isoformat(),
                end.isoformat(),
                capacity
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def _promote_waitlist(conn, trip_id, now):
    """Give free places to the longest-waiting students, oldest first."""

    capacity = conn.execute(
        "SELECT capacity FROM trips WHERE id = ?",
        (trip_id,)
    ).fetchone()["capacity"]

    occupied = conn.execute(
        """
        SELECT COUNT(*)
        FROM registrations
        WHERE trip_id = ?
          AND status IN ('pending_payment', 'confirmed')
        """,
        (trip_id,)
    ).fetchone()[0]

    free_places = capacity - occupied
    if free_places <= 0:
        return

    # id breaks ties if two students registered at the same moment.
    next_in_line = conn.execute(
        """
        SELECT id
        FROM registrations
        WHERE trip_id = ? AND status = 'waitlisted'
        ORDER BY registered_at, id
        LIMIT ?
        """,
        (trip_id, free_places)
    ).fetchall()

    # A promoted student gets a fresh payment window starting now.
    deadline = (now + PAYMENT_WINDOW).isoformat()
    for row in next_in_line:
        conn.execute(
            """
            UPDATE registrations
            SET status = 'pending_payment', payment_deadline = ?
            WHERE id = ?
            """,
            (deadline, row["id"])
        )


def _release_expired(conn, trip_id, now):
    """Cancel unpaid reservations past their deadline, then refill places.

    There is no background job (one process only), so this runs at the
    start of every registration change instead.
    """

    conn.execute(
        """
        UPDATE registrations
        SET status = 'cancelled'
        WHERE trip_id = ?
          AND status = 'pending_payment'
          AND payment_deadline < ?
        """,
        (trip_id, now.isoformat())
    )

    _promote_waitlist(conn, trip_id, now)


def register_student(trip_id, name, email):
    """Register a student or add them to the waiting list."""

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Student name cannot be empty")

    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email cannot be empty")

    name = name.strip()
    email = email.strip().lower()

    conn = get_connection()

    try:
        # Lock the database before checking capacity, so two students
        # cannot both take the last place.
        conn.execute("BEGIN IMMEDIATE")

        trip = conn.execute(
            "SELECT capacity FROM trips WHERE id = ?",
            (trip_id,)
        ).fetchone()

        if trip is None:
            raise ValueError("Trip not found")

        now = _now()
        _release_expired(conn, trip_id, now)

        occupied = conn.execute(
            """
            SELECT COUNT(*)
            FROM registrations
            WHERE trip_id = ?
              AND status IN ('pending_payment', 'confirmed')
            """,
            (trip_id,)
        ).fetchone()[0]

        # _release_expired has just filled any free places from the
        # waitlist, so a free place here means nobody is waiting for it.
        if occupied < trip["capacity"]:
            status = "pending_payment"
            payment_deadline = (now + PAYMENT_WINDOW).isoformat()
        else:
            status = "waitlisted"
            payment_deadline = None

        cursor = conn.execute(
            """
            INSERT INTO registrations
            (trip_id, name, email, status, registered_at, payment_deadline)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                trip_id,
                name,
                email,
                status,
                now.isoformat(),
                payment_deadline
            )
        )

        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise ValueError("Student already registered for this trip") from error

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def confirm_payment(registration_id):
    """Mark a reserved place as paid, if the deadline has not passed."""

    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        registration = conn.execute(
            "SELECT trip_id FROM registrations WHERE id = ?",
            (registration_id,)
        ).fetchone()

        if registration is None:
            raise ValueError("Registration not found")

        # Expire first, so a late payment finds its place already released.
        _release_expired(conn, registration["trip_id"], _now())

        status = conn.execute(
            "SELECT status FROM registrations WHERE id = ?",
            (registration_id,)
        ).fetchone()["status"]

        if status != "pending_payment":
            # Keep any expiries above even though this payment is refused.
            conn.commit()
            raise ValueError("Registration is not awaiting payment")

        conn.execute(
            """
            UPDATE registrations
            SET status = 'confirmed'
            WHERE id = ?
            """,
            (registration_id,)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def cancel_registration(registration_id):
    """Cancel a registration, free its room and update the waiting list."""

    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        registration = conn.execute(
            "SELECT trip_id, status FROM registrations WHERE id = ?",
            (registration_id,)
        ).fetchone()

        if registration is None:
            raise ValueError("Registration not found")

        if registration["status"] == "cancelled":
            raise ValueError("Registration is already cancelled")

        # Keep the registration row so its history stays visible.
        conn.execute(
            "UPDATE registrations SET status = 'cancelled' WHERE id = ?",
            (registration_id,)
        )

        # Free the student's bed if they were assigned to a room.
        conn.execute(
            "DELETE FROM room_assignments WHERE registration_id = ?",
            (registration_id,)
        )

        # Release expired reservations and offer available places
        # to students on the waiting list, in FIFO order.
        _release_expired(conn, registration["trip_id"], _now())

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def check_registration_on_trip(trip_id, registration_id):
    """Raise ValueError unless the registration belongs to this trip."""

    conn = get_connection()

    try:
        registration = conn.execute(
            "SELECT trip_id FROM registrations WHERE id = ?",
            (registration_id,)
        ).fetchone()

        if registration is None or registration["trip_id"] != trip_id:
            raise ValueError("Registration not found on this trip")

    finally:
        conn.close()
