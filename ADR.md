# Architecture Decision Records — Ski Club Manager

## 1. Use Flask with raw sqlite3

**Date:** 2026-10-11  
**Status:** Decided

**Context:** The club runs around four trips a season with about 150 students per trip, and usually only one or two organisers use the app at a time. The assignment also requires one process, one container and SQLite.

**Decision:** Use Flask for the web application and Python's built-in `sqlite3` module, with the database structure defined in `schema.sql` instead of using an ORM.

**Alternatives considered:** Django includes authentication, an admin interface and an ORM, but that would introduce more functionality than this project needs. FastAPI would make more sense for a JSON API, while this application mainly serves HTML pages. I also considered SQLAlchemy, but with five tables I preferred writing SQL directly so I could understand the queries and constraints.

**Consequences:** The application has few dependencies and the database is easy to inspect. The trade-off is that I have to write the SQL queries and validation myself.

## 2. Scope Trip Management and Room Allocation as separate domains

**Date:** 2026-10-11  
**Status:** Decided

**Context:** The application handles two different problems. Trip Management decides who gets a place, while Room Allocation decides where confirmed students stay. These responsibilities need to be separated so the application can be split into services in Assignment 2.

**Decision:** Trip Management owns `trips` and `registrations`. Room Allocation owns `rooms`, `room_assignments` and `roommate_preferences`.

Only trip IDs and registration IDs cross the boundary, together with the information needed to check whether a registration is confirmed.

There is one deliberate exception in `get_trip_statistics`, which joins registrations and room assignments to calculate dashboard statistics. This works because both domains currently share one database. In Assignment 2, the same information would need to come from the two services separately.

**Alternatives considered:** Putting everything in one large module would have been simpler initially, but registration and accommodation logic would become mixed together. That would make the later separation more difficult.

**Consequences:** Each domain has its own responsibilities and tables. However, cross-domain checks have to happen in Python, and some operations, such as cancelling a registration and releasing its room, require coordination between both domains.

## 3. Keep registration history and use plain IDs across the domain boundary

**Date:** 2026-10-11  
**Status:** Decided

**Context:** Students can cancel and register again, unpaid places are only reserved for 48 hours, and the waiting list must preserve registration order. The database also needs to respect the separation between the two domains.

**Decision:** Keep registrations in the database instead of deleting them. Their status can be `pending_payment`, `confirmed`, `waitlisted` or `cancelled`.

A partial unique index on `(trip_id, email)` applies only to active registrations. This prevents duplicate active registrations while allowing someone who cancelled to register again.

`registered_at` determines waiting-list order, while `payment_deadline` records when an unpaid reservation expires.

Foreign keys are used within each domain. References across the boundary, such as `room_assignments.registration_id`, are stored as plain integer IDs and checked by the application.

**Alternatives considered:** Deleting cancelled registrations would lose useful history. A normal unique constraint on trip and email would prevent students from registering again after cancellation. Cross-domain foreign keys would make the database harder to separate later.

**Consequences:** The application must check registration statuses carefully and validate cross-domain references itself. It also needs to distinguish between reserved places and confirmed payments when calculating statistics.

The addition of `pending_payment` required a small database upgrade in `db.init_db`, because `CREATE TABLE IF NOT EXISTS` does not change an existing table.

## 4. Prioritise tests for the business rules

**Date:** 2026-10-12  
**Status:** Decided

**Context:** The assignment requires at least 70% coverage of the core business logic. I wanted to focus testing on the parts where an error would actually affect students, rather than just trying to increase the percentage.

**Decision:** Use pytest with temporary SQLite databases and measure coverage across `trip_management.py`, `trip_statistics.py` and `room_allocation.py`.

I prioritised registration capacity, the 48-hour payment deadline, cancellations, FIFO waiting-list promotion and room assignments. These are connected operations, so an error in one can affect the others.

I also included a test where ten students try to register at the same time for a trip with only two places. This checks that the `BEGIN IMMEDIATE` transaction prevents overbooking.

**Alternatives considered:** I could have focused mainly on individual functions with simple inputs, which would have been quicker. However, I felt it was more useful to test complete workflows and cases where several rules interact. I also considered measuring coverage across every Python file, but chose to report the three core logic modules separately so the result would reflect the required business functionality.

**Consequences:** The latest test run passes 55 tests with 98% coverage across the core modules, above the 70% requirement.

This does not mean every possible case is covered. `room_allocation.py` is at 95%, with five lines still uncovered, and Flask routes are tested but not included in the reported coverage percentage. I accepted this because the most important business rules and integration cases are covered.

## 5. Leave out authentication and real payment processing

**Date:** 2026-10-12  
**Status:** Decided

**Context:** In a real ski club, organisers would probably need accounts and students might pay directly through the application. However, this assignment focuses on separating the two backend domains and delivering a working application in one container.

**Decision:** Do not implement user accounts, login or a payment provider.

Instead, the application is designed as a small organiser-facing tool. An organiser can record that a payment has been confirmed, but the application does not process or collect money.

I also chose not to add a background worker for expired payments. The application checks deadlines whenever a relevant registration, payment or cancellation operation takes place.

**Alternatives considered:** Adding Flask-Login and a users table would allow different access levels, but would introduce another area of functionality outside the two required domains. Connecting a real payment provider would require external credentials, payment security and webhook handling. A scheduled background job would make expiry more automatic, but would conflict with the assignment's single-process constraint.

**Consequences:** The application remains smaller and easier to understand and test. It is suitable for demonstrating the required workflows, but it is not intended to be deployed publicly without authentication and additional security measures.

Payment confirmation is also manual, and an expired reservation is not released until a relevant operation triggers the expiry check. These are limitations I accepted for this version.