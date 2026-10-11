# Ski Club Manager 

**Software Development and DevOps — Individual Assignment 1**  
Alicia Mueller Reglero | IE University

## 1. Project Overview

Ski Club Manager is a Python web application designed to help university ski clubs organize trips, manage student registrations and allocate accommodation.

The idea comes from the practical challenges of organizing group ski trips, where limited places, waiting lists and roommate requests need to be managed together.

The application is divided into two main domains:

- **Trip Management:** Manages ski trips, registrations, available places, cancellations and waiting lists.
- **Room Allocation:** Manages rooms, student assignments and roommate preferences.

The aim is to keep the application simple enough to run as a single service while separating responsibilities clearly in the code.

## 2. Features

### Currently implemented

- SQLite database with five tables: trips, registrations, rooms, room assignments and roommate preferences.
- Database constraints to prevent duplicate active registrations and invalid capacity values.
- Preservation of cancelled registration records, allowing students to register again.
- Trip creation with validation of name, destination, dates and capacity.
- Dashboard statistics for trip capacity, confirmed students, waiting lists, remaining places and room allocation.
- Automated pytest tests for trip creation and dashboard statistics.
- Root `Dockerfile` (the provided template with its TODOs filled in), passing the `container/run.sh` contract check.

### Planned functionality

- Edit and list ski trips.
- Register students and automatically place them on waiting lists when trips reach capacity.
- Cancel registrations and promote the next waitlisted student.
- Create rooms and manually assign confirmed students.
- Record roommate preferences.
- Release room assignments when students cancel.
- Display trip information and statistics through a Flask web interface.

An additional feature being considered is automatic roommate matching based on shared preferences, while keeping manual assignments unchanged.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application and business logic |
| Flask | Web application framework |
| SQLite | Persistent relational database |
| HTML | Web interface (planned) |
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
├── requirements.txt
├── pytest.ini
├── tests/
│   ├── conftest.py
│   ├── test_trip_management.py
│   └── test_trip_statistics.py
├── container/
│   ├── Dockerfile
│   └── run.sh
├── Dockerfile
├── ADR.md
├── AI_USAGE.md
├── ASSIGNMENT_BRIEF.md
└── README.md
```

**Main files:**

- `app.py`: Flask application entry point.
- `config.py`: Reads environment variables for the server port and database directory.
- `db.py`: Opens SQLite connections and initializes the database.
- `schema.sql`: Defines the database tables, constraints and indexes.
- `trip_management.py`: Creates ski trips after validating their details.
- `trip_statistics.py`: Calculates the statistics used by the future dashboard.
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

The current home page is a basic server-running confirmation. The full interface will be developed later.

## 7. Configuration

The application reads two environment variables:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Port used by the Flask server |
| `DATA_DIR` | `./data` | Directory containing the SQLite database |

For example:

```bash
PORT=9000 DATA_DIR=./local_data python app.py
```

The SQLite database is initialized automatically using `schema.sql`. Existing tables and data are preserved during repeated initialization.

## 8. Testing

The project uses pytest for automated tests.

`pytest.ini` puts the project root on the import path and points pytest at `tests/`, so plain `pytest` works from the repo root.

Run all tests:

```bash
pytest -v
```

Run tests with coverage. Coverage is measured on the business-logic modules only, so test files and framework glue (`app.py`, `config.py`, `db.py`) do not inflate the number:

```bash
pytest --cov=trip_management --cov=trip_statistics --cov-report=term-missing
```

Add each new logic module (for example a room allocation module) to this command as it is created.

Current result (8 tests):

```text
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
trip_management.py      22      3    86%   17, 23-24
trip_statistics.py      13      0   100%
--------------------------------------------------
TOTAL                   35      3    91%
```

The trip creation tests check that:

- A valid trip is saved and its ID is returned.
- An invalid capacity, an empty name and invalid dates are rejected with `ValueError`.

The dashboard tests check that:

- A trip with no registrations produces the expected statistics.
- Confirmed registrations, waiting lists and room assignments are counted correctly.
- Cancelled or waitlisted students who still have a room are not counted as assigned.
- Asking for an unknown trip raises `ValueError`.

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

This will be re-run before submission as more features are added.

## 10. Development and Documentation

Development is being completed incrementally, with functionality implemented and tested in small steps.

The repository also includes:

- **`ADR.md`** — Architectural decisions and trade-offs.
- **`AI_USAGE.md`** — AI assistance, prompts, outcomes and reflections.
- **`ASSIGNMENT_BRIEF.md`** — Original assignment requirements, preserved for reference.

## 11. Current Status

The database structure, Flask skeleton, trip creation, dashboard calculation logic and the container setup have been implemented.

The next development stages are the rest of Trip Management (registration, waitlist and cancellation), Room Allocation, cross-domain cancellation handling, the web interface and final testing.

The application is still under development and is not yet the final submission version.