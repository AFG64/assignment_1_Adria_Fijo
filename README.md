# Picky

Picky is a personal restaurant journal developed across Individual Assignments 1–2.
The current version serves a static UI and two Flask APIs, each owning an isolated
SQL database. It supports saved places, location editing, visits, ordered items
and bill uploads/downloads.

## Live Assignment 2 system

| Component | Public endpoint |
|---|---|
| Picky UI | [Open Picky](https://afijoieu2024ui.z28.web.core.windows.net) |
| Restaurant API | [Own SQL health](https://afijo-ieu2024-restaurants.wonderfulsmoke-a09dc47c.francecentral.azurecontainerapps.io/health) |
| Dining API | [Own SQL health](https://afijo-ieu2024-dining.wonderfulsmoke-a09dc47c.francecentral.azurecontainerapps.io/health) |

The first main release passed CI/CD on 20 November. Each health response reports
its deployed Git SHA; compare it with the latest successful main Actions run.
Every main release rebuilds SHA-tagged images, applies pending forward migrations,
checks both own databases, and publishes public-only UI configuration. Initial
resources and operating commands are documented in
[Azure operations](docs/assignment-2/AZURE_OPERATIONS.md).
Migration 002 is gated until the populated 001 baseline and the user's before
evidence are confirmed. Private local Assignment 1 data is not automatically
uploaded. Assignment 1 code and instructions remain available for reference.

## Run the current system locally

Install Docker Desktop with Linux containers. SQL Server uses linux/amd64; on
Apple Silicon, enable Docker Desktop's Rosetta support. The application images
and CI use Python 3.12. No host Python or credential preparation is needed to
start the current system.

From a fresh checkout, start the stack with one command:

```sh
docker compose up --build
```

Open [Picky locally](http://localhost:8080). API health endpoints are
[restaurants](http://localhost:8001/health) and [dining](http://localhost:8002/health).
The existing one-off SQL initializer generates three distinct random passwords
inside private Docker volumes. Each API mounts only its own password read-only;
the SQL administrator password is never mounted into either API. Passwords and
SQL data are retained together on later starts. If upgrading an older local
stack, keep its original ignored .env for the first start so existing credentials
are adopted. Conflicting credentials cause startup to fail without rotating them.
`docker compose down` keeps data and credentials; `down --volumes` removes both.

For one-service startup, configuration, SQL checks and offline data transfer, see
[local development](docs/assignment-2/LOCAL_DEVELOPMENT.md).

## Run checks

Use an activated virtual environment; CI uses Python 3.12. Install the development
manifest for the complete test suite, including both service domains:

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_contracts.py --require-system
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov=service_runtime --cov=services.restaurants --cov=services.dining --cov-report=term-missing --cov-report=json
python scripts/check_domain_coverage.py
```

The [local development guide](docs/assignment-2/LOCAL_DEVELOPMENT.md#tests-and-checks)
lists the real SQL/HTTP checks. CI also builds both images, lints workflows,
compiles Bicep and checks the migration evidence gate. CI uses disposable local
SQL containers; deployment runs only after CI passes on the same main SHA.

## Repository layout

```text
services/
  restaurants/          Restaurant API, pinned dependencies, Dockerfile and migrations
  dining/               Dining API, pinned dependencies, Dockerfile and migrations
service_runtime/        Shared SQL/migration, HTTP peer and health/logging helpers
ui/                     Current static HTML/CSS/JS and public API configuration
db/                     Local SQL Server database/login initialization
infra/azure/            Bicep, nonsecret deployment plan and migration checkpoint
scripts/                Local verification, data transfer and Azure operating tools
tests/
  restaurants/          Restaurant service unit tests
  dining/               Dining service unit tests
  runtime/              Shared runtime tests
  seam/                 Service coordination tests
  test_*.py             Legacy regressions and configuration/contract/tooling tests
.github/workflows/      Reusable CI and main-only CD
system.yaml             Service boundaries, configuration, calls and Azure names
system.schema.json      Unmodified official system schema
requirements-dev.txt    Full development/testing dependencies
backend/, database/,    Retained Assignment 1 Flask/SQLite application
frontend/, app.py
requirements.txt        Dependencies for the legacy application

docs/README.md          Documentation index
docs/assignment-1/      Legacy application instructions
docs/assignment-2/      Current technical guides and course requirement references
ADR.md, AI_USAGE.md     Student-owned process records
output/pdf/             Existing Assignment 1 report
```

Each service's requirements.txt is the pinned runtime manifest for its image.
The root requirements.txt supports the legacy app; requirements-dev.txt supports
repository-wide checks. `db/` initializes local SQL Server, while `database/`
belongs to the retained SQLite app.

## Documentation

Start with the [documentation index](docs/README.md). Main references:

- [API operation map](docs/assignment-2/API_TRANSITION.md) and committed
  [restaurant](services/restaurants/openapi.yaml)/[dining](services/dining/openapi.yaml) OpenAPI contracts.
- [Static UI](docs/assignment-2/STATIC_UI.md) and
  [cross-service coordination/recovery](docs/assignment-2/SERVICE_COORDINATION.md).
- [Azure setup and operation](docs/assignment-2/AZURE_OPERATIONS.md) and
  [verified resource inventory](docs/assignment-2/AZURE_READINESS.md).
- [Updated course requirements](docs/assignment-2/REQUIREMENT_UPDATES.md) and
  [official schema provenance](docs/assignment-2/SYSTEM_SCHEMA.md).
- [Legacy Assignment 1 instructions](docs/assignment-1/README.md).

## Git workflow and ownership

Use descriptive feature branches and a pull request to main. Required checks must
pass before merge; a main merge starts the Azure release automatically. Keep
meaningful commits with their actual timestamps. Ignore rules do not remove files
already in Git history or untrack them automatically.

Personal decisions, AI usage, explanations, report/disclosure and selected
evidence are written by the student. See [ADRs](ADR.md) and [AI usage](AI_USAGE.md).
Local agent instructions and the working roadmap are intentionally ignored;
they are not required to run the application or its CI. Migration 002 remains
paused at the populated-baseline checkpoint until the student confirms before
evidence is captured.
