# Architecture Decision Records — Ski Club Manager

## 1. Use Flask with raw sqlite3
Date: 2026-10-11
Status: Decided
Context: The club runs around four trips a season with about 150 students per trip, and only one or two organisers use the app at a time. The assignment also requires one process, one container and SQLite.
Decision: Use Flask to serve server-rendered HTML pages, and Python's built-in `sqlite3` module with the schema written by hand in `schema.sql` instead of an ORM.
Alternatives considered: Django brings authentication, an admin interface and an ORM, which is far more than five tables and two domains need. FastAPI is a better fit for a JSON API, but this app mainly serves HTML forms. SQLAlchemy was rejected because with five tables I preferred writing the SQL myself so I could see every query and constraint.
Consequences: Only one runtime dependency (Flask), and the database is easy to inspect with plain SQL. The cost is that I write every query and every validation check myself, with no ORM to catch mistakes.

## 2. Scope Trip Management and Room Allocation as separate domains
Date: 2026-10-11
Status: Decided
Context: The app solves two different problems: Trip Management decides who gets a place, and Room Allocation decides where confirmed students sleep. Assignment 2 will split them into separate services, so the seam has to exist now.
Decision: Trip Management (`trip_management.py`, `trip_statistics.py`) owns `trips` and `registrations`; Room Allocation (`room_allocation.py`) owns `rooms`, `room_assignments` and `roommate_preferences`. Only trip IDs, registration IDs and a registration's status cross the boundary.
Alternatives considered: One large module would have been quicker to write at first, but registration and accommodation rules would end up mixed in the same functions, making the Assignment 2 split a rewrite rather than a cut.
Consequences: Three things still cross the seam and would become API calls or messages after the split: `room_allocation.py` reads a registration's trip and status, but only through one adapter function, `_get_registration`, the cancellation event (Room Allocation subscribes with `on_registration_cancelled`, an Observer, so Trip Management never touches room tables), and `get_trip_statistics` joins registrations with room assignments for the dashboard.

## 3. Keep registration history and use plain IDs across the domain boundary
Date: 2026-10-11
Status: Decided
Context: Students can cancel and register again, unpaid places are only held for 48 hours, and the waiting list must keep registration order. The schema also has to respect the seam from ADR 2.
Decision: Registrations are never deleted; they move between `pending_payment`, `confirmed`, `waitlisted` and `cancelled`, with a partial unique index on `(trip_id, email)` that only applies to non-cancelled rows. Foreign keys are used inside each domain, but cross-domain references such as `room_assignments.registration_id` are plain integers checked in Python.
Alternatives considered: Deleting cancelled registrations would lose history. A normal `UNIQUE(trip_id, email)` would block a student from registering again after cancelling. Cross-domain foreign keys would tie the two domains together at the database level and break as soon as the tables live in different databases.
Consequences: The app has to validate cross-domain IDs itself and be careful to count `pending_payment` as a taken place but not as needing a room. Adding `pending_payment` later also needed a small table rebuild in `db.init_db`, because `CREATE TABLE IF NOT EXISTS` does not change an existing table's CHECK constraint.

## 4. Prioritise tests for the business rules
Date: 2026-10-12
Status: Decided
Context: The assignment requires at least 70% coverage of the core business logic, and I wanted the tests to target the rules whose failure would actually hurt students, not just raise the percentage.
Decision: Use pytest with a fresh temporary SQLite database per test, and measure coverage only on `trip_management.py`, `trip_statistics.py` and `room_allocation.py`, prioritising capacity, the 48-hour deadline, cancellation, FIFO waitlist promotion, room rules and a ten-thread overbooking test.
Alternatives considered: Simple one-function-at-a-time tests with fixed inputs would have reached 70% faster, but would miss the bugs that appear when rules interact (expiry triggering promotion, cancellation freeing a room). Measuring coverage over every file including `app.py` was rejected because it mixes framework glue into a number that is meant to describe business logic.
Consequences: 61 tests pass with 100% line coverage on the core modules. Flask routes are tested more thinly in `test_app.py` (one full workflow, form validation and trip-ownership checks) and kept out of the reported figure, and there are no tests for template rendering or styling.

## 5. Leave out authentication and real payment processing
Date: 2026-10-12
Status: Decided
Context: A real club would need organiser accounts and online payment, but this assignment is about two separable backend domains running in one container.
Decision: Build an organiser-only tool with no login, where an organiser records that a payment was received, and expire unpaid reservations inside normal requests instead of with a background job.
Alternatives considered: Flask-Login with a users table would add a third area of functionality outside the two required domains. A real payment provider would need external credentials and webhooks, which breaks the "no external dependency" rule. A scheduled background job would release expired places automatically, but needs a second process, which §1c rules out.
Consequences: The app stays small and fully testable, but must not be exposed publicly without authentication. An expired reservation is only released when the next registration, payment or cancellation on that trip runs `_release_expired`, so the dashboard can briefly show a stale count.
