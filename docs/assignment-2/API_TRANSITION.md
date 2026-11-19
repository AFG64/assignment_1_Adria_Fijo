# API transition status — milestone 6

Restaurant and dining JSON APIs now run on isolated SQL databases, including
server-side visit coordination and saved-entry/history deletion. Static collection lists/add/save/remove/filters/details now run in ui/, with read-only dining history. Dining/edit controls remain milestone 7. The Assignment 1
monolith and SQLite source remain available for reference and offline transfer.
OpenAPI files use JSON syntax, also valid YAML. Service manifests pin Flask,
pymssql and Gunicorn. See [coordination details](SERVICE_COORDINATION.md) for
failure semantics, cleanup retries and concurrency.

## Operation map

The static UI resolves restaurant IDs into saved-entry IDs from restaurant
responses, then use saved IDs for dining requests. IDs are not interchangeable.

| Existing UI operation | Target service and operation |
|---|---|
| Home saved list | restaurants: `GET /saved-restaurants` |
| Add restaurant and save it | restaurants: `POST /restaurants` |
| Catalog and five filters | restaurants: `GET /restaurants` |
| Restaurant detail | restaurants: `GET /restaurants/{restaurant_id}` |
| Save existing catalog entry | restaurants: `POST /restaurants/{restaurant_id}/saved-entry` |
| Edit rating, notes and return preference | restaurants: `PATCH /saved-restaurants/{saved_id}` |
| Address lookup or manual coordinates | restaurants: `PUT /restaurants/{restaurant_id}/location` |
| Remove saved entry, history and bills | restaurants: `DELETE /saved-restaurants/{saved_id}`, coordinating dining deletion |
| View visits, items and bill metadata | dining: `GET /saved-restaurants/{saved_id}/visits` |
| Record dated visit | dining: `POST /saved-restaurants/{saved_id}/visits` |
| Add ordered item | dining: `POST /saved-restaurants/{saved_id}/visits/{visit_id}/items` |
| Upload bill | dining: `POST /saved-restaurants/{saved_id}/visits/{visit_id}/bills` |
| Download bill | dining: `GET /saved-restaurants/{saved_id}/visits/{visit_id}/bills/{bill_id}` |
| Health | each service: `GET /health` |

## Ownership and server calls

Restaurants owns restaurants, saved_restaurants, restaurant_images and
restaurant_emails. Dining owns visits, visit_items and bills. The dining saved ID
is an external identifier, without a cross-database foreign key. No service may
query the peer database. Proposed bill storage is binary content in dining SQL,
so container replacement cannot erase uploads; implemented and tested in milestone 4.

Dining calls restaurants `GET /saved-restaurants/{saved_id}` and
`PUT /saved-restaurants/{saved_id}/visited`. Restaurants calls dining
`DELETE /saved-restaurants/{saved_id}/history` when removing a saved entry.
Both services need a peer URL and explicit bounded timeout from configuration.
Geocoding remains in restaurants and also needs a bounded timeout.

There is no distributed transaction. Dining validates and marks a saved entry
visited over HTTP before committing a local visit under a per-saved-ID lock.
Restaurant deletion revokes the saved entry first, then requests idempotent dining
cleanup. 503 responses explicitly distinguish unconfirmed writes and pending
cleanup. POST is not automatically retried; DELETE may safely repeat. The JSON
error envelope contains `error`, `message` and `retryable`; own health remains
independent of peer availability. See the coordination document for trade-offs.

## Checks and remaining gates

Install `requirements-dev.txt`, then run:

```sh
python -m ruff check --select E9,F63,F7,F82 app.py backend database tests scripts
python scripts/validate_contracts.py --require-system
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov=service_runtime --cov=services.restaurants --cov=services.dining --cov-report=term-missing --cov-report=json
python scripts/check_domain_coverage.py
```

The initial workflow runs these checks on pushes and PRs. Its coverage floor is
applied separately to the existing two domain modules, not a combined percentage.
Restaurant and dining core modules also have independent coverage gates. Both
images, local SQL workflows, transfers and cross-service HTTP/partial-failure
checks run in CI; legacy domain floors are retained during the UI transition.

The root `system.schema.json` is now the official Blackboard schema, copied
unchanged on 19 November. It replaces the historical student-authored version.
See [schema provenance](SYSTEM_SCHEMA.md) and [requirement updates](REQUIREMENT_UPDATES.md).
CI validates Draft 2020-12, including required PORT/DATABASE_URL, secret/default
rules, HTTPS public_url, Storage website naming and timeout bounds. Additional
semantic checks validate peer references and called OpenAPI endpoints without
changing the official schema. Negative acceptance tests exercise invalid values.

`system.yaml` describes the **target** split architecture. Its `ui/` path holds the static collection UI; each migration path holds `001_init.sql`. Remaining dining/editing UI and Azure provisioning remain planned; both APIs and cross-service coordination are implemented. Environment settings cover the service runtime and peer calls. The monolith continues to use its own configuration. Update this
inventory alongside implementation, including any added settings and defaults.
The user confirmed student/prefix `afijo2024` and class 3A on 17 November; registry namespace follows repository owner `AFG64`. The updated guide uses proposed personal group rg-afijo2024 and Storage account afijo2024ui.
Names are unverified, not provisioned. public_url is an explicit reserved HTTPS
placeholder; local CORS stays localhost. Replace the placeholder with the discovered Storage endpoint before deployment; this file is not
a deployment configuration. No secret values are stored here.

Both image builds and local isolated SQL checks now run in CI; a successful remote
run is still required before the first PR merges. No Azure access or deployment is part of this baseline.
