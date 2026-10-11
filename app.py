"""Flask web app entry point."""

from flask import Flask

from config import PORT
from db import init_db

app = Flask(__name__)

# Prepare the database before handling any requests.
init_db()


@app.route("/")
def index():
    """Simple home page so we can check the app is running."""
    return "<h1>Ski Club</h1><p>The app is running.</p>"


if __name__ == "__main__":
    # 0.0.0.0 makes the app reachable from outside a container.
    app.run(host="0.0.0.0", port=PORT)
