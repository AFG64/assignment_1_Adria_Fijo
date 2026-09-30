# DevOps Food

DevOps Food is an approved personal restaurant discovery and dining-history idea for Individual Assignment 1. This repository is **a scaffold, not the finished app**. It currently starts one Flask process, creates the SQLite schema supplied by the student, and serves a placeholder page. Restaurant and visit features, domain tests, and the final report remain to be built in later iterations.

## Run the scaffold

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:8000/`. `GET /health` returns `{"status":"ok"}`. The process binds to `0.0.0.0` and uses `PORT` (default `8000`). Set `DATA_DIR` to change the directory containing `devops_food.sqlite3`; the default is `./data/devops_food.sqlite3`, relative to the directory where you start the app. The database is initialized on startup without a manual migration step. No external service is required. The schema is in [`schema.sql`](schema.sql) and its diagram is in [`SCHEMA.md`](SCHEMA.md).

If you created a database with the earlier three-table scaffold, choose a new empty `DATA_DIR` or migrate the old data. Startup reports the incompatible schema instead of altering it silently.

Example configuration:

```sh
DATA_DIR=/tmp/devops-food-data PORT=8080 python app.py
```

## Planned feature boundaries

- **Restaurant collection:** store general restaurant details and the single user's saved status, overall rating, notes, and return preference. Planned filters include category, city, price, and personal rating.
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
