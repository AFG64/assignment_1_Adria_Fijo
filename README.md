# Picky

Picky is an approved personal restaurant discovery and dining-history app for Individual Assignment 1. One Flask process serves the UI and two SQLite-backed feature domains: restaurant collection and dining history. The app supports saved places, catalog filters, location lookup, dated visits, ordered items, and bill uploads.

## Run locally

You need Python 3.10 or newer. Open a terminal **in this repository's root folder** (the folder containing `app.py` and `requirements.txt`), then run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Leave that terminal running. Open **[http://localhost:8000/](http://localhost:8000/)** in your browser to use the app. If you already have the app running, just open that address; you do not need to start another copy. Press `Ctrl+C` in the terminal to stop it.

**Do not open `frontend/templates/index.html` directly.** It is a Flask template, so opening it as a `file://` page shows raw `{{ ... }}` and `{% ... %}` text and misses the styling. Flask renders it correctly at `http://localhost:8000/`.

On later runs, after the first installation, activate the existing environment and start the app:

```sh
source .venv/bin/activate
python app.py
```

`GET /health` returns `{"status":"ok"}`. The process binds to `0.0.0.0` and uses `PORT` (default `8000`). Set `DATA_DIR` to change the directory containing `devops_food.sqlite3`; the default is `./data/devops_food.sqlite3`, relative to the directory where you start the app. The database is initialized on startup without a manual migration step. Starting the app does not require an external service. The schema is in [`database/schema.sql`](database/schema.sql) and its diagram is in [`docs/SCHEMA.md`](docs/SCHEMA.md).

To add the 14 sourced Madrid restaurants to the catalog, run this once from the repository root with the same `DATA_DIR` used by the app:

```sh
python -m database.seed_madrid
```

The importer can be run again: it skips matching Madrid names and leaves saved entries and visits alone. It stores names, cuisines, and street addresses from the Madrid tourism pages linked in [`database/seed_madrid.py`](database/seed_madrid.py). It does not invent ratings, prices, or map coordinates, and it does not send bulk geocoding requests. New rows appear under **All restaurants** as **Not saved**; save any you want to track.

Use the **+** button beside **Picky** to open the add form. It asks for a restaurant name and optional category, city, location or street address, price level, personal rating, notes, and saved status. When an address is supplied, the app looks up its latitude and longitude and stores both with the address. On other pages, the + button returns to the home page with the form open. After saving, the new restaurant appears in the saved list. **[All restaurants](http://localhost:8000/restaurants)** shows every row in the `restaurants` table, including places that are no longer saved. Expand **Filters** to narrow the catalog by cuisine, city, price level, minimum personal rating, or saved status, and collapse it to focus on the list. Active filters stay visible when the page reloads. The filters can be combined; the minimum rating applies only to saved restaurants that have a personal rating. Choose **Clear filters** to see everything again. For an unsaved restaurant, choose **Save restaurant**, select **Want to go** or **Visited already**, then choose **Add to saved list**. This uses the student's `save_existing_restaurant` function and creates a saved entry for the existing catalog row.

Click a restaurant's name or information in either list to open its detail page at `/restaurants/<id>`. An unsaved restaurant can be added to your list directly on that page; after saving, you stay on its details page. The page shows available restaurant facts and, when saved, its personal status, rating, notes, return preference, and visit history. Its Location section shows the stored address and coordinates, opens the location in OpenStreetMap, and lets you add or change the address. A full address with city and postal code works best. The app uses it as entered, even if the restaurant has a different saved city; for short addresses, it adds the saved city. If lookup fails or points to the wrong place, expand **Enter coordinates manually** and save a place name, latitude, and longitude. Check the map pin after either method because the search service can return a street or another place with a similar name. Use **Record a visit** to enter a date, optional visit rating, and notes. Recording a visit marks the saved restaurant as Visited. Under each visit, **Add what you ordered** saves a dish or drink with quantity and optional unit price. **Attach a bill** accepts a PNG, JPEG, or PDF file up to 5 MB and then offers a download link. Missing restaurant IDs return a 404 page.

On a saved restaurant's detail page, expand **Edit your saved details** to change or clear your overall rating, private notes, and whether you would go back.

Address lookup uses OpenStreetMap's public Nominatim service when a location form is submitted. It requires internet access; adding a restaurant without an address still works offline. The app sends an identifying User-Agent, allows at most one lookup per second in its single process, caches successful and empty results in `DATA_DIR/geocoding_cache.json`, and displays OpenStreetMap attribution by the location controls. To use a compatible service instead, set `GEOCODER_BASE_URL` to its base URL before starting the app. Delete `geocoding_cache.json` while the app is stopped to repeat cached lookups. Do not use the public service for bulk imports or autocomplete. See the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/).

The add form calls the student's `add_restaurant` function in `backend/restaurant_domain.py`. The saved list's **Remove** button calls the student's `remove_restaurant` function after a confirmation prompt. It removes the `saved_restaurants` row, while keeping the restaurant in the full catalog. Any visits, bill records, and items linked to that saved entry are deleted by SQLite's cascading foreign keys; managed bill files are also removed. There is no way to restore them in the app. Editing general restaurant facts is not available yet. There is no login, so notes and bills are not access-controlled.

If you created a database with the earlier three-table scaffold, choose a new empty `DATA_DIR` or migrate the old data. Startup reports the incompatible schema instead of altering it silently.

Example configuration:

```sh
DATA_DIR=/tmp/picky-data PORT=8080 python app.py
```

## Project layout

```text
app.py                       Starts the one Flask process
backend/
  web.py                     Flask routes and app setup
  restaurant_domain.py       Restaurant business logic and catalog queries
  dining_history.py         Visit, ordered item, and bill database operations
  bill_files.py             Bill upload validation and file storage
  geocoding.py              Address lookup, rate limit, and persistent cache
database/
  __init__.py                SQLite path, connections, and initialization
  schema.sql                 Table definitions and relationships
frontend/
  templates/                  Shared layout, saved list, full catalog, and detail pages
  static/                    Page styling and add-form interaction
docs/                         Plan, domain boundaries, schema diagram, and report
ADR.md, AI_USAGE.md           Required process logs at the repository root
requirements.txt             The only dependency manifest
```

The root `app.py` is the start command. `backend/web.py` handles requests, calls restaurant logic in `backend/restaurant_domain.py`, and renders files from `frontend/`. Database functions read `database/schema.sql` and store the SQLite file in `DATA_DIR`.

## Feature boundaries

- **Restaurant collection:** adding, saving an existing catalog row with a status, listing saved places, filtering the full catalog, viewing a restaurant's details, editing personal rating, notes, and return preference, changing an address and coordinates, and removing a saved entry are implemented. Editing other general restaurant facts is not included.
- **Dining history:** recording and listing dated visits with optional rating and notes, recording ordered items, and attaching and downloading bill files are implemented. Spend, party size, and bill extraction remain planned.

`restaurants`, `saved_restaurants`, `restaurant_images`, and `restaurant_emails` belong to the collection; `visits`, `bills`, and `visit_items` belong to dining history. A visit refers to a saved restaurant by ID. Bill files are stored in `DATA_DIR/bills/` with generated filenames; `bills.image_path` stores their relative paths in SQLite. The app checks the file signature and size before storing an upload. The bill download route checks that the bill belongs to the restaurant's visit. Keep `DATA_DIR` private because the app has no login.

The planned ownership, business rules, and interactions are defined in [`docs/DOMAIN_BOUNDARIES.md`](docs/DOMAIN_BOUNDARIES.md).

## Documents and checks

- [`assignment_1.md`](assignment_1.md): assignment brief.
- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md): checklist and staged work plan.
- [`docs/SCHEMA.md`](docs/SCHEMA.md): the seven-table database diagram and field explanations.
- [`ADR.md`](ADR.md): five dated architecture and scope decisions.
- [`AI_USAGE.md`](AI_USAGE.md): AI interaction log; the student's explanation needs review.
- [`docs/REPORT.md`](docs/REPORT.md): report source with architecture and database diagrams.
- [`output/pdf/picky-assignment-1-report.pdf`](output/pdf/picky-assignment-1-report.pdf): four-page submission report.

Run the tests and measure coverage of the two backend feature domains with:

```sh
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov=service_runtime --cov=services.restaurants --cov=services.dining --cov-report=term-missing
```

Measured on 2026-10-04: **83 tests passed; 97% combined domain coverage** (restaurant collection 97%, dining history 96%). These tests check restaurant validation, saving, editing, and removal, catalog filters, visit status, ordered items, bill ownership, bill-file validation and cleanup, and cascade deletion. The command measures the two domain modules, not every line of the Flask UI. Location lookup is mocked in route tests, so the test suite does not need internet access.

## Assignment 2 container foundation (in progress)

The Assignment 1 instructions above remain available. The split services currently
implement startup, versioned SQL schemas, `/health` and request logs. Restaurants
also implements catalog/saved/details/location APIs and idempotent Madrid seeding.
Dining features and static screens are still being ported; nginx serves
a temporary setup page. Target endpoints/configuration are in `services/*/openapi.yaml`
and `system.yaml`. The system schema is student-authored from brief §8a.

Install Docker Desktop. SQL Server uses `linux/amd64`; on Apple Silicon use Docker
Desktop's Rosetta emulation. The real SQL checks also run on native amd64 in CI.
From a clean checkout:

```sh
python3 scripts/configure_local.py
docker compose up --build
```

The generator creates a private, ignored `.env` with three different random local
passwords. `.env.example` describes the required settings. Keep the generated
passwords with the SQL volume: existing logins are deliberately not reset on
startup. Never commit this file. If supplying your own passwords, use the same
`Aa1` plus random-hex format to keep sqlcmd substitution and connection URLs safe.

Local UI: [http://localhost:8080](http://localhost:8080).
Restaurant health: [http://localhost:8001/health](http://localhost:8001/health).
Dining health: [http://localhost:8002/health](http://localhost:8002/health).
SQL is reachable only inside the compose network. One-off `db-init` creates the
two databases/logins idempotently; each login has `db_owner` only in its own
database so it can apply migrations. Neither service receives the SA password.
Production privilege refinement and Azure setup remain later work.

To run only one service and its database prerequisites:

```sh
docker compose up --build restaurants
```

For local checks:

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_contracts.py --require-system
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov=service_runtime --cov=services.restaurants --cov=services.dining --cov-report=term-missing --cov-report=json
python scripts/check_domain_coverage.py
python scripts/check_stack.py
```

The last command needs the running full stack. It checks real SQL permissions,
second-boot migration no-ops, own read/write probes and persistence across service
restarts. CI builds both images and runs this against a disposable SQL container,
never Azure SQL. Coverage still measures the original feature modules until the
feature APIs are ported; runtime unit tests additionally exercise startup safety.

Each service image uses an allowlisted build context, explicit COPY, a pinned
manifest and UID 10001. Gunicorn starts one worker after acquiring a database
migration lock. SQL scripts and ledger entries commit together; applied script
checksums are verified and modified/missing applied files cause startup to fail.
No `002` exists yet. Do not edit `001` after applying it; use a new migration for
future changes. No startup path drops a database or erases existing tables.

Database connections use encrypted TDS, 5-second login/query timeouts and up to
12 startup attempts with capped exponential backoff (about two minutes including
connection timeouts). Read/write health probes roll back their temporary rows
and return 503 when the own database fails; they do not call the peer. Request
logs include method, path, status, duration, service and version. `PORT`,
`DATABASE_URL`, `VERSION` and `UI_ORIGIN` are the runtime settings currently read;
other settings in `system.yaml` describe the target APIs. A nonlocal version can
be built with `VERSION=$(git rev-parse HEAD) docker compose build`.

`docker compose down` retains the named SQL volume. Do not use `down --volumes`
for data you want to keep. To repeat initialization without resetting data:

```sh
docker compose run --rm db-init
docker compose restart restaurants dining
```

Restaurant API regression (running local stack): `python scripts/check_restaurant_api.py`.
For example, `GET http://localhost:8001/restaurants?city=Madrid&status=not_saved`
lists unsaved catalog entries. JSON responses include nested `saved` details;
creation/saving use POST, personal detail changes use PATCH, and location changes
use PUT. See the restaurant OpenAPI for bodies and status codes. A location can
be entered manually offline. Address search uses a bounded timeout, one-second
rate limit and a 256-entry in-memory success cache in the single worker. Cache
contents reset on restart. Do not bulk-geocode or use autocomplete.

Removal currently returns 503 `coordination_pending`, leaving records intact.
Successful deletion requires the dining HTTP cleanup protocol in milestone 5.
Unit tests enforce at least 70% on each restaurant core module, alongside the
transitional legacy domain/runtime floors. The SQL HTTP check runs in CI after
compose starts and cleans up only records it creates. Dining own-domain workflows are described below.


### Dining SQL and Assignment 1 transfer

Dining now lists history and stores ordered items and PNG/JPEG/PDF bill contents
in its own SQL database. Downloads check the saved-entry, visit and bill IDs.
Uploads are limited to 5 MiB and returned as attachments. Container replacement
does not remove bill contents. The visit insertion operation is implemented and
validated internally; its public POST and history DELETE return 503
`coordination_pending` until milestone 5 provides the restaurant coordinator.
Existing history, item and bill operations do not contact restaurants.

Run `python scripts/check_dining_sql.py` with compose running. It creates two
**local disposable** databases, tests repeated transfers, conflicts, original IDs,
SQL bill bytes and scoped HTTP operations, and removes only those test databases.
CI runs this check and enforces at least 70% on each dining core module.

For existing Assignment 1 data, first stop writes and make an SQLite backup
(using SQLite's backup API, not a file copy while writes may be active). Copy the
adjacent `bills/` directory beside that backup. Keep both under ignored `data/`;
never commit private bills or migrate them to the public demonstration system.
Validate the copy without changing any target:

```sh
python scripts/transfer_assignment1.py data/assignment2-check/snapshot.sqlite3
python scripts/check_dining_sql.py --snapshot data/assignment2-check/snapshot.sqlite3
```

The second command imports that copy twice into disposable local targets and
compares all source fields, relationships and bill bytes. Originals are untouched.
For an actual offline transfer, configure `RESTAURANTS_DATABASE_URL` and
`DINING_DATABASE_URL` securely in the local environment, then run the first
command with `--apply`. Never pass URLs as command arguments or paste credentials
into chat. The targets must already have 001 applied. Stop all application writes
and restaurant seeding; use empty targets or exact matching rows. A seeded target
may have conflicting IDs, which are rejected rather than overwritten.

Each domain transfers in one transaction. The two databases cannot commit
atomically: if the second domain fails, correct the cause and rerun against the
same snapshot before allowing traffic. Existing identical IDs are skipped;
conflicting IDs roll back that domain. Bill files must exist inside the copied
`bills/` directory; missing, invalid, oversized or symlinked files are rejected.
No migration file is changed by transfer. Cloud baseline uses synthetic data only.

Azure readiness and the proposed resource inventory are in
[AZURE_READINESS.md](docs/assignment-2/AZURE_READINESS.md). No Azure deployment exists yet.
