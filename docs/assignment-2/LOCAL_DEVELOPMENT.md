# Assignment 2 local development

Run all commands from the repository root. The current system has two Flask JSON
services, one SQL database per service, shared runtime helpers and a static UI.
Contract paths and configuration are defined by system.yaml and each service's
OpenAPI document. The official system schema is copied unchanged.

For navigation, see the [main README](../../README.md) and
[documentation index](../README.md). Cloud setup and operating steps live in
[Azure operations](AZURE_OPERATIONS.md).

## Start the local system

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
Azure uses contained users with db_ddladmin, db_datareader and db_datawriter
in each own database; the real local compatibility check is described below.

To run only one service and its database prerequisites:

```sh
docker compose up --build restaurants
```

## Tests and checks

Activate a virtual environment before installing development dependencies. CI and
service images use Python 3.12. The full command below includes both the legacy
regression tests and the split-service tests.

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_contracts.py --require-system
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov=service_runtime --cov=services.restaurants --cov=services.dining --cov-report=term-missing --cov-report=json
python scripts/check_domain_coverage.py
python scripts/check_stack.py
python scripts/check_restaurant_api.py
python scripts/check_dining_sql.py
python scripts/check_seam.py
python scripts/check_azure_roles.py
python scripts/check_baseline_local.py
```

The SQL/HTTP scripts require the running full local stack and use only local
containers, never Azure SQL. Disposable database/record checks remove their own
targets. The stack check retains its local restart marker for repeated checks. The seam check deliberately stops and restores
peers. check_stack.py verifies repeat boot and restart persistence;
check_dining_sql.py also verifies exact bill bytes across a restart.
check_azure_roles.py checks the proposed Azure contained-user roles locally and
restores the original local SQL instance settings.

Coverage floors apply independently to restaurant and dining core modules,
shared runtime modules and the retained legacy domains. Both Docker images,
contracts, workflow lint and Bicep compilation are also gated in CI.

## Runtime, configuration and persistence

Each service image uses an allowlisted build context, explicit COPY, a pinned
manifest and UID 10001. Gunicorn uses one worker; worker initialization applies
migrations under a database lock before serving API requests. SQL scripts and
ledger entries commit together. Checksums are verified, and changed or missing
applied scripts cause startup to fail.
No `002` exists yet. Do not edit `001` after applying it; use a new migration for
future changes. No startup path drops a database or erases existing tables.

Database connections use encrypted TDS, 5-second login/query timeouts and up to
12 startup attempts with capped exponential backoff (about two minutes including
connection timeouts). Read/write health probes roll back their temporary rows
and return 503 when the own database fails; they do not call the peer. Request
logs include method, path, status, duration, service and version. `PORT`,
`DATABASE_URL`, `VERSION` and `UI_ORIGIN` configure each service. The peer URL/
timeout and restaurant geocoder settings are also read from the environment;
see system.yaml for their documented defaults. A nonlocal version can
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

Removal coordinates dining cleanup over HTTP; see Service coordination below.
Unit tests enforce at least 70% on each restaurant core module, alongside the
retained legacy domain and shared-runtime floors. The SQL HTTP check runs in CI
after compose starts and cleans up only records it creates. Dining own-domain
workflows are described below.


## Dining SQL and Assignment 1 transfer

Dining now lists history and stores ordered items and PNG/JPEG/PDF bill contents
in its own SQL database. Downloads check the saved-entry, visit and bill IDs.
Uploads are limited to 5 MiB and returned as attachments. Container replacement
does not remove bill contents. Visit creation uses the restaurant coordinator;
history DELETE performs idempotent cleanup under the dining lock (see Service
coordination below).
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

Verified Azure settings and the resource inventory are in
[AZURE_READINESS.md](AZURE_READINESS.md). Initial resources were
provisioned on 20 November; application release status is recorded by main’s
CI/CD runs and each service’s health version.

## Service coordination

Dining now records visits through the restaurant API: it validates the saved ID,
marks it visited, then commits the visit. Peer failure produces an explicit 503;
POST is not automatically retried. When an own write cannot be confirmed, check
history before submitting again. Restaurant status may remain visited after a
failed attempt. Saved-entry deletion removes the saved row, then asks dining to
clear history/items/bill bytes; 503 cleanup_pending means retry that same DELETE
until 204. The catalog row remains. See
[coordination details](SERVICE_COORDINATION.md) for concurrency,
recovery and the distinction between peer failure and an uncertain own write.
Run `python scripts/check_seam.py` against the local compose stack to check real
service calls, stopped peers, recovery and concurrent deletion. No migration 002
has been added or applied.
