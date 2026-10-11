
import sqlite3

from trip_statistics import get_trip_statistics


def test_empty_trip_statistics(tmp_path, monkeypatch):
    # Use a temporary database so we don't change real data.
    db_path = tmp_path / "test.db"

    import db
    monkeypatch.setattr(db, "DB_PATH", str(db_path))

    # Create the five tables in the temporary database.
    with open(db.SCHEMA_PATH) as file:
        schema = file.read()

    conn = sqlite3.connect(db_path)
    conn.executescript(schema)

    # Create a trip with 100 available places.
    conn.execute(
        """
        INSERT INTO trips
        (name, destination, start_date, end_date, capacity)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Andorra", "Andorra", "2027-01-20", "2027-01-24", 100)
    )
    conn.commit()
    conn.close()

    # Check that an empty trip shows the correct numbers.
    result = get_trip_statistics(1)

    assert result["capacity"] == 100
    assert result["confirmed"] == 0
    assert result["waitlisted"] == 0
    assert result["places_remaining"] == 100
    assert result["room_assigned"] == 0
    assert result["need_room"] == 0
    assert result["occupancy_percent"] == 0.0



def test_trip_statistics_with_students(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    import db
    monkeypatch.setattr(db, "DB_PATH", str(db_path))

    with open(db.SCHEMA_PATH) as file:
        schema = file.read()

    conn = sqlite3.connect(db_path)
    conn.executescript(schema)

    # Create a trip with 5 places.
    conn.execute(
        """
        INSERT INTO trips
        (id, name, destination, start_date, end_date, capacity)
        VALUES (1, 'Andorra', 'Andorra', '2027-01-20', '2027-01-24', 5)
        """
    )

    # Register three confirmed students and one waitlisted student.
    students = [
        (1, 1, "Sofia", "sofia@example.com", "confirmed"),
        (2, 1, "Emma", "emma@example.com", "confirmed"),
        (3, 1, "Lucas", "lucas@example.com", "confirmed"),
        (4, 1, "Daniel", "daniel@example.com", "waitlisted"),
    ]

    for student in students:
        conn.execute(
            """
            INSERT INTO registrations
            (id, trip_id, name, email, status, registered_at)
            VALUES (?, ?, ?, ?, ?, '2026-10-11T15:00:00')
            """,
            student
        )

    # Create a room and assign Sofia and Emma.
    conn.execute(
        "INSERT INTO rooms (id, trip_id, name, capacity) VALUES (1, 1, 'Room A', 4)"
    )
    conn.execute(
        "INSERT INTO room_assignments (room_id, registration_id) VALUES (1, 1)"
    )
    conn.execute(
        "INSERT INTO room_assignments (room_id, registration_id) VALUES (1, 2)"
    )

    conn.commit()
    conn.close()

    result = get_trip_statistics(1)

    assert result["capacity"] == 5
    assert result["confirmed"] == 3
    assert result["waitlisted"] == 1
    assert result["places_remaining"] == 2
    assert result["room_assigned"] == 2
    assert result["need_room"] == 1
    assert result["occupancy_percent"] == 60.0

