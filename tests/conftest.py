import sqlite3
import pytest
import db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create a temporary database for each test."""

    db_path = tmp_path / "test.db"

    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))

    db.init_db()

    return db_path
