# Milestone 1: API transition

Restaurant collection endpoints now run on SQL Server; coordinated deletion remains a
503 response until milestone 5. Dining feature contracts remain planned. The Assignment 1 app and its
SQLite data remain the runnable baseline. OpenAPI files use JSON syntax, which is
also valid YAML. Service manifests pin Flask, pymssql and Gunicorn; milestone 2 adds SQL startup
and container health. Dining features and the static UI remain for later milestones.

## Operation map

The static UI will resolve restaurant IDs into saved-entry IDs from restaurant
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

There is no distributed transaction. The exact ordering, retry/idempotency and
concurrent deletion protocol is intentionally unresolved until milestone 5. The
contracts reserve 409 and 503 for conflicts and unavailable dependencies. Tests
must demonstrate partial-write behavior before claiming these flows work. An
error envelope has `error`, `message` and `retryable`; clients must not blindly
retry a mutation merely because its HTTP status is 503. Own-database health must
remain independent of peer availability.

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
It does not yet claim service-level or SQL integration coverage. Those gates must
replace the transitional baseline as services are implemented.

The root `system.schema.json` is **student-authored from Assignment 2 §8a**,
with user authorization on 15 November 2026. It is not official or
professor-provided. It declares JSON Schema Draft 2020-12 and uses the pinned
jsonschema validator. If an official schema appears later, compare/adapt ours
and rerun the checks; compatibility with an unknown official schema is unverified.

Local interpretations: exactly two services; closed objects to catch misspellings;
ports 1–65535; positive HTTP timeouts; nonsecret settings require a default;
secret settings require `secret: true` and forbid defaults. The schema checks
structure, not Azure naming rules, provisioned resources or live availability.
The validation script also checks UI/peer service references, declared peer URL
configuration and called endpoints against the target OpenAPI document. It
always requires both system files; there is no optional validation bypass.
Negative acceptance cases run with the normal pytest suite.

`system.yaml` describes the **target** split architecture. Its `ui/` path currently holds a setup page; each migration path holds `001_init.sql`. Feature UI and cross-service coordination remain planned; own-domain restaurant and dining APIs are implemented. Environment settings cover both implemented restaurant/runtime settings and planned
peer calls. The monolith continues to use its own configuration. Update this
inventory alongside implementation, including any added settings and defaults.
The user confirmed student/prefix `afijo2024` and class group `rg-sdd-3a` on 17 November; registry namespace follows repository owner `AFG64`. Resource names are proposed, not provisioned. Public URL and
CORS origin currently describe localhost only. Confirm identities and replace
all placeholders with actual resources/URLs before Azure setup; this file is not
a deployment configuration. No secret values are stored here.

Both image builds and local isolated SQL checks now run in CI; a successful remote
run is still required before the first PR merges. No Azure access or deployment is part of this baseline.


Milestone 4: own-domain history/item/bill endpoints are implemented, with binary
bill contents in SQL and scoped download checks. New visit POST and history DELETE
remain explicitly unavailable until milestone 5 coordinates restaurant writes.
The internal visit writer is validated but is not exposed as an uncoordinated
mutation. OpenAPI records these temporary gates. Coverage now gates restaurant
and dining core modules independently; CI also runs disposable real SQL transfers.
