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
| Before `5349d00` | Claude / ChatGPT | Help plan a Ski Club Manager with two backend domains and a small SQLite database. | Accepted | Defined the project around Trip Management and Room Allocation. | The two domains handle different rules, even though they run in the same application. This should make separating them in Assignment 2 easier. |
| `b8d66d3` | Claude Code | Create a requirements file for Flask and the testing tools. | Accepted | Added `requirements.txt` with pinned dependencies. | The same versions are installed locally and when Docker builds the application. |
| `5349d00` | Claude Code | Set up the initial Flask application, configuration and SQLite connection helper. | Accepted | Created the project skeleton and environment-based configuration. | `config.py` reads settings such as `PORT` and `DATA_DIR`. `db.py` opens the SQLite database, and Flask listens on `0.0.0.0` so the container can be reached from outside. |
| `ae6b4fa` | Claude Code | Create the five database tables and constraints, keeping the two domains separate. | Accepted | Added `schema.sql`, including the partial unique index for active registrations. | The database prevents someone from having two active registrations for the same trip, but a cancelled student can register again. |
| `65a3a66` | ChatGPT | Help calculate trip statistics and test them using a temporary database. | Accepted | Added `trip_statistics.py` and its initial tests. | The function reads the trip and registrations, calculates availability and counts room assignments. The tests use temporary databases so they don't change real data. |
| `2954989` | ChatGPT | Help draft architecture decisions and organise the AI usage log. | Modified | Created the first documentation entries, which were later reorganised to match the assignment format. | The ADRs explain why I chose an approach, what alternatives I considered and what consequences it has. |
| `ecb6482` | Claude Code | Review the test setup and documentation against the assignment requirements. | Accepted | Added `pytest.ini`, a shared database fixture and additional tests, and restructured the documentation. | The fixture creates a fresh test database for each test. `pytest.ini` lets the tests import the project modules correctly. |
| `8172426`, `046b54e` | ChatGPT / Claude Code | Implement trip creation and improve validation tests. | Accepted | Added trip creation rules and tests for invalid names, dates and capacity values. | Invalid trip information is rejected before it is saved to the database. |
| `d1d30bc` | Claude Code | Complete the Dockerfile using the provided template and run the contract checker. | Accepted | Added the root `Dockerfile`, documented the container setup and checked that it builds and runs. | Docker needs the application modules and `schema.sql` inside the image. The database stays outside the image in a persistent volume. |
| `e53dd2c` | ChatGPT / Claude Code | Implement student registration with payment reservations and a first-come, first-served waiting list. | Accepted | Added registration statuses, 48-hour reservations and waiting-list logic. | `register_student` checks whether a place is available. It uses `BEGIN IMMEDIATE` before checking capacity so two requests cannot reserve the same final place. If the trip is full, the student joins the waiting list. |
| `49f1eb5` | Claude Code | Fix the dashboard statistics so unpaid reservations also count as occupied places. | Accepted | Updated `get_trip_statistics` to count pending payments when calculating remaining capacity. | A student who hasn't paid yet still holds a place for 48 hours. That place should not appear as available, although the student should not yet count as needing a room. |
| `1fd467e` | Claude Code | Complete payment expiry, cancellation and room allocation, with integration tests. | Accepted | Added the complete payment lifecycle and room management functionality. | When a reservation expires or is cancelled, the place becomes available to the next waitlisted student. Room assignments are checked against the student's trip and confirmed registration status. Cancelling also releases an existing room assignment. |
| `2c92af2` | Claude Code | Add a simple web interface so organisers can use the application without running Python functions manually. | Accepted | Added Flask routes, HTML templates and CSS. | The routes receive form inputs, call the existing domain functions and display the results. The business rules remain in the Python modules rather than being duplicated in the templates. |
| `c17e9e1` | Claude Code | Review form validation, prevent actions on records from another trip and test simultaneous registrations. | Accepted | Improved error handling, checked trip ownership in routes and added route and concurrency tests. | An ID submitted through a form cannot be trusted on its own. The route must check that the registration or room belongs to the trip being managed. The concurrency test checks that the database cannot overbook a trip. |
| `803f684` | Claude Code | Improve the trip page layout and mobile usability without changing the business logic. | Modified | Reordered the page, shortened date displays, improved spacing and made registration actions easier to use on smaller screens. | These changes affect how information is displayed, not how places or rooms are allocated. Keeping presentation separate from business logic makes the application easier to maintain. |
| `98d9911` | ChatGPT | Review and rewrite the README to make it clearer, less repetitive and more specific to the project. | Modified | Updated the project introduction, architecture explanation, testing evidence and file descriptions. | The README explains what the application does and how to run it, while the ADRs and separate report explain the engineering decisions in more detail. |
| Final documentation update | ChatGPT | Review the missing ADR entries and update the AI usage log to reflect the completed application. | Modified | Added the testing-strategy and deliberate-omission decisions, and brought the development record up to date. | The testing decision explains which risks I prioritised. The omission decision explains why I left out authentication and real payment processing instead of adding features that were not required. |

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

The final implementation has 55 passing tests and 98% coverage across the three core business-logic modules. The Docker contract checker also passes.

The most useful thing I learned was how much the different rules depend on one another. Registration capacity affects payments, payments affect waiting lists, and cancellations can also affect room assignments. Keeping those responsibilities separate in the code made the application easier to understand and test.

I used AI as a development assistant, but I also needed to review the results, check the behaviour and understand the design decisions well enough to explain them.