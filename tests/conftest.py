"""Shared database setup for tests."""

import pytest

import db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Provide a fresh SQLite connection for each test."""

    db_path = tmp_path / "test.db"

    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))

    db.init_db()

    conn = db.get_connection()

    try:
        yield conn
    finally:
        conn.close()
