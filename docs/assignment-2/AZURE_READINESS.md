# Azure readiness — 17 November 2026

Naming confirmed by the user: **afijo2024**, **3A**. Existing class group:
`rg-sdd-3a`. This is a proposed inventory, not deployed infrastructure. No cloud
configuration has been changed. Infrastructure/CD implementation remains milestone 9;
show the final validated configuration and obtain authorization before provisioning.

| Resource | Proposed name | Required configuration |
|---|---|---|
| Container Apps environment | afijo2024-env | One environment; Consumption workloads |
| Restaurant Container App | afijo2024-restaurants | Consumption, public HTTPS, min 0/max 1 replica |
| Dining Container App | afijo2024-dining | Consumption, public HTTPS, min 0/max 1 replica |
| SQL logical server | afijo2024-sql | One server; separate service logins restricted to their database |
| Restaurant SQL database | afijo2024-restaurants-db | GP Gen5 serverless, min 0.5/max 1 vCore, 2 GB, local backups |
| Dining SQL database | afijo2024-dining-db | Same settings; shortest supported auto-pause delay verified at setup |
| Static Web App | afijo2024-ui | One static site; API URLs injected by main-only pipeline |

Region, subscription, name availability, supported SQL auto-pause minimum and
resource-group permissions remain unverified pending local Azure authentication.
Do not create a resource group or use resources belonging to another prefix.
No additional fixed-cost resources are planned. SQL firewall permits Azure
services; a personal IP exception, if needed, must be temporary and authorized.

Images will use `ghcr.io/afg64/...:<full-commit-sha>`; final image paths are selected
with CD implementation. Explicit job-level `packages: write` is needed for
publishing via `GITHUB_TOKEN`. Application deployment must run only through the
pipeline after CI passes on the same main SHA. CORS must use the actual SWA origin.

## Access checks

- Python and Docker are available; both local service images build and SQL runs.
- GitHub CLI authenticated as AFG64 with repository ADMIN permission.
- Actions enabled, all actions allowed; default workflow token read-only; automated
  PR review approval disabled. Merge, rebase and squash methods available.
- Latest `717f38f` CI passed: run 43959110968. No open PRs at inspection time.
- No repository Actions secrets or environments returned by GitHub at inspection.
- No branch protection or repository rulesets found. Changes must still reach main
  through passing PRs; no settings changed.
- Current local GitHub token lacks `read:packages`; registry package inventory
  could not be inspected (403). This does not establish whether Actions can publish.
- Azure CLI installed during readiness work. No logged-in accounts; subscription,
  resources, role assignments and group access cannot yet be checked.

Authenticate locally with `az login` using the IE account in Microsoft's page,
then request the read-only subscription/group check. Do not send credentials in chat.
The professor's class service principal belongs only in GitHub Actions secrets,
not in files, local CLI login commands or chat. Use the repository's Settings →
Secrets and variables → Actions to enter it securely when the workflow's exact
secret names and format are implemented. Proposed names are `AZURE_CREDENTIALS`,
`SQL_ADMIN_PASSWORD`, `RESTAURANTS_DB_PASSWORD`, `DINING_DB_PASSWORD` and
`AZURE_STATIC_WEB_APPS_API_TOKEN`; these are not configured or consumed yet.
Do not invent class credentials or generate the SWA token before approved setup.

## Mandatory deployment checkpoint

Initial pipeline deployment contains **001 only**, with synthetic data. Stop for
the user's populated-baseline before evidence. Do not create/deploy 002 until
that checkpoint is explicitly confirmed. Applied migrations must never be edited.
The user owns ADR-8, AI usage records and all evidence/report work.
