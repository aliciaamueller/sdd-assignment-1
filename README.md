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
- Dashboard statistics for trip capacity, confirmed students, waiting lists, remaining places and room allocation.
- Automated pytest tests for dashboard statistics.

### Planned functionality

- Create and manage ski trips.
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
| Docker | Containerized deployment (planned) |

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
├── trip_statistics.py
├── requirements.txt
├── tests/
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
- `trip_statistics.py`: Calculates the statistics used by the future dashboard.
- `tests/`: Contains automated tests.
- `container/`: Contains the professor-provided Docker template and contract checker.
- `ADR.md`: Records architectural decisions.
- `AI_USAGE.md`: Documents how AI tools were used during development.

Some files listed above are planned deliverables and may not exist until later development stages.

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

Run all tests:

```bash
python -m pytest -v
```

Run tests with coverage:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

The current dashboard tests check that:

- A trip with no registrations produces the expected statistics.
- Confirmed registrations, waiting lists and room assignments are counted correctly.

The tests use temporary SQLite databases to avoid modifying application data.

## 9. Docker Deployment

The assignment requires a single Docker container, configurable through `PORT` and `DATA_DIR`, with persistent SQLite storage.

The professor-provided Dockerfile template is available in `container/Dockerfile`, together with the contract checker `container/run.sh`.

The root Dockerfile and final container verification are still part of the development work.

Once the container configuration is complete, the required check will be run with:

```bash
./container/run.sh .
```

The final verification results will be documented here before submission.

## 10. Development and Documentation

Development is being completed incrementally, with functionality implemented and tested in small steps.

The repository also includes:

- **`ADR.md`** — Architectural decisions and trade-offs.
- **`AI_USAGE.md`** — AI assistance, prompts, outcomes and reflections.
- **`ASSIGNMENT_BRIEF.md`** — Original assignment requirements, preserved for reference.

## 11. Current Status

The database structure, Flask skeleton and dashboard calculation logic have been implemented.

The next development stages are Trip Management, Room Allocation, cross-domain cancellation handling, the web interface, Docker verification and final testing.

The application is still under development and is not yet the final submission version.