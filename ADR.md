# Architecture Decision Records

These entries record decisions made for the scaffold. Entries 4 and 5 will be added when the relevant choices are actually made, on later dates. The final submission must have exactly five entries spanning at least three distinct commit dates.

## 1. Use Python and Flask for the single-process app
Date: 2026-09-29
Status: Decided
Context: The assignment calls for a small monolith that the student can explain in a closed-book check. The student said Python and Flask are a comfortable stack.
Decision: Use one Flask process for the web interface and Python's built-in `sqlite3` for persistence. Serve the frontend from Flask instead of running a separate frontend server.
Alternatives considered: FastAPI was considered, but this project does not need its asynchronous API model and a switch would add learning work unrelated to the assignment.
Consequences: The deployment command is simple and third-party dependency count stays low. We must write our own input validation and SQL access code as features are added.

## 2. Separate restaurant collection from dining history
Date: 2026-09-29
Status: Decided
Context: The approved idea includes saved restaurants and records of actual visits, and the assignment requires two distinct SQLite-backed domains. A restaurant can exist before any visit, while a visit only makes sense for a saved restaurant.
Decision: Treat saved restaurant facts and filtering as the restaurant collection domain; treat visits, orders, ratings, notes, and bills as the dining-history domain. Connect them by restaurant ID and keep their business rules in separate modules when implemented.
Alternatives considered: A single restaurant record with one rating, bill, and notes would be smaller, but it would lose the history of repeat visits and make the domains indistinct.
Consequences: The split gives a clear later service boundary. Rating-based restaurant filtering will need a read-only view of visit ratings, which is a deliberate cross-domain query to isolate when that feature is built.

## 3. Put restaurants, visits, orders, and bills in one SQLite file
Date: 2026-09-29
Status: Decided
Context: The deployment contract requires SQLite at one documented path, and the app must preserve multiple visits and their ordered items. Bill uploads should not introduce another required storage service.
Decision: Store `restaurants`, `visits`, and `ordered_items` as separate tables with foreign keys. Keep a bill's filename, media type, and bytes on its visit row; use `DATA_DIR/devops_food.sqlite3` as the only persistent file.
Alternatives considered: Saving uploaded bills as separate files would keep the database smaller, but it would create a second persistent path and make backup and container volume setup more complicated.
Consequences: One SQLite file is easy to run and back up, and each visit can have multiple orders. Bill size and file-type limits must be enforced before uploads are implemented so the database does not grow without bound.
