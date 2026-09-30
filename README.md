# DevOps Food

DevOps Food is an approved personal restaurant discovery and dining-history idea for Individual Assignment 1. This repository is **still in progress**. It starts one Flask process, creates the SQLite schema supplied by the student, and has a simple form to save and list restaurants. Dining-history features, domain tests, and the final report remain to be built in later iterations.

## Run locally

You need Python 3.10 or newer. Open a terminal **in this repository's root folder** (the folder containing `app.py` and `requirements.txt`), then run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Leave that terminal running. Open **[http://localhost:8000/](http://localhost:8000/)** in your browser to use the app. If you already have the app running, just open that address; you do not need to start another copy. Press `Ctrl+C` in the terminal to stop it.

**Do not open `templates/index.html` directly.** It is a Flask template, so opening it as a `file://` page shows raw `{{ ... }}` and `{% ... %}` text and misses the styling. Flask renders it correctly at `http://localhost:8000/`.

On later runs, after the first installation, activate the existing environment and start the app:

```sh
source .venv/bin/activate
python app.py
```

`GET /health` returns `{"status":"ok"}`. The process binds to `0.0.0.0` and uses `PORT` (default `8000`). Set `DATA_DIR` to change the directory containing `devops_food.sqlite3`; the default is `./data/devops_food.sqlite3`, relative to the directory where you start the app. The database is initialized on startup without a manual migration step. No external service is required. The schema is in [`schema.sql`](schema.sql) and its diagram is in [`SCHEMA.md`](SCHEMA.md).

The home page lets you add a restaurant with a name, optional category, city, price level, personal rating, notes, and saved status. After saving, it appears in the list below the form. The form calls the student's `add_restaurant` function in `restaurant_domain.py`. Visit recording and editing restaurants are not available yet. There is no login, so notes are not access-controlled.

If you created a database with the earlier three-table scaffold, choose a new empty `DATA_DIR` or migrate the old data. Startup reports the incompatible schema instead of altering it silently.

Example configuration:

```sh
DATA_DIR=/tmp/devops-food-data PORT=8080 python app.py
```

## Planned feature boundaries

- **Restaurant collection:** saving and listing are implemented. The schema also supports the single user's status, overall rating, notes, and return preference; editing and filters are planned.
- **Dining history:** record dated visits with a visit rating, notes, spend, party size, items ordered, and bills.

`restaurants`, `saved_restaurants`, `restaurant_images`, and `restaurant_emails` belong to the collection; `visits`, `bills`, and `visit_items` belong to dining history. A visit refers to a saved restaurant by ID. The final behavior, validation, and upload rules are still pending. Bill files are planned under `DATA_DIR`, with their path stored in SQLite; uploads are not implemented yet.

The planned ownership, business rules, and interactions are defined in [`DOMAIN_BOUNDARIES.md`](DOMAIN_BOUNDARIES.md).

## Documents and checks

- [`assignment_1.md`](assignment_1.md): assignment brief.
- [`PROJECT_PLAN.md`](PROJECT_PLAN.md): checklist and staged work plan.
- [`SCHEMA.md`](SCHEMA.md): the seven-table database diagram and field explanations.
- [`ADR.md`](ADR.md): decisions made so far; two more dated entries are still required.
- [`AI_USAGE.md`](AI_USAGE.md): AI interaction log; the student's explanation needs review.
- [`REPORT.md`](REPORT.md): report outline; expand to 4–5 pages once the app and test results are real.

The required core-logic tests and measured coverage do not exist yet. The intended command, once those tests are added, is:

```sh
python -m pytest --cov=restaurant_domain --cov=visit_domain --cov-report=term-missing
```

Do not report a coverage percentage until the command has been run on implemented domain logic.
