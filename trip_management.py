"""Functions for managing ski trips."""
import sqlite3
from datetime import date, datetime, timedelta, timezone

from db import get_connection



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
        # Start a transaction before checking capacity.
        conn.execute("BEGIN IMMEDIATE")

        trip = conn.execute(
            "SELECT capacity FROM trips WHERE id = ?",
            (trip_id,)
        ).fetchone()

        if trip is None:
            raise ValueError("Trip not found")

        occupied = conn.execute(
            """
            SELECT COUNT(*)
            FROM registrations
            WHERE trip_id = ?
              AND status IN ('pending_payment', 'confirmed')
            """,
            (trip_id,)
        ).fetchone()[0]

        waiting = conn.execute(
            """
            SELECT COUNT(*)
            FROM registrations
            WHERE trip_id = ? AND status = 'waitlisted'
            """,
            (trip_id,)
        ).fetchone()[0]

        now = datetime.now(timezone.utc)
        registered_at = now.isoformat()

        if occupied < trip["capacity"] and waiting == 0:
            status = "pending_payment"
            payment_deadline = (
                now + timedelta(hours=48)
            ).isoformat()
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
                registered_at,
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
