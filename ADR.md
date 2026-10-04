# Architecture Decision Records

These five entries explain decisions made while building the Assignment 1 app. Their original decision dates are kept so the record shows when each choice was made.

## 1. Use Python and Flask for the single-process app
Date: 2026-09-29
Status: Decided
Context: The assignment requires one process that starts quickly, serves the interface, and can later run in one container. I already know Python and Flask well enough to explain the request flow and database code in the written check.
Decision: Use Flask routes and server-rendered HTML in one Python process, with the standard-library `sqlite3` module for storage. Start it with `python app.py`, bind to `0.0.0.0`, and read `PORT` from the environment.
Alternatives considered: FastAPI would also work, but its asynchronous API focus does not help these small form submissions or SQLite queries. A separate frontend server would add another process and break the assignment's simple deployment shape.
Consequences: Flask, templates, and SQLite need only one application process and a short dependency list. I must maintain SQL queries, validation, and form error handling myself; there is no larger framework doing those parts automatically.

## 2. Separate restaurant collection from dining history
Date: 2026-09-29
Status: Decided
Context: The approved idea has two different jobs: keeping a catalog and personal saved list, and recording what happened on individual visits. A restaurant can be listed without a visit, but a visit belongs to a saved restaurant; the assignment also requires two distinct SQLite-backed domains.
Decision: Keep catalog, saved-entry, location, and filter rules in `backend/restaurant_domain.py`; keep visits, ordered items, and bills in `backend/dining_history.py`. Use `saved_restaurants.id` as the link and let Flask routes call the two modules.
Alternatives considered: Putting the latest visit, bill, and one rating directly on a restaurant row would use fewer tables and functions. It would lose repeat-visit history and make the two responsibilities harder to separate later.
Consequences: Each module has its own main tables and can be tested independently, giving a concrete boundary for a future service split. Recording a visit currently also marks its saved entry `visited` in the same SQLite transaction; if the domains become separate services, that status update will need an explicit cross-service operation.

## 3. Implement the supplied single-user SQLite schema
Date: 2026-09-30
Status: Decided
Context: The first scaffold had three tables and stored bill bytes in SQLite. I then supplied a seven-table, single-user schema so general restaurant facts, my saved details, visits, items, bills, images, and emails could have separate relationships.
Decision: Implement my schema in `database/schema.sql` and create one database at `DATA_DIR/devops_food.sqlite3`. Make `saved_restaurants.restaurant_id` unique, link visits through `saved_restaurants.id`, enable foreign keys on each connection, and store uploaded bill files under `DATA_DIR/bills/` with paths in the `bills` table.
Alternatives considered: Keeping the three-table scaffold and bill bytes in SQLite would make backup a single-file operation, but it cannot represent the separate personal record and repeated visit data cleanly. Adding a `users` table was unnecessary for this one-person version.
Consequences: Unsaved restaurants can stay in the catalog, and deleting a saved entry cascades to its visits, items, and bill rows; the app also removes the matching managed bill files. Backups must include both the database and bill directory, and an older scaffold database needs a migration or a fresh `DATA_DIR`; the app does not silently reshape it.

## 4. Test both domains with temporary SQLite databases
Date: 2026-10-04
Status: Decided
Context: The assignment measures coverage of the two domains' core logic and requires at least 70%. Validation, filtering, cascade deletion, and visit ownership depend on real SQL behavior, while a public address service could make tests slow or unreliable.
Decision: Test domain functions against a new temporary SQLite database for each test and measure `backend.restaurant_domain` and `backend.dining_history` with `pytest-cov`. Add a smaller set of Flask form tests and mock address lookup so the suite runs offline.
Alternatives considered: Browser-only testing would exercise the visible flow but make failed business rules harder to locate and would not directly measure domain coverage. Mocking SQLite instead would miss foreign-key and cascade behavior that the app relies on.
Consequences: The final command in the README passes 65 tests and reports 97% combined domain coverage without changing the user's database. This measures the selected Python modules, not every browser interaction or the accuracy of a real map search.

## 5. Keep authentication out of this local single-user version
Date: 2026-10-04
Status: Decided
Context: I designed the schema without a `users` table, and Assignment 1 is a minimal local app rather than a public multi-user service. The app stores private notes and bill files, so access control matters if its use expands beyond a trusted local machine.
Decision: Do not add login or multiple accounts for this version. Treat the SQLite file and bill directory as private local data and leave account support for a later redesign.
Alternatives considered: Adding login now would support use on a shared or public server, but it would also need user records, password or external identity handling, sessions, authorization checks on every read and download, and further security tests. That work would enlarge this assignment without strengthening its required two-domain behavior.
Consequences: The app can start with no account setup, but anyone who can reach a publicly exposed instance could see or change personal records. A public or multi-user release must add authentication and ownership checks before real notes or bills are used there.
