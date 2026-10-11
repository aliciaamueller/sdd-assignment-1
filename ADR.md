# Architecture Decision Records for Alicia Mueller Reglero's Ski Club Manager

## ADR-1: Use Flask and SQLite
**Date:** 2026-10-11  
**Status:** Accepted

**Context:**  
I needed to choose a framework and database for a small ski trip management application. The application needs to handle registrations, waiting lists, rooms and student preferences without becoming unnecessarily complicated.

**Decision:**  
I chose Flask for the web application and SQLite for storing data. Flask is lightweight and allows me to build the application using Python, while SQLite works without needing a separate database server.

**Alternatives considered:**  
I considered Django, but it includes more functionality than this project currently needs. PostgreSQL was another database option, but it would require additional setup.

**Consequences:**  
The application is easier to develop, test and run inside one Docker container. However, SQLite is less suitable for applications with many concurrent users, and Flask requires me to implement more functionality myself.

---

## ADR-3: Separate Trip Management and Room Allocation
**Date:** 2026-10-11  
**Status:** Accepted

**Context:**  
The application has two main responsibilities: managing trip registrations and managing room allocations. I wanted to keep these responsibilities separate because they follow different business rules.

**Decision:**  
Trip Management owns the `trips` and `registrations` tables. Room Allocation owns `rooms`, `room_assignments` and `roommate_preferences`.

I decided to use foreign keys within each domain, but store plain integer IDs when Room Allocation refers to Trip Management data. The application will validate these cross-domain references in Python.

**Alternatives considered:**  
I could have used foreign keys between every related table. This would have allowed SQLite to enforce more relationships automatically, but would also have created stronger dependencies between the two domains.

**Consequences:**  
The domains are easier to separate in a future version of the application. However, Room Allocation must check that registrations and trips exist, and that students are confirmed for the correct trip. These rules need automated tests because the database does not enforce them across the domain boundary.