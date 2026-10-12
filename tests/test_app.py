"""Tests for the Flask routes."""

import pytest

from app import app
from room_allocation import create_room
from trip_management import confirm_payment, create_trip, register_student


@pytest.fixture
def client(test_db):
    app.config["TESTING"] = True
    return app.test_client()


def make_trip(name="Andorra"):
    return create_trip(name, "Grandvalira", "2027-01-10", "2027-01-15", 4)


def test_dashboard_and_trip_page_load(client):
    trip_id = make_trip()

    assert client.get("/").status_code == 200
    assert client.get(f"/trips/{trip_id}").status_code == 200
    assert client.get("/trips/999").status_code == 404


def test_blank_capacity_shows_friendly_error(client):
    response = client.post(
        "/trips/create",
        data={
            "name": "A", "destination": "B",
            "start_date": "2027-01-10", "end_date": "2027-01-15",
            "capacity": "",
        },
        follow_redirects=True,
    )

    page = response.get_data(as_text=True)
    assert "Capacity must be a positive integer" in page
    assert "invalid literal" not in page


def test_cannot_cancel_registration_through_another_trip(client, test_db):
    trip_a = make_trip("A")
    trip_b = make_trip("B")
    reg_id = register_student(trip_b, "Ann", "ann@example.com")

    response = client.post(
        f"/trips/{trip_a}/cancel/{reg_id}", follow_redirects=True
    )

    assert "Registration not found on this trip" in response.get_data(as_text=True)
    status = test_db.execute(
        "SELECT status FROM registrations WHERE id = ?", (reg_id,)
    ).fetchone()["status"]
    assert status == "pending_payment"


def test_full_flow_through_routes(client, test_db):
    trip_id = make_trip()
    client.post(f"/trips/{trip_id}/register",
                data={"name": "Ann", "email": "ann@example.com"})
    client.post(f"/trips/{trip_id}/register",
                data={"name": "Bob", "email": "bob@example.com"})
    client.post(f"/trips/{trip_id}/pay/1")
    confirm_payment(2)
    client.post(f"/trips/{trip_id}/rooms/create",
                data={"name": "R1", "capacity": "2"})
    client.post(f"/trips/{trip_id}/rooms/assign",
                data={"room_id": "1", "registration_id": "1"})
    response = client.post(
        f"/trips/{trip_id}/preferences",
        data={"registration_id": "1", "preferred_registration_id": "2"},
        follow_redirects=True,
    )

    assert "Roommate preference saved." in response.get_data(as_text=True)
    assert test_db.execute(
        "SELECT COUNT(*) FROM room_assignments"
    ).fetchone()[0] == 1


def test_cannot_assign_room_from_another_trip(client, test_db):
    trip_a = make_trip("A")
    trip_b = make_trip("B")
    reg_id = register_student(trip_a, "Ann", "ann@example.com")
    confirm_payment(reg_id)
    room_id = create_room(trip_b, "R1", 2)

    response = client.post(
        f"/trips/{trip_a}/rooms/assign",
        data={"room_id": str(room_id), "registration_id": str(reg_id)},
        follow_redirects=True,
    )

    assert "Room not found on this trip" in response.get_data(as_text=True)
