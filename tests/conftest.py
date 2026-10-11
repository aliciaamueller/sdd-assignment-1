import sqlite3

import pytest

import db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Give each test its own empty database with the five tables created."""
    # Use a temporary database so we don't change real data.
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_path))

    with open(db.SCHEMA_PATH) as file:
        schema = file.read()

    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    yield conn
    conn.close()
