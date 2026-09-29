# DevOps Food

DevOps Food is an approved personal restaurant discovery and dining-history idea for Individual Assignment 1. This repository is **a scaffold, not the finished app**. It currently starts one Flask process, creates the SQLite schema, and serves a placeholder page. Restaurant and visit features, domain tests, and the final report remain to be built in later iterations.

## Run the scaffold

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:8000/`. `GET /health` returns `{"status":"ok"}`. The process binds to `0.0.0.0` and uses `PORT` (default `8000`). Set `DATA_DIR` to change the directory containing `devops_food.sqlite3`; the default is `./data/devops_food.sqlite3`, relative to the directory where you start the app. The database is initialized on startup without a manual migration step. No external service is required.

Example configuration:

```sh
DATA_DIR=/tmp/devops-food-data PORT=8080 python app.py
```

## Planned feature boundaries

- **Restaurant collection:** save restaurants to visit or already visited, with cuisine, city, and price level; filter the collection, including by visit rating.
- **Dining history:** record dated visits, rating, notes, orders, bill, and whether to return.

The SQLite schema is in `storage.py`: `restaurants` is owned by the collection, while `visits` and `ordered_items` belong to dining history. A visit refers to one restaurant by ID. The final behavior, validation, and upload rules are still pending.

## Documents and checks

- [`assignment_1.md`](assignment_1.md): assignment brief.
- [`PROJECT_PLAN.md`](PROJECT_PLAN.md): checklist and staged work plan.
- [`ADR.md`](ADR.md): decisions made so far; two more dated entries are still required.
- [`AI_USAGE.md`](AI_USAGE.md): AI interaction log; the student's explanation needs review.
- [`REPORT.md`](REPORT.md): report outline; expand to 4–5 pages once the app and test results are real.

The required core-logic tests and measured coverage do not exist yet. The intended command, once those tests are added, is:

```sh
python -m pytest --cov=restaurant_domain --cov=visit_domain --cov-report=term-missing
```

Do not report a coverage percentage until the command has been run on implemented domain logic.
