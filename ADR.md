# Architecture Decision Records

These five entries record the application's main architecture and scope decisions.

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
Decision: Treat saved restaurant facts and filtering as the restaurant collection domain; treat visits, orders, ratings, notes, and bills as the dining-history domain. Connect a visit to `saved_restaurants.id` and keep the business rules in separate modules.
Alternatives considered: A single restaurant record with one rating, bill, and notes would be smaller, but it would lose the history of repeat visits and make the domains indistinct.
Consequences: The split gives a clear later service boundary. The personal-rating filter reads `saved_restaurants.rating` within the restaurant collection; any future analysis of visit ratings would need a deliberate cross-domain read.

## 3. Implement the supplied single-user SQLite schema
Date: 2026-09-30
Status: Decided
Context: The 2026-09-29 scaffold used three tables and embedded bill bytes. The student then supplied a more detailed single-user schema separating general restaurant facts, personal saved details, visits, bills, items, images, and emails.
Decision: Implement those seven tables in `database/schema.sql` with foreign keys and cascade rules, using `DATA_DIR/devops_food.sqlite3` for SQLite. Keep bill file locations in `bills.image_path` as supplied, with uploaded files under `DATA_DIR/bills`.
Alternatives considered: The original three-table design would keep one persistent file, but it cannot represent separate general and personal ratings or multiple images, emails, and bill records without changing its structure.
Consequences: The diagram matches the schema and each feature domain has clear table ownership. Backups need both SQLite and the bill files; money stored as `REAL` would need rounding rules if payment calculations were added.

## 4. Test both domains with temporary SQLite databases
Date: 2026-10-04
Status: Decided
Context: The assignment requires at least 70% coverage of core business logic in both domains. The app also has Flask routes and a public address lookup, but those are not the main coverage target.
Decision: Test restaurant and dining-history functions against an isolated temporary SQLite database, then add a few Flask route tests for the forms. Mock the external address lookup in tests so they run offline.
Alternatives considered: Browser-only tests would show the page flow but would make domain failures harder to locate and would not directly measure the required business logic coverage.
Consequences: The measured domain coverage is 97%, with repeatable tests that do not alter the user's database. This does not prove every browser interaction or every external map result is correct.

## 5. Keep authentication out of this local single-user version
Date: 2026-10-04
Status: Decided
Context: The schema deliberately has no `users` table, and the assignment asks for a minimal single-process app to run locally. Personal notes and bills would need access control before public use.
Decision: Do not build login or multiple accounts for Assignment 1; keep this version for a trusted local user.
Alternatives considered: Adding accounts now would protect private records on a shared server, but it would require user storage, session management, and more security testing outside the agreed scope.
Consequences: The app must not be exposed publicly with real private notes or bills. Authentication and data separation would be needed before a multi-user release.
