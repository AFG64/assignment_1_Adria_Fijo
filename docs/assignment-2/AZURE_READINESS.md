# Azure configuration and initial setup — 20 November 2026

The reviewed plan in infra/azure/plan.json was applied under the user's request
to complete milestone 7 and Azure. This is technical deployment documentation;
AI usage, ADRs, report and evidence remain user-owned.

## Verified initial setup

- Personal Azure for Students subscription fba03120-1f24-4f01-9d1f-038a4b705cad,
  tenant 4a39c578-6df0-42b9-a7e0-e9eac6d91816; Enabled, spending limit On.
- Actual IE username afijo.ieu2024, guide-derived prefix afijo-ieu2024.
- France Central is permitted by the live region policy and used for app/SQL.
  Other allowed regions at setup: denmarkeast, spaincentral, austriaeast,
  belgiumcentral. Provider registrations are now Registered.
- Initial Bicep deployment completed successfully after serializing the two
  federated credential writes. The first operation failed because concurrent
  credentials on one managed identity are unsupported; existing resources were
  resumed without deleting databases or changing names.

| Resource | Actual initial name/configuration |
|---|---|
| Resource group | rg-afijo-ieu2024, tagged Picky/student |
| UI storage | afijoieu2024ui, StorageV2 Standard_LRS, shared keys disabled |
| Website | https://afijoieu2024ui.z28.web.core.windows.net |
| Managed identity | afijo-ieu2024-github; both verified main OIDC subjects |
| Environment | afijo-ieu2024-env, Consumption |
| Log Analytics | afijo-ieu2024-logs, PerGB2018, 30-day retention |
| Restaurant app | afijo-ieu2024-restaurants, min 0/max 1, 0.25 CPU/0.5 GiB |
| Dining app | afijo-ieu2024-dining, same limits |
| SQL server | afijo-ieu2024-sql, TLS 1.2 minimum |
| Restaurant database | afijo-ieu2024-restaurants-db, GP_S_Gen5_1, min 0.5 vCore |
| Dining database | afijo-ieu2024-dining-db, same SKU |

Both databases report useFreeLimit true, exhaustion AutoPause, 60-minute pause
and 32-GiB maximum size, with local backup redundancy requested. The automatically
managed master database is not an extra application database. No paid-SKU fallback
was used. Actual cost/remaining-credit observations must be checked in Azure;
scale-to-zero does not make stored data/log retention free of usage charges.

## Access and secrets

The managed identity has Contributor only on this resource group and Blob Data
Contributor on the UI storage account. The setup user has storage-scoped Blob
Data Contributor for keyless website enablement. The two professors in the course
guide have Reader on this group. No role was granted on IE Workspaces.

Each contained picky_<service> SQL user was created and verified in its own
application database, with db_ddladmin, db_datareader and db_datawriter. The
bootstrap personal-IP firewall rule was removed; only AllowAzureServices remains.
Local compatibility tests also verify peer denial and non-db_owner access; real
application migration/health behavior is verified during first pipeline release.

Three distinct generated database credentials were saved in macOS Keychain,
account afijo.ieu2024, service names
picky-assignment-2/afijo-ieu2024/<AZURE_SQL_ADMIN_PASSWORD|RESTAURANTS_DB_PASSWORD|DINING_DB_PASSWORD>.
Values are never printed or stored in the repository. Retain them for recovery;
do not generate replacements on a partial retry. The admin password is not given
to an application or GitHub.

Configured repository secrets: AZURE_CLIENT_ID, AZURE_TENANT_ID,
AZURE_SUBSCRIPTION_ID, RESTAURANTS_DB_PASSWORD, DINING_DB_PASSWORD.
Configured variables: PREFIX, RESOURCE_GROUP, UI_STORAGE.
Container Apps receive their own DATABASE_URL through a secret reference at
release; UI configuration contains only public HTTPS API addresses.

## Pipeline and live verification

Applications are released only by cd.yml on main after the same-SHA reusable CI
passes. SHA-tagged GHCR packages must be public for anonymous Azure pulls;
provenance is disabled per the course guide. Static UI upload uses identity-based
blob access. Application CORS permits only the discovered website origin; ingress
CORS is absent. Cold-start health polling requires own SQL read/write and the
new SHA before the UI is published. See AZURE_OPERATIONS.md for commands/recovery.

The initial setup created placeholder app images; it did not deploy the application
or populate private/local data. Check the latest successful main workflow and
live health version for the actual release state. No screenshot/evidence task is
completed merely by this configuration or the local tests.

First deploy 001 only, then populate/verify the synthetic baseline. STOP so the
user can capture before evidence and explicitly confirm it before migration 002.
The committed migration checkpoint remains maximum_version=1 and
before_evidence_confirmed=false. Do not edit an applied migration or import
private Assignment 1 records without a separate explicit request.

## First application release

PR #10 passed both branch/PR CI gates and merged at
aa656e31904fb5b2b84322a5e15dc30f053d18a3. Main's
[CI/CD run 44640494444](https://github.com/AFG64/assignment_1_Adria_Fijo/actions/runs/44640494444)
passed on that same SHA. Both service /health responses report status/db ok and
that version, and the Storage config.js/release.json readback matches. The actual
packages were already Public when inspected; anonymous exact-SHA manifest checks
passed without changing visibility. No failed GitHub workflow is claimed from
the separate initial ARM credential-concurrency failure.

Current API origins are the public Container App ingress hosts:

- https://afijo-ieu2024-restaurants.wonderfulsmoke-a09dc47c.francecentral.azurecontainerapps.io
- https://afijo-ieu2024-dining.wonderfulsmoke-a09dc47c.francecentral.azurecontainerapps.io

The UI calls these origins directly over HTTPS, with application CORS restricted
to the Storage website. See the latest successful main release for subsequent
versions; resource names/origins remain the same across those releases.
