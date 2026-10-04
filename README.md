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

Click a restaurant's name or information in either list to open its detail page at `/restaurants/<id>`. It shows available restaurant facts and, when the restaurant is saved, its personal status, rating, notes, return preference, and visit history. Its Location section shows the stored address and coordinates, opens the location in OpenStreetMap, and lets you add or change the address. A full address with city and postal code works best. The app uses it as entered, even if the restaurant has a different saved city; for short addresses, it adds the saved city. If lookup fails or points to the wrong place, expand **Enter coordinates manually** and save a place name, latitude, and longitude. Check the map pin after either method because the search service can return a street or another place with a similar name. Use **Record a visit** to enter a date, optional visit rating, and notes. Recording a visit marks the saved restaurant as Visited. Under each visit, **Add what you ordered** saves a dish or drink with quantity and optional unit price. **Attach a bill** accepts a PNG, JPEG, or PDF file up to 5 MB and then offers a download link. Missing restaurant IDs return a 404 page.

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
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov-report=term-missing
```

Measured on 2026-10-04: **65 tests passed; 97% combined domain coverage** (restaurant collection 97%, dining history 96%). These tests check restaurant validation, saving, editing, and removal, catalog filters, visit status, ordered items, bill ownership, and cascade deletion. The command measures the two domain modules, not every line of the Flask UI. Location lookup is mocked in route tests, so the test suite does not need internet access.
