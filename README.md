# DevOps Food

DevOps Food is an approved personal restaurant discovery and dining-history idea for Individual Assignment 1. This repository is **still in progress**. It starts one Flask process, creates the SQLite schema supplied by the student, and has pages for the saved list, full restaurant catalog, restaurant details, and dining history. Location lookup, bill uploads, and initial automated tests are implemented. The final report and some planned features remain to be completed.

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

Use the **+** button beside **DevOps Food** to open the add form. It asks for a restaurant name and optional category, city, location or street address, price level, personal rating, notes, and saved status. When an address is supplied, the app looks up its latitude and longitude and stores both with the address. On other pages, the + button returns to the home page with the form open. After saving, the new restaurant appears in the saved list. **[All restaurants](http://localhost:8000/restaurants)** shows every row in the `restaurants` table, including places that are no longer saved. Its status label distinguishes saved places from unsaved ones. For an unsaved restaurant, choose **Save restaurant**, select **Want to go** or **Visited already**, then choose **Add to saved list**. This uses the student's `save_existing_restaurant` function and creates a saved entry for the existing catalog row.

Click a restaurant's name or information in either list to open its detail page at `/restaurants/<id>`. It shows available restaurant facts and, when the restaurant is saved, its personal status, rating, notes, return preference, and visit history. Its Location section shows the stored address and coordinates, opens the location in OpenStreetMap, and lets you add or change the address. Check the map pin after lookup: the first search match may not be the intended restaurant, so a full address works best. Use **Record a visit** to enter a date, optional visit rating, and notes. Recording a visit marks the saved restaurant as Visited. Each visit has an **Attach a bill** control for a PNG, JPEG, or PDF file up to 5 MB, followed by a download link. Visits and bills use the student's `add_visit` and `add_bill` functions. Missing restaurant IDs return a 404 page.

Address lookup uses OpenStreetMap's public Nominatim service when a location form is submitted. It requires internet access; adding a restaurant without an address still works offline. The app sends an identifying User-Agent, allows at most one lookup per second in its single process, caches successful and empty results in `DATA_DIR/geocoding_cache.json`, and displays OpenStreetMap attribution by the location controls. To use a compatible service instead, set `GEOCODER_BASE_URL` to its base URL before starting the app. Delete `geocoding_cache.json` while the app is stopped to repeat cached lookups. Do not use the public service for bulk imports or autocomplete. See the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/).

The add form calls the student's `add_restaurant` function in `backend/restaurant_domain.py`. The saved list's **Remove** button calls the student's `remove_restaurant` function after a confirmation prompt. It removes the `saved_restaurants` row, while keeping the restaurant in the full catalog. Any visits, bill records, and items linked to that saved entry are deleted by SQLite's cascading foreign keys; managed bill files are also removed. There is no way to restore them in the app. Editing restaurants and recording ordered items are not available yet. There is no login, so notes and bills are not access-controlled.

If you created a database with the earlier three-table scaffold, choose a new empty `DATA_DIR` or migrate the old data. Startup reports the incompatible schema instead of altering it silently.

Example configuration:

```sh
DATA_DIR=/tmp/devops-food-data PORT=8080 python app.py
```

## Project layout

```text
app.py                       Starts the one Flask process
backend/
  web.py                     Flask routes and app setup
  restaurant_domain.py       Restaurant business logic and catalog queries
  dining_history.py         Visit and bill database operations
  bill_files.py             Bill upload validation and file storage
  geocoding.py              Address lookup, rate limit, and persistent cache
database/
  __init__.py                SQLite path, connections, and initialization
  schema.sql                 Table definitions and relationships
frontend/
  templates/                  Shared layout, saved list, full catalog, and detail pages
  static/                    Page styling and add-form interaction
docs/                         Plan, domain boundaries, schema diagram, and report draft
ADR.md, AI_USAGE.md           Required process logs at the repository root
requirements.txt             The only dependency manifest
```

The root `app.py` is the start command. `backend/web.py` handles requests, calls restaurant logic in `backend/restaurant_domain.py`, and renders files from `frontend/`. Database functions read `database/schema.sql` and store the SQLite file in `DATA_DIR`.

## Planned feature boundaries

- **Restaurant collection:** adding, saving an existing catalog row with a status, listing saved places, listing all catalog rows, viewing a restaurant's details, adding or changing an address and coordinates, and removing a saved entry are implemented. The schema also supports the single user's overall rating, notes, and return preference; other editing and filters are planned.
- **Dining history:** recording and listing dated visits with optional rating and notes, and attaching and downloading bill files are implemented. Spend, party size, ordered items, and bill extraction remain planned.

`restaurants`, `saved_restaurants`, `restaurant_images`, and `restaurant_emails` belong to the collection; `visits`, `bills`, and `visit_items` belong to dining history. A visit refers to a saved restaurant by ID. Bill files are stored in `DATA_DIR/bills/` with generated filenames; `bills.image_path` stores their relative paths in SQLite. The app checks the file signature and size before storing an upload. The bill download route checks that the bill belongs to the restaurant's visit. Keep `DATA_DIR` private because the app has no login.

The planned ownership, business rules, and interactions are defined in [`docs/DOMAIN_BOUNDARIES.md`](docs/DOMAIN_BOUNDARIES.md).

## Documents and checks

- [`assignment_1.md`](assignment_1.md): assignment brief.
- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md): checklist and staged work plan.
- [`docs/SCHEMA.md`](docs/SCHEMA.md): the seven-table database diagram and field explanations.
- [`ADR.md`](ADR.md): decisions made so far; two more dated entries are still required.
- [`AI_USAGE.md`](AI_USAGE.md): AI interaction log; the student's explanation needs review.
- [`docs/REPORT.md`](docs/REPORT.md): report outline; expand to 4–5 pages once the app and test results are real.

The required core-logic tests and measured coverage do not exist yet. The intended command, once those tests are added, is:

```sh
python -m pytest --cov=backend.restaurant_domain --cov=backend.dining_history --cov-report=term-missing
```

Do not report a coverage percentage until the command has been run on implemented domain logic.
