-- Ski Club Manager schema.
-- Runs on every startup, so every statement must be safe to repeat:
-- IF NOT EXISTS only creates what is missing. Nothing is ever dropped.

-- =====================================================================
-- Domain 1: Trip Management
-- Owns trips and who has signed up for them.
-- =====================================================================

CREATE TABLE IF NOT EXISTS trips (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    destination TEXT    NOT NULL,
    start_date  TEXT    NOT NULL,  -- ISO date, e.g. 2027-01-15
    end_date    TEXT    NOT NULL,
    capacity    INTEGER NOT NULL CHECK (capacity > 0)
);


CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE,
    status TEXT NOT NULL
        CHECK (status IN (
            'pending_payment',
            'confirmed',
            'waitlisted',
            'cancelled'
        )),
    registered_at TEXT NOT NULL,
    payment_deadline TEXT
);


-- One active registration per email per trip.
-- Cancelled rows are left out, so a cancelled person can register again.
CREATE UNIQUE INDEX IF NOT EXISTS idx_registrations_active_email
    ON registrations (trip_id, email)
    WHERE status IN ('pending_payment', 'confirmed', 'waitlisted');

-- =====================================================================
-- SEAM: everything below belongs to Room Allocation.
-- It refers to trips and registrations by plain integer IDs only,
-- with no foreign keys across this line, so it could move to its own
-- service and database in Assignment 2 without changing these tables.
-- =====================================================================

-- =====================================================================
-- Domain 2: Room Allocation
-- Owns rooms, who sleeps where, and roommate requests.
-- =====================================================================

CREATE TABLE IF NOT EXISTS rooms (
    id       INTEGER PRIMARY KEY,
    trip_id  INTEGER NOT NULL,  -- trip ID from Trip Management, no FK
    name     TEXT    NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity BETWEEN 1 AND 6),
    UNIQUE (trip_id, name)
);

CREATE TABLE IF NOT EXISTS room_assignments (
    id              INTEGER PRIMARY KEY,
    room_id         INTEGER NOT NULL REFERENCES rooms(id),
    registration_id INTEGER NOT NULL UNIQUE  -- one room per person, no FK
);

CREATE TABLE IF NOT EXISTS roommate_preferences (
    id                        INTEGER PRIMARY KEY,
    registration_id           INTEGER NOT NULL,  -- who is asking, no FK
    preferred_registration_id INTEGER NOT NULL,  -- who they want, no FK
    CHECK (registration_id != preferred_registration_id),
    UNIQUE (registration_id, preferred_registration_id)
);
