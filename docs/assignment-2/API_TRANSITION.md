# API boundaries and operation map

Restaurant and dining JSON APIs run on isolated SQL databases, including
server-side visit coordination and saved-entry/history deletion. The static UI
supports catalog/saved lists, add/save/remove/filter/detail flows, personal and
location editing, visit/item entry and bill upload/download. The retained
Assignment 1 monolith/SQLite source is described separately in the
[legacy guide](../assignment-1/README.md).

OpenAPI files use JSON syntax, also valid YAML. Each service manifest pins Flask,
pymssql and Gunicorn. See [coordination details](SERVICE_COORDINATION.md) for
failure semantics, cleanup retries and concurrency.

## Operation map

The static UI resolves restaurant IDs into saved-entry IDs from restaurant
responses, then uses saved IDs for dining requests. IDs are not interchangeable.

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

Ordered-item creation and visit history return read-only `line_total` alongside
`unit_price`: Dining SQL computes quantity times stored unit price. Unknown prices
produce null totals; clients must omit this field from requests. Migration 002
adds the persisted column without changing existing item inputs or ownership.

## Ownership and server calls

Restaurants owns restaurants, saved_restaurants, restaurant_images and
restaurant_emails. Dining owns visits, visit_items and bills. The dining saved ID
is an external identifier, without a cross-database foreign key. No service may
query the peer database. Bill contents are stored as binary data in dining SQL,
so replacing a container does not erase uploads.

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

## Validation and deployed configuration

Install `requirements-dev.txt`, then run:

```sh
python -m ruff check --select E9,F63,F7,F82 app.py backend database tests scripts service_runtime services
python scripts/validate_contracts.py --require-system
python -m pytest -q --cov=backend.restaurant_domain --cov=backend.dining_history --cov=service_runtime --cov=services.restaurants --cov=services.dining --cov-report=term-missing --cov-report=json
python scripts/check_domain_coverage.py
```

Reusable CI runs these checks on feature pushes/PRs and is called by main's CD
on the same commit before release. Coverage is enforced independently for service
core modules, shared runtime and the two retained legacy domains. CI also builds
both images and tests local SQL workflows, transfers, restart persistence and
cross-service/partial-failure behavior. It never connects to Azure SQL.

The root `system.schema.json` is now the official Blackboard schema, copied
unchanged on 19 November. It replaces the historical student-authored version.
See [schema provenance](SYSTEM_SCHEMA.md) and [requirement updates](REQUIREMENT_UPDATES.md).
CI validates Draft 2020-12, including required PORT/DATABASE_URL, secret/default
rules, HTTPS public_url, Storage website naming and timeout bounds. Additional
semantic checks validate peer references and called OpenAPI endpoints without
changing the official schema. Negative acceptance tests exercise invalid values.

`system.yaml` records the split services, actual guide-derived resource names,
public website URL, runtime settings and peer calls. The student is afijo.ieu2024;
the resource prefix is afijo-ieu2024, group rg-afijo-ieu2024 and Storage account
afijoieu2024ui. The deployment plan/manifest consistency check protects those
names from drifting. Live component URLs are in the [main README](../../README.md)
and [Azure inventory](AZURE_READINESS.md).

Peer URLs and UI origin have local defaults and are overridden with discovered
HTTPS endpoints by main's deployment pipeline. The static UI receives public API
origins through generated config.js. Secret DATABASE_URL values are not stored
in system.yaml or UI files. The monolith continues to use its legacy configuration.

Restaurants has only 001_init.sql; Dining also has 002_add_item_line_total.sql.
The approved before bundle and checkpoint permit 002 in source. Actual deployed
state is determined by the successful main release and service versions. See
[migration verification](MIGRATIONS.md) and
[Azure operations](AZURE_OPERATIONS.md#before-migration-002) for the release gates.
