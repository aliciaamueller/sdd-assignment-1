# Architecture Decision Records — Ski Club Manager

## 1. Use Flask with raw sqlite3
Date: 2026-10-11
Status: Decided
Context: The club runs around 4 trips a season with about 150 students per trip, and one or two organisers use the app at a time. It has to run as one process in one container, and SQLite is required.
Decision: Flask for the web layer, and Python's built-in `sqlite3` module with hand-written SQL in `schema.sql` instead of an ORM.
Alternatives considered: Django, rejected because its admin, auth and ORM are more than this app needs and its migrations would replace the plain `schema.sql`. FastAPI, rejected because the app serves HTML pages to organisers rather than a JSON API, so its main strengths go unused. SQLAlchemy as an ORM, rejected because with five tables the raw SQL is short and I can see exactly which constraints exist.
Consequences: Few dependencies and a schema I can read in one file. In exchange I write the queries and the input validation myself.

## 2. Scope Trip Management and Room Allocation as separate domains
Date: 2026-10-11
Status: Decided
Context: The app has two jobs with different rules: deciding who gets a place on a trip (capacity, waitlist, cancellation) and deciding who sleeps where (room capacity, roommate requests). Assignment 2 splits the app into services, so the seam has to exist now.
Decision: Trip Management owns `trips` and `registrations`. Room Allocation owns `rooms`, `room_assignments` and `roommate_preferences`. Only trip IDs and registration IDs cross the seam, plus Room Allocation needs to know whether a registration is confirmed. The one deliberate crossing is `get_trip_statistics` in `trip_statistics.py`, which JOINs `room_assignments` with `registrations` in one SQL query. That works only because both domains share one database. In Assignment 2 it becomes two calls: Trip Management returns the confirmed registrations, and Room Allocation returns the assignments for them.
Alternatives considered: One "trips" module that does everything, rejected because cancelling a registration and freeing a room would get tangled together and could not be split later without rewriting.
Consequences: Room Allocation can be moved out later without changing its tables. The cost is that cross-domain checks (is this registration confirmed and on this trip?) happen in Python, not in the database.

## 3. Keep history with a status column, link across the seam by plain IDs
Date: 2026-10-11
Status: Decided
Context: Students cancel and re-register, and the waitlist needs to know who came first. The schema also has to respect the seam from entry 2.
Decision: A registration is never deleted. `status` is one of `confirmed`, `waitlisted` or `cancelled` (enforced by a CHECK), and `registered_at` orders the waitlist. A partial unique index on `(trip_id, email)` with `WHERE status IN ('confirmed', 'waitlisted')` allows only one active registration per email per trip, so a cancelled student can sign up again. Foreign keys are used inside a domain (`registrations.trip_id` → `trips`, `room_assignments.room_id` → `rooms`), but `rooms.trip_id`, `room_assignments.registration_id` and both columns in `roommate_preferences` are plain integers with no foreign key. CHECK constraints guard `trips.capacity > 0`, room capacity between 1 and 6, and that nobody lists themselves as a preferred roommate.
Alternatives considered: Deleting cancelled rows, rejected because it loses history and the waitlist order. A plain UNIQUE on `(trip_id, email)`, rejected because it would block re-registration after cancelling. Foreign keys across the seam, rejected because they would tie Room Allocation's tables to Trip Management's database.
Consequences: Every query has to filter by `status`, which is why `get_trip_statistics` only counts room assignments for confirmed registrations. SQLite cannot catch a room assignment that points at a missing registration, so that check needs code and tests.
