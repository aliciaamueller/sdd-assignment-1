# AI Usage Log — Ski Club Manager

**Student:** Alicia Mueller Reglero  
**Assignment:** Software Development and DevOps — Individual Assignment 1

## How I used AI

I used ChatGPT and Claude Code throughout this assignment, mainly to plan the application, understand unfamiliar concepts, review code, generate parts of the implementation and identify problems through testing.

I worked in Cursor to inspect the files, run the application and tests, review changes and manage the Git repository.

I wanted to keep the Python code relatively simple and similar to the style used in my previous Software Development coursework. I therefore asked for readable functions, straightforward conditions and no unnecessary design patterns.

The log below records the main interactions. Where I no longer have the exact wording of a prompt, I have summarised the request rather than presenting it as a direct quotation.

## AI Usage Log

| Date / Commit | Tool | Prompt or request (summarised) | Disposition | What changed and why | How I understand it |
|---|---|---|---|---|---|
| Before `5349d00` | Claude / ChatGPT | Help plan a Ski Club Manager with two backend domains and a small SQLite database. | Accepted | Defined the project around Trip Management and Room Allocation. | Trip Management owns `trips` and `registrations` and decides who gets a place; Room Allocation owns `rooms`, `room_assignments` and `roommate_preferences` and decides where confirmed students sleep. The only thing Room Allocation needs from the other side is a registration's ID, trip and status, so that is where the Assignment 2 cut goes. |
| `b8d66d3` | Claude Code | Create a requirements file for Flask and the testing tools. | Accepted | Added `requirements.txt` with pinned dependencies. | Every package is pinned with `==` (`flask==3.1.3`, `pytest==9.1.1`, `pytest-cov==7.1.0`), so `pip install -r requirements.txt` installs exactly the same versions on my laptop and in the Docker image. Only Flask is needed at runtime; the other two are for testing. |
| `5349d00` | Claude Code | Set up the initial Flask application, configuration and SQLite connection helper. | Accepted | Created the project skeleton and environment-based configuration. | `config.py` reads `PORT` (default 8000), `DATA_DIR` (default `./data`) and `SECRET_KEY` with `os.environ.get`, and builds `DB_PATH` as `DATA_DIR/ski_club.db`. `get_connection` in `db.py` opens that file, sets `row_factory = sqlite3.Row` so I can read `row["name"]`, and turns on `PRAGMA foreign_keys`, which SQLite leaves off by default. `app.run` binds `0.0.0.0` so requests from outside the container reach it. |
| `ae6b4fa` | Claude Code | Create the five database tables and constraints, keeping the two domains separate. | Accepted | Added `schema.sql`, including the partial unique index for active registrations. | `idx_registrations_active_email` is a unique index on `(trip_id, email)` with `WHERE status IN ('pending_payment', 'confirmed', 'waitlisted')`, so it only checks non-cancelled rows. A second active registration raises `sqlite3.IntegrityError`, which `register_student` turns into "Student already registered", but a cancelled row is ignored so the student can sign up again. |
| `65a3a66` | ChatGPT | Help calculate trip statistics and test them using a temporary database. | Accepted | Added `trip_statistics.py` and its initial tests. | `get_trip_statistics` runs separate `COUNT(*)` queries for `confirmed`, `pending_payment` and `waitlisted`, then counts room assignments by joining `room_assignments` to `registrations` and `rooms` for the same trip. `places_remaining` is capacity minus confirmed plus pending, and `need_room` is confirmed minus assigned. The `test_db` fixture points `DB_PATH` at a temporary file, so tests never touch real data. |
| `2954989` | ChatGPT | Help draft architecture decisions and organise the AI usage log. | Modified | Created the first documentation entries, which were later reorganised to match the assignment format. | The first drafts covered the Flask choice and the domain split. I kept the reasoning (Django too big, raw SQL so I can see the queries) but later rewrote them in the exact Context / Decision / Alternatives / Consequences format the brief asks for. |
| `ecb6482` | Claude Code | Review the test setup and documentation against the assignment requirements. | Accepted | Added `pytest.ini`, a shared database fixture and additional tests, and restructured the documentation. | The `test_db` fixture in `conftest.py` uses pytest's `tmp_path` and `monkeypatch` to point `db.DB_PATH` at a new file, runs `init_db()`, and yields a connection, so every test starts from an empty schema. `pythonpath = .` in `pytest.ini` lets `tests/` import `trip_management` and the other root modules. |
| `8172426`, `046b54e` | ChatGPT / Claude Code | Implement trip creation and improve validation tests. | Accepted | Added trip creation rules and tests for invalid names, dates and capacity values. | `create_trip` raises `ValueError` for an empty name or destination, dates that are not ISO `YYYY-MM-DD`, an end date before the start date, or a capacity that is not a positive integer, all before the `INSERT`. The Flask route catches the `ValueError` and shows it as a flash message. |
| `d1d30bc` | Claude Code | Complete the Dockerfile using the provided template and run the contract checker. | Accepted | Added the root `Dockerfile`, documented the container setup and checked that it builds and runs. | Docker needs the application modules and `schema.sql` inside the image. The database stays outside the image in a persistent volume. |
| `e53dd2c` | ChatGPT / Claude Code | Implement student registration with payment reservations and a first-come, first-served waiting list. | Accepted | Added registration statuses, 48-hour reservations and waiting-list logic. | `register_student` starts with `BEGIN IMMEDIATE`, which takes SQLite's write lock before reading anything, so a second request waits instead of reading the same count. It calls `_release_expired` first, then counts `pending_payment` + `confirmed` rows. If that is below `capacity`, the new row is `pending_payment` with `payment_deadline = now + PAYMENT_WINDOW` (48 h); otherwise it is `waitlisted` with no deadline. |
| `49f1eb5` | Claude Code | Fix the dashboard statistics so unpaid reservations also count as occupied places. | Accepted | Updated `get_trip_statistics` to count pending payments when calculating remaining capacity. | A student who hasn't paid yet still holds a place for 48 hours. That place should not appear as available, although the student should not yet count as needing a room. |
| `1fd467e` | Claude Code | Complete payment expiry, cancellation and room allocation, with integration tests. | Accepted | Added the complete payment lifecycle and room management functionality. | `_release_expired` sets every `pending_payment` row whose `payment_deadline` has passed to `cancelled`, then calls `_promote_waitlist`, which works out the free places and moves that many `waitlisted` rows, ordered by `registered_at, id`, to `pending_payment` with a fresh 48-hour deadline. `confirm_payment` runs the expiry first, so a late payment is refused. `cancel_registration` marks the row `cancelled`, deletes its `room_assignments` row and promotes the next student. `assign_student` refuses non-confirmed students, a room on another trip, or a full room. |
| `2c92af2` | Claude Code | Add a simple web interface so organisers can use the application without running Python functions manually. | Accepted | Added Flask routes, HTML templates and CSS. | Each POST route reads the form, converts numbers with `form_int`, and calls one domain function through `handle_action`, which catches `ValueError` and flashes its message as an error (or flashes the success message); the route then redirects back to the trip page. The routes never decide capacity or room rules themselves; they only call `register_student`, `confirm_payment`, `assign_student` and so on. |
| `c17e9e1` | Claude Code | Review form validation, prevent actions on records from another trip and test simultaneous registrations. | Accepted | Improved error handling, checked trip ownership in routes and added route and concurrency tests. | A registration ID in a form could belong to any trip, so routes call `check_registration_on_trip` and `check_room_on_trip`, which raise `ValueError` if the ID is not on the trip in the URL. The concurrency test starts ten threads calling `register_student` on a two-place trip and asserts exactly two `pending_payment` and eight `waitlisted` rows. |
| `803f684` | Claude Code | Improve the trip page layout and mobile usability without changing the business logic. | Modified | Reordered the page, shortened date displays, improved spacing and made registration actions easier to use on smaller screens. | These changes affect how information is displayed, not how places or rooms are allocated. Keeping presentation separate from business logic makes the application easier to maintain. |
| `98d9911` | ChatGPT | Review and rewrite the README to make it clearer, less repetitive and more specific to the project. | Modified | Updated the project introduction, architecture explanation, testing evidence and file descriptions. | The README explains what the application does and how to run it, while the ADRs and separate report explain the engineering decisions in more detail. |
| `aa92de8` | ChatGPT | Review the missing ADR entries and update the AI usage log to reflect the completed application. | Modified | Added the testing-strategy and deliberate-omission decisions, and brought the development record up to date. | The testing decision explains which risks I prioritised. The omission decision explains why I left out authentication and real payment processing instead of adding features that were not required. |
| `63163b4` | Claude Code | Find which lines in the core modules are still uncovered and add tests for them. | Accepted | Added four tests in `test_room_allocation.py`; `room_allocation.py` went from 95% to 100%. | The five missed lines were all error branches: an empty room name, `assign_student` with an unknown room or registration, `add_roommate_preference` where the preferred student does not exist (`len(students) != 2`), and `get_rooms` for a missing trip. Each test calls the function with a bad ID and checks the `ValueError` message. |
| `f3330eb` | Claude Code | Check my ADR log against the format in the brief and fix whatever does not match. | Modified | Rewrote all five entries in the exact field format with 1-2 sentence decisions. I kept my original reasoning and asked for the seam crossings to be named explicitly. | ADR 2 now lists the three places that currently cross the domain seam through the shared database: `room_allocation.py` reading `registrations`, `cancel_registration` deleting from `room_assignments`, and the join in `get_trip_statistics`. These would become API calls in Assignment 2. |

## Examples of decisions and modifications

### 1. Keeping the database design practical

I wanted cancellations to remain visible instead of deleting registration records. This is why the database uses statuses and a partial unique index. The index prevents duplicate active registrations but still allows someone to register again after cancelling.

I also kept foreign keys within each domain rather than connecting the two domains directly through the database.

### 2. Making the payment and waiting-list logic consistent

One important issue was that an unpaid registration still reserves a place. Initially, the dashboard statistics did not reflect this correctly.

The calculation was updated so `pending_payment` counts toward occupied capacity, while room allocation only counts confirmed students.

This helped me understand that two parts of an application can work separately but still produce inconsistent results if they interpret the same status differently.

### 3. Testing more than the expected cases

I wanted to test situations where the application might fail, not just whether a normal registration succeeds.

The simultaneous-registration test was particularly useful. It checks that ten students trying to register for two places cannot cause overbooking. This is why the database transaction matters, even in a relatively small application.

### 4. Keeping the Python readable

I used examples from my earlier coursework as a reference for code style. I preferred functions with clear names, simple conditions and direct SQL over adding more classes or design patterns.

I also kept Flask routes separate from the domain logic, so the web interface does not become responsible for deciding who gets a place or a room.

### 5. Improving the interface without adding unnecessary features

The first web interface worked, but the trip page contained a lot of information. I used AI feedback to reorganise the page and improve the mobile layout.

I chose to focus on making existing features easier to use rather than adding more functionality close to the deadline.

## Reflection

AI was useful throughout this project, especially for understanding SQLite constraints, database transactions, test coverage and how the different parts of the application should interact.

It also helped me move faster when setting up Flask, Docker and the web interface. At the same time, I found that generating code quickly does not automatically mean the result is correct. For example, the initial statistics calculation did not treat unpaid reservations as occupied places, even though the registration logic did.

Testing helped identify these inconsistencies and gave me a way to check that changes had not broken existing functionality.

The final implementation has 59 passing tests and 100% line coverage across the three core business-logic modules. The Docker contract checker also passes.

The most useful thing I learned was how much the different rules depend on one another. Registration capacity affects payments, payments affect waiting lists, and cancellations can also affect room assignments. Keeping those responsibilities separate in the code made the application easier to understand and test.

I used AI as a development assistant, but I also needed to review the results, check the behaviour and understand the design decisions well enough to explain them.