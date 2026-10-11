"""Statistics for the Ski Club dashboard."""

from db import get_connection


def get_trip_statistics(trip_id):
    """Calculate registration and room statistics for one trip.

    Read-only: an unpaid reservation past its deadline is still counted
    until the next registration change for the trip releases it.
    """
    conn = get_connection()

    try:
        trip = conn.execute(
            "SELECT capacity FROM trips WHERE id = ?",
            (trip_id,)
        ).fetchone()

        if trip is None:
            raise ValueError("Trip not found")

        confirmed = conn.execute(
            """
            SELECT COUNT(*) FROM registrations
            WHERE trip_id = ? AND status = 'confirmed'
            """,
            (trip_id,)
        ).fetchone()[0]

        # Reserved but not yet paid. These still hold a place on the trip.
        pending = conn.execute(
            """
            SELECT COUNT(*) FROM registrations
            WHERE trip_id = ? AND status = 'pending_payment'
            """,
            (trip_id,)
        ).fetchone()[0]

        waitlisted = conn.execute(
            """
            SELECT COUNT(*) FROM registrations
            WHERE trip_id = ? AND status = 'waitlisted'
            """,
            (trip_id,)
        ).fetchone()[0]

        assigned = conn.execute(
            """
            SELECT COUNT(*)
            FROM room_assignments AS a
            JOIN registrations AS r ON a.registration_id = r.id
            JOIN rooms AS room ON a.room_id = room.id
            WHERE r.trip_id = ?
              AND room.trip_id = ?
              AND r.status = 'confirmed'
            """,
            (trip_id, trip_id)
        ).fetchone()[0]

        capacity = trip["capacity"]
        taken = confirmed + pending

        return {
            "capacity": capacity,
            "confirmed": confirmed,
            "pending_payment": pending,
            "waitlisted": waitlisted,
            "places_remaining": max(0, capacity - taken),
            "room_assigned": assigned,
            "need_room": max(0, confirmed - assigned),
            "occupancy_percent": round(taken / capacity * 100, 1)
        }

    finally:
        conn.close()
