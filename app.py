
"""Flask web interface for Ski Club Manager."""

from datetime import date

from flask import Flask, flash, redirect, render_template, request, url_for

from config import PORT, SECRET_KEY
from db import get_connection, init_db
from room_allocation import (
    add_roommate_preference,
    assign_student,
    check_room_on_trip,
    create_room,
    get_rooms,
)
from trip_management import (
    cancel_registration,
    check_registration_on_trip,
    confirm_payment,
    create_trip,
    register_student,
)
from trip_statistics import get_trip_statistics


app = Flask(__name__)
app.secret_key = SECRET_KEY

# Prepare the database when the application starts.
init_db()


def get_trips():
    """Return all trips, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM trips ORDER BY start_date, id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_trip_details(trip_id):
    """Load a trip, its registrations and room assignments."""
    conn = get_connection()
    try:
        trip = conn.execute(
            "SELECT * FROM trips WHERE id = ?",
            (trip_id,)
        ).fetchone()

        if trip is None:
            return None, [], []

        registrations = conn.execute(
            """
            SELECT r.*, rooms.name AS room_name
            FROM registrations AS r
            LEFT JOIN room_assignments AS a
                ON a.registration_id = r.id
            LEFT JOIN rooms
                ON rooms.id = a.room_id
            WHERE r.trip_id = ?
            ORDER BY r.registered_at, r.id
            """,
            (trip_id,)
        ).fetchall()

        preferences = conn.execute(
            """
            SELECT p.registration_id,
                   r1.name AS student_name,
                   r2.name AS preferred_name
            FROM roommate_preferences AS p
            JOIN registrations AS r1
                ON r1.id = p.registration_id
            JOIN registrations AS r2
                ON r2.id = p.preferred_registration_id
            WHERE r1.trip_id = ?
            ORDER BY p.id
            """,
            (trip_id,)
        ).fetchall()

        return (
            dict(trip),
            [dict(row) for row in registrations],
            [dict(row) for row in preferences],
        )
    finally:
        conn.close()


def format_dates(start_date, end_date):
    """Turn two ISO dates into a short range, e.g. 10–15 Jan 2027."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    end_text = f"{end.day} {end.strftime('%b')} {end.year}"

    # Only repeat the month and year when they change.
    if start == end:
        return end_text
    if start.year != end.year:
        start_text = f"{start.day} {start.strftime('%b')} {start.year}"
    elif start.month != end.month:
        start_text = f"{start.day} {start.strftime('%b')}"
    else:
        start_text = f"{start.day}"

    return f"{start_text} – {end_text}"


def form_int(field, message):
    """Read a whole number from the submitted form, or fail with a clear message."""
    try:
        return int(request.form.get(field, ""))
    except ValueError:
        raise ValueError(message)


def handle_action(action, success_message):
    """Run a form action and show a helpful message.

    Command-style: each route wraps its work in an action() function and
    passes it here, so error handling and flash messages live in one place
    instead of being repeated in every route.
    """
    try:
        action()
        flash(success_message, "success")
    except (ValueError, TypeError) as error:
        flash(str(error), "error")


@app.route("/")
def index():
    """Show all trips and their dashboard statistics."""
    trips = get_trips()

    for trip in trips:
        trip["stats"] = get_trip_statistics(trip["id"])
        trip["dates"] = format_dates(trip["start_date"], trip["end_date"])

    return render_template("index.html", trips=trips)


@app.route("/trips/create", methods=["POST"])
def create_trip_route():
    """Create a trip from the dashboard form."""
    def action():
        create_trip(
            request.form.get("name", ""),
            request.form.get("destination", ""),
            request.form.get("start_date", ""),
            request.form.get("end_date", ""),
            form_int("capacity", "Capacity must be a positive integer")
        )

    handle_action(action, "Trip created successfully.")
    return redirect(url_for("index"))


@app.route("/trips/<int:trip_id>")
def trip_page(trip_id):
    """Show one trip's registrations, rooms and preferences."""
    trip, registrations, preferences = get_trip_details(trip_id)

    if trip is None:
        return "Trip not found", 404

    trip["dates"] = format_dates(trip["start_date"], trip["end_date"])

    stats = get_trip_statistics(trip_id)
    rooms = get_rooms(trip_id)

    confirmed_students = [
        student for student in registrations
        if student["status"] == "confirmed"
    ]

    unassigned_students = [
        student for student in confirmed_students
        if student["room_name"] is None
    ]

    return render_template(
        "trip.html",
        trip=trip,
        stats=stats,
        registrations=registrations,
        preferences=preferences,
        rooms=rooms,
        confirmed_students=confirmed_students,
        unassigned_students=unassigned_students,
    )


@app.route("/trips/<int:trip_id>/register", methods=["POST"])
def register_route(trip_id):
    """Register a student for a trip."""
    def action():
        register_student(
            trip_id,
            request.form.get("name", ""),
            request.form.get("email", "")
        )

    handle_action(action, "Registration submitted.")
    return redirect(url_for("trip_page", trip_id=trip_id))


@app.route("/trips/<int:trip_id>/pay/<int:registration_id>",
           methods=["POST"])
def payment_route(trip_id, registration_id):
    """Confirm a student's payment."""
    def action():
        check_registration_on_trip(trip_id, registration_id)
        confirm_payment(registration_id)

    handle_action(action, "Payment confirmed.")
    return redirect(url_for("trip_page", trip_id=trip_id))


@app.route("/trips/<int:trip_id>/cancel/<int:registration_id>",
           methods=["POST"])
def cancel_route(trip_id, registration_id):
    """Cancel a registration and free its place and room."""
    def action():
        check_registration_on_trip(trip_id, registration_id)
        cancel_registration(registration_id)

    handle_action(action, "Registration cancelled.")
    return redirect(url_for("trip_page", trip_id=trip_id))


@app.route("/trips/<int:trip_id>/rooms/create", methods=["POST"])
def create_room_route(trip_id):
    """Create a room for the selected trip."""
    def action():
        create_room(
            trip_id,
            request.form.get("name", ""),
            form_int("capacity", "Room capacity must be between 1 and 6")
        )

    handle_action(action, "Room created successfully.")
    return redirect(url_for("trip_page", trip_id=trip_id))


@app.route("/trips/<int:trip_id>/rooms/assign", methods=["POST"])
def assign_room_route(trip_id):
    """Assign a confirmed student to a room."""
    def action():
        room_id = form_int("room_id", "Choose a room")
        registration_id = form_int("registration_id", "Choose a student")
        check_room_on_trip(trip_id, room_id)
        check_registration_on_trip(trip_id, registration_id)
        assign_student(room_id, registration_id)

    handle_action(action, "Student assigned to room.")
    return redirect(url_for("trip_page", trip_id=trip_id))


@app.route("/trips/<int:trip_id>/preferences", methods=["POST"])
def preference_route(trip_id):
    """Record a student's preferred roommate."""
    def action():
        registration_id = form_int("registration_id", "Choose a student")
        preferred_id = form_int(
            "preferred_registration_id", "Choose a preferred roommate"
        )
        check_registration_on_trip(trip_id, registration_id)
        check_registration_on_trip(trip_id, preferred_id)
        add_roommate_preference(registration_id, preferred_id)

    handle_action(action, "Roommate preference saved.")
    return redirect(url_for("trip_page", trip_id=trip_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
