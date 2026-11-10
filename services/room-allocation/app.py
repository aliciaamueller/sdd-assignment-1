"""Room Allocation service: rooms, room assignments and roommate preferences.

Initial skeleton for the Assignment 2 split. The room logic from the monolith
moves here in the next steps.
"""

import os

from flask import Flask, jsonify

# Commit SHA of the running image, set by the pipeline at deploy time.
VERSION = os.environ.get("GIT_SHA", "dev")

# Base URL of the Trip Management service, used to check trips and
# registrations over HTTP instead of reading its tables.
TRIPS_URL = os.environ.get("TRIPS_URL", "http://trip-management:8000")

app = Flask(__name__)


@app.get("/health")
def health():
    """Report that the service is up. The database check is added with the database."""
    return jsonify(status="ok", service="room-allocation", version=VERSION)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
