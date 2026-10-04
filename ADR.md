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
Consequences: The split gives a clear later service boundary. The personal-rating filter reads `saved_restaurants.rating` within the restaurant collection; any future analysis of visit ratings would need a deliberate cross-domain read.

## 3. Implement the supplied single-user SQLite schema
Date: 2026-09-30
Status: Decided
Context: The 2026-09-29 scaffold used three tables and embedded bill bytes. The student then supplied a more detailed single-user schema separating general restaurant facts, personal saved details, visits, bills, items, images, and emails.
Decision: Implement those seven tables in `database/schema.sql` with foreign keys and cascade rules, using `DATA_DIR/devops_food.sqlite3` for SQLite. Keep bill file locations in `bills.image_path` as supplied, with uploaded files planned under `DATA_DIR`.
Alternatives considered: The original three-table design would keep one persistent file, but it cannot represent separate general and personal ratings or multiple images, emails, and bill records without changing its structure.
Consequences: The diagram now matches the student's schema and each feature domain has clear table ownership. Bill uploads will need a documented file path and backup alongside SQLite, and money stored as `REAL` may need rounding rules when payment calculations are implemented.
