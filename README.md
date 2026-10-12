# Ski Club Manager

**Software Development & DevOps | Individual Assignment 1**  
Alicia Mueller Reglero | IE University

*Managing the trip is one thing. Managing everyone going is another.*

## Why I built this

Organising ski trips for a university club has made me realise that the difficult part isn't necessarily choosing the destination or planning the dates. It's everything that happens once registrations open.

Places fill up quickly, payments arrive at different times, waiting lists keep changing, and room assignments depend on who has actually confirmed their place.

I built Ski Club Manager around those challenges: a small web application that keeps registrations, payments and accommodation connected, without making the underlying system unnecessarily complicated.

The application uses **Python, Flask and SQLite**, with a responsive web interface and two separate areas of responsibility: Trip Management and Room Allocation.

## 1. How it works

### Trip registration and payments

Each trip has a fixed number of places. When a student registers, the application checks availability and assigns one of four statuses:

| Status | Meaning |
|---|---|
| `pending_payment` | A place is reserved for 48 hours |
| `confirmed` | Payment has been confirmed |
| `waitlisted` | The trip is full, so the student joins the waiting list |
| `cancelled` | The registration was cancelled or the payment deadline expired |

When someone cancels or a payment deadline expires, the first student on the waiting list receives the available place and a new 48-hour payment window.

Expired reservations are processed whenever a registration, payment or cancellation is handled. This keeps the application within the single-process requirement without introducing background workers.

### Room allocation

Once payment is confirmed, organisers can create rooms with one to six beds, assign students and record roommate preferences.

The application checks that students are confirmed, rooms belong to the correct trip and no room exceeds its capacity. Cancelling a registration also releases the student's room assignment.

### Dashboard

The Flask interface provides an overview of each trip, including available places, confirmed registrations, pending payments, waiting lists and accommodation progress.

Each trip has its own management page, where organisers can handle registrations, payments, cancellations, rooms and roommate preferences.

## 2. Architecture

Ski Club Manager follows a **modular monolith** approach: one Flask application, one SQLite database and two logically separate business domains.

```text
                      Flask Web Interface
                             app.py
                               |
                +--------------+--------------+
                |                             |
         Trip Management                Room Allocation
                |                             |
       trip_management.py              room_allocation.py
       trip_statistics.py                     |
                |                             |
        trips, registrations           rooms, assignments,
                                     roommate preferences
                |                             |
                +--------------+--------------+
                               |
                         SQLite Database
```

**Trip Management** owns the `trips` and `registrations` tables. It handles capacity, payments, cancellations and waiting-list order.

**Room Allocation** owns `rooms`, `room_assignments` and `roommate_preferences`. It handles accommodation independently of the registration lifecycle.

The boundary between them is intentional. Foreign keys are used within each domain, while references crossing the domain boundary are stored as integer IDs and validated in Python.

This allows the two domains to remain separate in the code while running together in one application. It also provides a starting point for separating them into services in Assignment 2.

The database schema is defined in `schema.sql`, with constraints and indexes that protect important rules such as room capacity and duplicate active registrations.

The design choices and alternatives are explained in [ADR.md](ADR.md).

## 3. Getting started

### Run locally

Requirements: Python 3 and pip.

Clone the repository and install the dependencies:

```bash
git clone https://github.com/aliciaamueller/sdd-assignment-1.git
cd sdd-assignment-1

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Open **http://localhost:8000** in your browser.

The database is created automatically on first startup. Existing data is preserved when the application restarts.

### Run with Docker

The root `Dockerfile` uses the professor-provided template, with its TODOs completed.

```bash
docker build -t ski-club .
docker run -p 8000:8000 -v ski-club-data:/data ski-club
```

The named Docker volume preserves the SQLite database between container restarts.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Port used by the Flask server |
| `DATA_DIR` | `./data` | Directory containing the SQLite database |
| `SECRET_KEY` | `ski-club-local-demo` | Flask session signing key for flash messages |

For example, to run locally with a different port and data directory:

```bash
PORT=9000 DATA_DIR=./local_data python app.py
```

Set a separate `SECRET_KEY` for any shared deployment.

**SQLite path:** the database file is always `$DATA_DIR/ski_club.db`. That is `./data/ski_club.db` when running locally with the default, and `/data/ski_club.db` inside the container, where `/data` is the mounted volume.

The application initializes its database using `schema.sql`. It also includes a small upgrade procedure for databases created before the `pending_payment` status existed, preserving existing registration records.

## 4. Testing and reliability

The project uses **pytest** and **pytest-cov**. Tests run against temporary SQLite databases, so they do not modify real application data.

Run all tests:

```bash
python -m pytest -v
```

Run tests with coverage:

```bash
python -m pytest \
  --cov=trip_management \
  --cov=trip_statistics \
  --cov=room_allocation \
  --cov-report=term-missing
```

Coverage is measured on the three business-logic modules, rather than including test files or Flask presentation code.

### Recorded test results

**61 tests | 100% business-logic coverage** (run on 2026-10-12)

```text
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
room_allocation.py     103      0   100%
trip_management.py     117      0   100%
trip_statistics.py      15      0   100%
--------------------------------------------------
TOTAL                  235      0   100%
```

100% is line coverage, not proof that every combination of rules is tested; the testing priorities are explained in ADR 4.

The tests cover the complete registration and payment lifecycle, FIFO waiting-list promotion, room capacity and assignment rules, roommate preferences, dashboard calculations, database initialization and migration, and Flask routes.

They also check invalid inputs and attempts to access registrations or rooms belonging to another trip.

### Preventing overbooking

One test starts **10 simultaneous registrations for a trip with only 2 available places**.

The expected result is two reserved places and eight waitlisted students.

The registration function uses SQLite's `BEGIN IMMEDIATE` transaction before checking capacity, so simultaneous requests cannot independently reserve the same remaining places.

Time-dependent tests use `monkeypatch` to simulate payment deadlines without waiting 48 hours.

### Docker contract check

The professor-provided checker can be run with:

```bash
./container/run.sh .
```

Output from the run on 2026-10-12, against the final code:

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

The checker verifies the container build, HTTP availability, configurable port, SQLite persistence and safe initialization across restarts.

## 5. Engineering decisions

A few decisions were particularly important during development.

**Keeping the implementation simple.** Flask and Python's built-in `sqlite3` module were sufficient for this project's scope. Using direct SQL also makes the database constraints and queries easier to follow.

**Preserving registration history.** Cancelled registrations are retained instead of deleted. A partial unique index prevents duplicate active registrations while allowing students to register again after cancelling.

**Handling simultaneous requests safely.** Database transactions protect capacity checks and registration updates, rather than assuming that registrations will always happen one at a time.

**Keeping responsibilities separate.** Trip Management and Room Allocation share one database but have distinct tables and business rules. One deliberate cross-domain query remains in the dashboard statistics, as documented in the architecture decisions.

**Design patterns where they earn their place.** Each domain module acts as a **Facade**: its public functions are the only way the rest of the app changes that domain, and they become the service endpoints in Assignment 2. Cancelling a registration uses an **Observer**: Room Allocation subscribes with `on_registration_cancelled`, so Trip Management never writes to room tables. Room Allocation reads registration data only through `_get_registration`, an **Adapter** that is the single function to swap for an API call after the split. `get_connection` is a **simple factory** for identically configured connections, and `handle_action` in `app.py` runs each route's action **Command-style** with shared error handling. Heavier patterns such as Builder and Strategy were left out because nothing in the current app needs them.

**Avoiding unnecessary infrastructure.** The application uses one process and one container. Payment expiry is checked during relevant operations rather than introducing background jobs or additional services.

These decisions, including alternatives and consequences, are documented in [ADR.md](ADR.md).

## 6. Project structure

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
├── requirements.txt
├── pytest.ini
├── ADR.md
├── AI_USAGE.md
├── ASSIGNMENT_BRIEF.md
└── README.md
```

### Main files

| File | Responsibility |
|---|---|
| `app.py` | Flask entry point, routes, form handling and rendering |
| `config.py` | Reads environment variables and defines application settings |
| `db.py` | SQLite connections, database initialization and schema upgrade |
| `schema.sql` | Database tables, constraints and indexes |
| `trip_management.py` | Trip creation, registration, payments, cancellation and waitlist promotion |
| `trip_statistics.py` | Calculates trip availability and accommodation statistics |
| `room_allocation.py` | Room creation, student assignments and roommate preferences |
| `templates/base.html` | Shared page layout and navigation |
| `templates/index.html` | Trip dashboard and trip creation form |
| `templates/trip.html` | Individual trip management page |
| `static/style.css` | Styling and responsive layout |
| `tests/conftest.py` | Shared temporary database fixture |
| `tests/test_app.py` | Flask route and interface workflow tests |
| `tests/test_db.py` | Database initialization and migration tests |
| `tests/test_room_allocation.py` | Room and roommate preference tests |
| `tests/test_trip_management.py` | Trip, registration, payment and waitlist tests |
| `tests/test_trip_statistics.py` | Dashboard statistics tests |
| `pytest.ini` | pytest configuration and import paths |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Single-container application build |
| `container/` | Professor-provided Docker template and contract checker |
| `ADR.md` | Architectural decisions and their trade-offs |
| `AI_USAGE.md` | Record of AI assistance and development decisions |
| `ASSIGNMENT_BRIEF.md` | Original assignment instructions |

## 7. Development and documentation

The project was developed incrementally, with Git commits recording changes to the application, tests and documentation.

The supporting documents provide more detail:

- [ADR.md](ADR.md): architectural decisions, alternatives and consequences.
- [AI_USAGE.md](AI_USAGE.md): use of ChatGPT and Claude Code, including prompts, accepted or modified suggestions, and explanations of the resulting code.
- [ASSIGNMENT_BRIEF.md](ASSIGNMENT_BRIEF.md): the original assignment requirements.

The current implementation focuses on the two required domains. Editing existing trips and automatic roommate matching are possible future extensions, rather than dependencies of the existing workflow.