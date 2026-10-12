"""App settings, read from environment variables with sensible defaults.

Singleton: Python runs a module only once, on its first import, so these
settings are read from the environment once at startup and every module
that imports them shares the same values. A Singleton class would add
nothing a module does not already give us.
"""

import os

# Port the web server listens on.
PORT = int(os.environ.get("PORT", "8000"))

# Folder that holds the SQLite database file.
DATA_DIR = os.environ.get("DATA_DIR", "./data")

# Full path to the database file inside DATA_DIR.
DB_PATH = os.path.join(DATA_DIR, "ski_club.db")

# Signs the session cookie used for flash messages. Set SECRET_KEY in any
# shared deployment; the default is only for local use.
SECRET_KEY = os.environ.get("SECRET_KEY", "ski-club-local-demo")
