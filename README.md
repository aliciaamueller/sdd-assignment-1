# Ski Club Manager 

**Software Development and DevOps — Individual Assignment 1**  
Alicia Mueller Reglero | IE University

## 1. Project Overview

Ski Club Manager is a Python web application designed to help university ski clubs organize trips, manage student registrations and allocate accommodation.

The idea comes from the practical challenges of organizing group ski trips, where limited places, waiting lists and roommate requests need to be managed together.

The application is divided into two main domains:

- **Trip Management:** Manages ski trips, registrations, payment reservations, cancellations and waiting lists.
- **Room Allocation:** Manages rooms, student assignments and roommate preferences.

The aim is to keep the application simple enough to run as a single service while separating responsibilities clearly in the code.

## 2. Features

### Currently implemented

- SQLite database with five tables: trips, registrations, rooms, room assignments and roommate preferences.
- Database constraints to prevent duplicate active registrations and invalid capacity values.
- Preservation of cancelled registration records, allowing students to register again.
- Trip creation with validation of name, destination, dates and capacity.
- Student registration. A free place is reserved as `pending_payment` for 48 hours; when the trip is full the student joins a first-come, first-served waiting list.
- Payment confirmation within the 48-hour window (`pending_payment` → `confirmed`).
- Cancellation, which keeps the record and offers the freed place to the longest-waiting student.
- Expiry of unpaid reservations. With no background jobs in a single process, expired reservations are released at the start of every registration, payment or cancellation for that trip.
- Dashboard statistics for trip capacity, confirmed and unpaid registrations, waiting lists, remaining places and room allocation.
- Automatic upgrade of a database created before the payment status existed, without losing rows.
- Room creation (1–6 beds) and manual assignment of confirmed students, with checks that the room belongs to the student's trip and is not full.
- Roommate preferences between two confirmed students on the same trip.
- Release of a student's room when their registration is cancelled.
- Flask web interface: a dashboard of all trips, and a trip page for registrations, payments, cancellations, rooms and roommate preferences. The layout adapts to phone screens.
- Form validation in the web routes, with readable error messages, and a check that every registration or room in a request belongs to the trip in the URL.
- Automated pytest tests for trips, registrations, payments, the waiting list, rooms, roommate preferences, dashboard statistics, database start-up, the web routes and simultaneous registrations.
- Root `Dockerfile` (the provided template with its TODOs filled in), passing the `container/run.sh` contract check.

### Planned functionality

- Edit existing ski trips.

An additional feature being considered is automatic roommate matching based on shared preferences, while keeping manual assignments unchanged.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application and business logic |
| Flask | Web application framework |
| SQLite | Persistent relational database |
| HTML and CSS | Web interface (Jinja templates) |
| pytest | Automated testing |
| pytest-cov | Test coverage measurement |
| Docker | Single-container deployment |

The application uses Python's built-in `sqlite3` module rather than an external ORM.

## 4. Architecture

The application follows a modular monolith approach. Both domains run inside one Flask application and share one SQLite database, but each domain is responsible for its own data and business rules.

**Trip Management** owns:

- `trips`
- `registrations`

**Room Allocation** owns:

- `rooms`
- `room_assignments`
- `roommate_preferences`

The boundary between these domains is deliberate. Within each domain, SQLite foreign keys are used where appropriate. Across the domain boundary, Room Allocation stores trip and registration IDs without database-level foreign keys.

This means the Python application must validate cross-domain relationships, including whether a student is confirmed for the correct trip before assigning a room.

The reasons for these decisions are documented in `ADR.md`.

## 5. Project Structure

```text
sdd-assignment-1/
├── app.py
├── config.py
├── db.py
├── schema.sql
├── trip_management.py
├── trip_statistics.py
├── room_allocation.py
├── templates/
│   ├── base.html
│   ├── index.html
│   └── trip.html
├── static/
│   └── style.css
├── requirements.txt
├── pytest.ini
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_db.py
│   ├── test_room_allocation.py
│   ├── test_trip_management.py
│   └── test_trip_statistics.py
├── container/
│   ├── Dockerfile
│   ├── README.md
│   └── run.sh
├── Dockerfile
├── ADR.md
├── AI_USAGE.md
├── ASSIGNMENT_BRIEF.md
└── README.md
```

**Main files:**

- `app.py`: Flask application entry point. The routes only read the form, call the domain modules and redirect; it also formats trip dates for display.
- `config.py`: Reads environment variables for the server port, database directory and secret key.
- `db.py`: Opens SQLite connections, initializes the database and upgrades an older `registrations` table.
- `schema.sql`: Defines the database tables, constraints and indexes.
- `trip_management.py`: Creates trips; registers, confirms payment for and cancels students; expires unpaid reservations and promotes the waiting list.
- `room_allocation.py`: Creates rooms, assigns confirmed students to them and records roommate preferences.
- `trip_statistics.py`: Calculates the statistics shown on the dashboard and trip page.
- `templates/` and `static/`: The HTML pages and the stylesheet for the web interface.
- `pytest.ini`: Lets plain `pytest` find the project modules and the `tests/` folder.
- `tests/`: Contains automated tests. `conftest.py` provides the shared `test_db` fixture (a temporary database with the schema loaded).
- `Dockerfile`: The provided template copied to the root, with its four TODOs filled in.
- `container/`: Contains the professor-provided Docker template and contract checker.
- `ADR.md`: Records architectural decisions.
- `AI_USAGE.md`: Documents how AI tools were used during development.

## 6. Running the Application Locally

### Requirements

- Python 3
- pip

### Installation

Clone the repository:

```bash
git clone https://github.com/aliciaamueller/sdd-assignment-1.git
cd sdd-assignment-1
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

By default, the application runs at:

http://localhost:8000

The home page is the trip dashboard. From there you can create a trip and open it to manage registrations, payments and rooms.

## 7. Configuration

The application reads three environment variables:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Port used by the Flask server |
| `DATA_DIR` | `./data` | Directory containing the SQLite database |
| `SECRET_KEY` | `ski-club-local-demo` | Signs the session cookie used for flash messages. Set your own value in any shared deployment |

For example:

```bash
PORT=9000 DATA_DIR=./local_data python app.py
```

The SQLite database is initialized automatically using `schema.sql`. Existing tables and data are preserved during repeated initialization.

`CREATE TABLE IF NOT EXISTS` never changes a table that already exists, so a database created before the `pending_payment` status was added would keep the old rules. On start-up, `init_db` detects that case and rebuilds `registrations` in one transaction, copying every row across.

## 8. Testing

The project uses pytest for automated tests.

`pytest.ini` puts the project root on the import path and points pytest at `tests/`, so plain `pytest` works from the repo root.

Run all tests:

```bash
pytest -v
```

Run tests with coverage. Coverage is measured on the business-logic modules only, so test files and framework glue (`app.py`, `config.py`, `db.py`) do not inflate the number:

```bash
pytest --cov=trip_management --cov=trip_statistics --cov=room_allocation --cov-report=term-missing
```

Current result (55 tests):

```text
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
room_allocation.py      96      5    95%   12, 57, 65, 135, 173
trip_management.py     112      0   100%
trip_statistics.py      15      0   100%
--------------------------------------------------
TOTAL                  223      5    98%
```

The uncovered lines in `room_allocation.py` are error checks with no test yet (an empty room name, an unknown room or registration, and a missing trip when listing rooms).

The trip creation tests check that:

- A valid trip is saved and its ID is returned.
- An invalid or boolean capacity, an empty name or destination, and invalid dates are rejected with `ValueError`.

The registration tests check that:

- A student with a free place gets `pending_payment` and a payment deadline; email is stored lowercased.
- A student on a full trip is waitlisted with no deadline.
- Duplicate emails, unknown trips and empty names or emails are rejected.
- Payment inside 48 hours confirms the place; payment after 48 hours is refused, the place is released and the first waitlisted student is promoted.
- An expired reservation frees its place for the next new student.
- Cancelling promotes the longest-waiting student, cancelling a waitlisted student promotes nobody, and a cancelled student can register again.

- Ten students registering at the same moment for a trip with two places end up as exactly two reservations and eight waitlisted students. The test starts ten threads together with a `threading.Barrier`. It passes because `register_student` locks the database with `BEGIN IMMEDIATE` before counting the free places.

Time-based tests replace `trip_management._now` with `monkeypatch`, so they move the clock forward instead of waiting.

The room allocation tests (`test_room_allocation.py`) check that:

- Rooms are created with 1–6 beds, and duplicate names or unknown trips are rejected.
- Only confirmed students are assigned, never to a full room, a room on another trip, or a second room.
- Roommate preferences need two confirmed students on the same trip, and cannot be duplicated or point at the student themselves.
- Cancelling a student frees their bed and promotes the next waitlisted student.

The dashboard tests check that:

- A trip with no registrations produces the expected statistics.
- Confirmed registrations, waiting lists and room assignments are counted correctly.
- Unpaid reservations still use up places, but do not yet need a room.
- Cancelled or waitlisted students who still have a room are not counted as assigned.
- Asking for an unknown trip raises `ValueError`.

The web tests (`test_app.py`) use Flask's test client to check that:

- The dashboard and trip pages load, and an unknown trip returns 404.
- A blank number in a form shows a readable error message.
- A registration or room from another trip is refused, even when its ID is put in the URL.
- A full flow (register, pay, create a room, assign it, save a preference) works through the routes.
- Trip dates are formatted as short ranges, e.g. `10 – 15 Jan 2027`.

The database tests (`test_db.py`) check that running `init_db` twice keeps existing data, and that an old-format `registrations` table is upgraded with its rows intact.

The tests use temporary SQLite databases to avoid modifying application data.

## 9. Docker Deployment

The assignment requires a single Docker container, configurable through `PORT` and `DATA_DIR`, with persistent SQLite storage.

The professor-provided Dockerfile template is available in `container/Dockerfile`, together with the contract checker `container/run.sh`.

The root `Dockerfile` is that template with only its four `TODO` lines filled in: the `python:3.12-slim` base image, installing from `requirements.txt`, copying the application files (tests are left out), and starting the app with `python app.py`.

Build and run it:

```bash
docker build -t ski-club .
docker run -p 8000:8000 -v ski-club-data:/data ski-club
```

Run the contract check:

```bash
./container/run.sh .
```

Result:

```text
=== SDD Assignment 1 contract check ===

==> Repository shape
  PASS  one Dockerfile, one manifest (requirements.txt)

==> Build from a clean context, no build args
  PASS  image built
  PASS  image size 53 MB

==> Start on PORT=8000 and reach it from the host
  PASS  HTTP 200 from http://localhost:8000/

==> SQLite file under DATA_DIR
  PASS  found in /data: ski_club.db

==> Data persists, and a second boot does not re-seed
  PASS  volume at /data persists
  PASS  row counts unchanged across restart: registrations=0 room_assignments=0 roommate_preferences=0 rooms=0 trips=0

==> PORT override is honoured (not hardcoded)
  PASS  HTTP 200 from http://localhost:9123/

=== ALL CHECKS PASSED ===
```

Re-run after the web interface and room allocation were added; the result is unchanged.

## 10. Development and Documentation

Development is being completed incrementally, with functionality implemented and tested in small steps.

The repository also includes:

- **`ADR.md`** — Architectural decisions and trade-offs.
- **`AI_USAGE.md`** — AI assistance, prompts, outcomes and reflections.
- **`ASSIGNMENT_BRIEF.md`** — Original assignment requirements, preserved for reference.

## 11. Current Status

Both domains are implemented: Trip Management (trips, registration, payment, cancellation and the waiting list) and Room Allocation (rooms, assignments and roommate preferences). Cancelling a student releases their room. The web interface, dashboard statistics and the container setup are complete, and the contract check passes.

Remaining work before submission: editing existing trips, and possibly automatic roommate matching.