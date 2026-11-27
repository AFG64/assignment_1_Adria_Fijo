# Schema evolution and recovery

## Migration inventory

Restaurants has `001_init.sql`. Dining has `001_init.sql` and
`002_add_item_line_total.sql`. Applied files are immutable: the ledger stores
each filename, checksum and application time. Startup compares those checksums,
takes a transaction-owned migration lock, applies pending files in order and
commits schema changes and ledger entries together. Repeated startup applies
nothing. A changed or missing applied file prevents startup.

Dining 002 adds a persisted computed column to the populated visit_items table:

```sql
ALTER TABLE dbo.visit_items
ADD line_total AS (quantity * unit_price) PERSISTED;
```

SQL stores and maintains the result when quantity or price changes. The result
is decimal(23,2), large enough for the permitted integer quantity and
decimal(12,2) unit price. Unknown prices produce null totals; zero prices produce
zero. Existing IDs, dates, ratings, notes, timestamps and bill bytes are retained.
The baseline soup quantity 2 at unit price 3.50 therefore has line_total 7.00.

Visit history and successful item creation return line_total as a read-only,
nullable JSON number, alongside the existing unit_price. Neither field changes
the ownership boundary. Clients still submit item_name, quantity and optional
unit_price; supplying line_total is rejected. The UI displays totals to two
decimal places and leaves unknown prices/totals undisplayed.

## Local verification

Run these commands against the running local compose stack:

```sh
python scripts/check_item_migration.py
python scripts/check_azure_roles.py
python scripts/check_baseline_local.py
```

The item migration check creates its own uniquely named local database, applies
001, inserts populated visits/items and the valid synthetic PDF, and only then
applies 002. It compares every original data column, bill bytes and original
ledger row. It checks persisted decimal metadata, missing/zero/fractional/maximal
prices, new inserts, automatic recalculation and a repeated no-op migration.

Recovery fixtures exist only in a temporary directory inside that disposable
database. A deliberately failing pending migration must roll back its DDL, row
updates and ledger entry. Changed applied files and an image missing 002 must
be rejected. A separate new forward fixture must apply once without changing
the original data. Fixture databases are removed by the check; fixture 003 files
never enter the application's migrations folder or Azure.

The contained-user check verifies the same migration set under the deployed
role combination, without db_owner or peer-database access. The baseline check
creates only its UUID-named local records, stops and restarts the local SQL
service, and verifies health 503 then 200, request-log fields, the unchanged IDs,
item total and PDF bytes. This briefly interrupts both local APIs. Its finally
blocks restart SQL and remove only its own synthetic records. None of these
checks connects to Azure SQL or removes the normal local SQL volume.

## Azure release and paired evidence

The [before bundle](evidence/2026-11-26-before-002/README.md) records the live
001-only system at source 0d313d7, including screenshots, original data/PDF,
startup logs, source checksums and successful deployment references. The user
approved that bundle on 27 November. The source checkpoint now permits version 2
with before_evidence_confirmed=true; a source file does not prove deployment.

Publish through a reviewed feature PR and passing CI. Main's pipeline repeats
CI on the exact main SHA, publishes both SHA-tagged images and updates the
existing apps. Service startup applies migrations; CI never connects to Azure
SQL. Do not run initial setup again or apply SQL manually from a workstation.

After the first 002 deployment, compare both health versions and UI release.json
with the successful main SHA. Run the read-only inspection:

```sh
python scripts/azure_baseline.py inspect
```

Expected existing IDs remain restaurant 15/saved 1/visit 1/item 1/bill 1, with the
same visited status, date 2026-11-01, rating 4, item quantity 2 and unit price 3.50.
The new total is 7.00. The 648-byte bill SHA-256 remains
`abc73e5230c4d7659f95e0f4871c4e1aa3d77f16d49d2c2bea3c469e46ead63e`.
Restaurants must apply no new migration; Dining's first startup must log
`migration applied version=002_add_item_line_total.sql` and
`migrations committed applied=1`. Subsequent starts must log applied=0.

Pause before another release so the after UI/data, exact bill, successful run
and 002 startup line can be paired with the saved before bundle. Preserve the
before artifacts and their hashes. Never overwrite the before capture to make
it describe the later schema.

## Recovery rules

Inspect the exact SHA, startup logs and applied ledger before taking action.
A failed pending migration rolls back its transaction; retain the populated
database and diagnose the failing statement. An already applied migration is
never edited. Correct an applied schema through a reviewed new forward migration
and an explicitly approved checkpoint increase.

Do not redeploy an old image that contains only 001 after 002 has been applied:
the missing-file guard will reject it. An application rollback requires a new
image combining the earlier application code with every applied migration file
unchanged, checked against the evolved schema. It does not undo schema changes.
The disposable recovery checks enforce these limits.

Do not drop/recreate production tables, delete databases/volumes, rotate retained
credentials to mask a startup problem, or add resources outside the allowance.
Use the [Azure operating guide](AZURE_OPERATIONS.md) for authorized release/log
commands and the [coordination guide](SERVICE_COORDINATION.md) for partial writes.
