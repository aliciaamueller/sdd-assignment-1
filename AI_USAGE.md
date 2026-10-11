# AI Usage Log — Ski Club Manager

**Student:** Alicia Mueller Reglero  
**Assignment:** Software Development and DevOps — Individual Assignment 1

## How I used AI

I used Claude Code and ChatGPT as development assistants during this assignment. AI helped me understand unfamiliar concepts, plan the application, generate some initial code and troubleshoot errors.

I also worked directly in Cursor, created files, ran tests, reviewed outputs and used Git commands to commit and push changes.

Below is a record of the main AI interactions so far.

## AI Usage Log

Where I did not save the exact wording of a prompt, the Prompt column summarises what I asked for. "—" in the last column means the interaction produced no code.

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why | In my own words, how this works |
|---|---|---|---|---|---|
| Before 5349d00 | claude.ai | Planning chat: the Ski Club Manager idea, the two domains, the five-table schema and the prompts to give Claude Code | Accepted | Gave me the plan, the schema shape (status column, partial index, plain IDs across the seam) and the prompts I used for the skeleton and schema commits. | The chat split the app into Trip Management (`trips`, `registrations`) and Room Allocation (`rooms`, `room_assignments`, `roommate_preferences`). Room Allocation only stores trip and registration IDs, so it can become its own service later. |
| Before 5349d00 | ChatGPT | Discussed the app idea, its two domains and which features are realistic for the assignment | Accepted | Chose Trip Management and Room Allocation, with Flask and SQLite. | Flask keeps the app as one small process, and SQLite is one file in `DATA_DIR`, which fits the single-container rule. |
| b8d66d3 | Claude Code | Asked for a `requirements.txt` containing Flask, pytest and pytest-cov | Accepted | No changes. | One manifest at the root with pinned versions (`flask==3.1.3`, `pytest==9.1.1`, `pytest-cov==7.1.0`). `pip install -r requirements.txt` installs everything, both locally and in Docker. |
| 5349d00 | Claude Code | Asked for the initial Flask app, environment-based configuration and an SQLite connection helper | Accepted | Checked the files and the basic setup; no changes. | `config.py` reads `PORT` (default 8000) and `DATA_DIR` (default `./data`) and builds `DB_PATH` as `DATA_DIR/ski_club.db`. `get_connection` opens that file, sets `row_factory` so I can use `row["name"]`, and turns on `PRAGMA foreign_keys` because SQLite ignores foreign keys otherwise. `init_db` creates the folder and runs `schema.sql`. `app.py` calls `init_db()` at startup and binds `0.0.0.0` so the app is reachable from outside the container. |
| ae6b4fa | Claude Code | Gave requirements for five tables, their constraints, the domain boundary and safe re-initialization | Accepted | Accepted after the checks for duplicate registrations, cancellation and repeated initialization passed. | Every statement uses `IF NOT EXISTS`, so `init_db` can run on every boot without losing data. Registrations are never deleted: `status` is confirmed, waitlisted or cancelled. The partial unique index `idx_registrations_active_email` only covers confirmed and waitlisted rows, so the same email can't be active twice on a trip but can register again after cancelling. |
| — | ChatGPT | Reviewed examples from my previous Software Design and Development assignment to match my usual level of Python complexity | Modified | Used them only as a style reference and left out design patterns this app doesn't need. | — |
| 65a3a66 | ChatGPT | Asked for a function that calculates trip capacity, confirmed registrations, waiting list and room allocation statistics | Accepted | Typed it into `trip_statistics.py` myself in Cursor. | `get_trip_statistics(trip_id)` loads the trip's `capacity` and raises `ValueError("Trip not found")` if there is no trip. It counts `confirmed` and `waitlisted` registrations. `assigned` joins `room_assignments` to `registrations` and `rooms` and only counts confirmed students whose room is on the same trip, so cancelled or waitlisted students who still hold a room don't count. `places_remaining` is `capacity - confirmed` and `need_room` is `confirmed - assigned`, both floored at 0 with `max`. `occupancy_percent` is `confirmed / capacity * 100` rounded to one decimal. The connection is closed in `finally`. |
| 65a3a66 | ChatGPT | Asked how to write pytest tests that use a temporary SQLite database | Accepted | Wrote two tests and checked that both pass locally. | Each test points `db.DB_PATH` at a file in `tmp_path` with `monkeypatch`, loads `schema.sql` into it, inserts a trip and students, then checks every key that `get_trip_statistics` returns. The real database in `data/` is never touched. |
| — | ChatGPT | pytest was not found in my Python environment | Accepted | Created `.venv` and installed the requirements into it. | — |
| 2954989 | ChatGPT | Asked for draft ADR entries on the framework choice and the separation between the two domains | Modified | Used the drafts as a starting point; later restructured them into the brief's format (see the Claude Code row below). | — |
| 2954989 | ChatGPT | Asked for help organizing and drafting this AI usage log | Modified | Checked the draft against what actually happened; later converted to the required columns. | — |
| This commit | Claude Code | Pasted review feedback: add pytest.ini, narrow coverage, fix the AI_USAGE and ADR formats, use a fixture and add tests | Accepted | Added `pytest.ini`; moved the duplicated database setup into a `test_db` fixture in `tests/conftest.py`; added tests for cancelled/waitlisted students with a room and for an unknown trip; narrowed the README coverage command to `--cov=trip_statistics`; restructured `ADR.md` into `## N.` entries with `Status: Decided`, splitting domain scoping (2) from the schema (3); converted this table to the required columns. | Plain `pytest` failed because the project root wasn't on the import path, so `import trip_statistics` couldn't be found. `pythonpath = .` in `pytest.ini` fixes that. The `test_db` fixture in `conftest.py` creates a fresh database for each test, hands the connection to the test and closes it afterwards. `--cov=trip_statistics` measures only the logic module, so test files don't inflate the number. |

## Examples of decisions and modifications

**1. Database design**

I chose to keep cancelled registrations instead of deleting them, so registration history remains available. I also chose a partial unique index to prevent duplicate active registrations while allowing someone to register again after cancelling.

**2. Separation between domains**

I decided to keep Trip Management and Room Allocation separate. Room Allocation stores references to trip registrations as integer IDs, rather than using foreign keys across the domain boundary. This makes future separation easier, but means the application must validate these references itself.

**3. Dashboard implementation**

I wanted to add a dashboard showing useful statistics for ski trip organizers. ChatGPT helped me write the initial Python function and tests. I created the files in Cursor, ran the tests and committed the feature using Git.

**4. Development workflow**

Initially, I used Claude Code to help generate and commit the project skeleton and database schema. I then decided to work through subsequent features manually with ChatGPT guidance, so I could understand the implementation step by step and control the changes myself.

## Reflection

AI was particularly useful when I needed explanations of unfamiliar concepts, such as database schemas, SQLite constraints and pytest. It also helped me identify implementation details that I might otherwise have missed, such as allowing re-registration after cancellation.

One limitation is that generated code can appear correct without having been sufficiently tested or understood. For that reason, I used temporary databases and automated tests to check the dashboard calculations rather than relying only on the code importing successfully.

My main goal for the remaining development is to understand how the different parts of the application interact, particularly how trip registrations, room assignments and cancellations affect one another.

I will continue updating this document as I implement and test additional features.