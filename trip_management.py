
"""Functions for managing ski trips."""

from datetime import date

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
