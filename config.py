"""App settings, read from environment variables with sensible defaults."""

import os

# Port the web server listens on.
PORT = int(os.environ.get("PORT", "8000"))

# Folder that holds the SQLite database file.
DATA_DIR = os.environ.get("DATA_DIR", "./data")

# Full path to the database file inside DATA_DIR.
DB_PATH = os.path.join(DATA_DIR, "ski_club.db")
