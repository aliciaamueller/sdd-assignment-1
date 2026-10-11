# AI Usage Log — Ski Club Manager

**Student:** Alicia Mueller Reglero  
**Assignment:** Software Development and DevOps — Individual Assignment 1

## How I used AI

I used Claude Code and ChatGPT as development assistants during this assignment. AI helped me understand unfamiliar concepts, plan the application, generate some initial code and troubleshoot errors.

I also worked directly in Cursor, created files, ran tests, reviewed outputs and used Git commands to commit and push changes.

Below is a record of the main AI interactions so far.

## AI Usage Log

| Task | AI tool | How I used it | Outcome |
|---|---|---|---|
| Project planning | ChatGPT | Discussed the Ski Club Manager idea, its two domains and which features would be realistic for the assignment. | Chose Trip Management and Room Allocation, with Flask and SQLite. |
| Dependencies | Claude Code | Asked for a `requirements.txt` containing Flask, pytest and pytest-cov. | Accepted the dependency setup. |
| Project skeleton | Claude Code | Requested the initial Flask application, environment-based configuration and SQLite connection helper. | Accepted the initial implementation after checking the files and basic setup. |
| Database schema | Claude Code | Provided specific requirements for five tables, database constraints, domain boundaries and initialization. | Accepted the schema after Claude reported successful checks for duplicate registrations, cancellations and repeated initialization. |
| Coding style reference | ChatGPT | Reviewed examples from my previous Software Design and Development assignment to establish a familiar level of Python complexity. | Used these as references for readability and testing, without copying unnecessary design patterns. |
| Dashboard statistics | ChatGPT | Requested help creating a function to calculate trip capacity, confirmed registrations, waiting lists and room allocation statistics. | Added `trip_statistics.py` manually in Cursor. |
| Dashboard tests | ChatGPT | Followed instructions for writing pytest tests using a temporary SQLite database. | Created two tests and verified that both passed locally. |
| Python environment | ChatGPT | Asked for help after pytest was not found in my Python environment. | Created a virtual environment, installed the project dependencies and successfully ran pytest. |
| Architecture decisions | ChatGPT | Requested draft ADR entries explaining the framework choice and separation between Trip Management and Room Allocation. | Used the drafts as a starting point for `ADR.md`, subject to review and editing. |
| AI usage documentation | ChatGPT | Requested help organizing and drafting this AI usage log. | Used the draft as a starting point and checked it against the actual development process. |

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