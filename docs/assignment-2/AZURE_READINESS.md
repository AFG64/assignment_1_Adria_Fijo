# Azure readiness — updated 19 November 2026

The user supplied the updated course deployment guide and announcements on
19 November. **Individual Assignment 2 uses the student's own Azure for Students
subscription.** The shared IE subscription/class-group plan is superseded; the
separate group-project instructions in the guide do not apply to this repository.
Confirmed username/prefix: afijo2024. Class 3A is not the deployment scope.
No cloud resource has been created or verified. `az account list` currently shows
no signed-in accounts. Authenticate locally with `az login`, check subscription
state and choose the active Azure for Students subscription. Never put account
passwords, verification codes or tokens in chat or Git.

## Proposed inventory (not provisioned)

| Resource | Proposed name | Updated required configuration |
|---|---|---|
| Resource group | rg-afijo2024 | Create in the student's verified active subscription, after authorization |
| Storage account/static website | afijo2024ui | StorageV2, Standard_LRS, index.html; name availability unverified |
| Pipeline managed identity | afijo2024-github | OIDC; Contributor on this resource group only |
| Container Apps environment | afijo2024-env | Consumption workloads |
| Log Analytics workspace | Name to be discovered/confirmed during environment setup | Keep the environment's log workspace; allowed by new announcement |
| Restaurant Container App | afijo2024-restaurants | Public HTTPS; min 0/max 1 replica |
| Dining Container App | afijo2024-dining | Public HTTPS; min 0/max 1 replica |
| SQL logical server | afijo2024-sql | Two owned databases, encrypted connections, contained users |
| Restaurant SQL database | afijo2024-restaurants-db | GP Gen5 serverless free offer, 0.5–1 vCore, local backups |
| Dining SQL database | afijo2024-dining-db | Same free-offer settings |

Get the subscription's allowed regions from its policy assignment before choosing
a region. Verify actual free-offer availability. The guide permits SQL in another
allowed region if necessary. For the free offer, use `--use-free-limit true` and
`--free-limit-exhaustion-behavior AutoPause`; the guide fixes auto-pause at 60 minutes
and size at 32 GB, so do not pass `--auto-pause-delay` or `--max-size`. These
supersede the earlier shared-subscription 2 GB/shortest-delay plan. Live SKU/region
support must still be checked at setup; no Azure bill or credit balance checked.

Register Microsoft.App, Microsoft.OperationalInsights, Microsoft.Sql,
Microsoft.Storage and Microsoft.ManagedIdentity in the selected personal
subscription as part of authorized initial setup. Do not apply setup to the
shared IE/group-project subscription. Contained service users get db_ddladmin,
db_datareader and db_datawriter in their own database, without peer access.
Local compose still uses its existing SQL logins; Azure user provisioning and
least-privilege migration/lock checks belong to infrastructure verification.
Open SQL firewall to a personal IP only for setup, then remove that exception.

## Identity, permissions and pipeline

Use a user-assigned managed identity rather than a class service principal.
Create OIDC federation for the exact GitHub main subject, issuer
https://token.actions.githubusercontent.com and audience api://AzureADTokenExchange.
The guide calls for name and numeric-ID subject forms; derive actual owner/repo
IDs and verify them, never guess. Avoid zsh interpolation of `:ref` by using Bash
or braced variables. Grant Reader on this resource group to the two professors
named in the supplied guide as an explicit part of approved initial setup.

Planned GitHub secrets: AZURE_CLIENT_ID, AZURE_TENANT_ID,
AZURE_SUBSCRIPTION_ID, RESTAURANTS_DB_PASSWORD, DINING_DB_PASSWORD.
Planned repository variables: PREFIX, RESOURCE_GROUP, UI_STORAGE.
Enter secrets securely in repository settings; names are planned and no CD
workflow consumes them yet. No AZURE_CREDENTIALS class secret or Static Web App
deployment token is part of the updated plan.

CD implementation remains milestone 9: main-only workflow calls reusable CI for
the same SHA, publishes both SHA-tagged GHCR images with packages:write and
provenance:false, authenticates with id-token:write, deploys Container Apps,
generates ui/config.js, uploads ui/ to Storage's $web container and polls health.
When reusable CI is introduced, exclude main from its standalone push trigger to
avoid duplicate runs. Do not disable the present main CI until CD invokes it.

Keep ingress-level CORS off; application CORS must permit only the discovered
Storage website origin and Content-Type. Keep cold-start failure/retry messages
in the UI. Azure setup may create the guide's placeholder Container App images;
application image deployment then happens only through the pipeline. GHCR
packages need verified public pull access. Do not manufacture a failure as
assignment evidence; retain real failure/fix runs if they occur.

## Remaining access and approval steps

1. User signs in locally; select the active personal Azure for Students subscription.
2. Read-only verification of active state, allowed regions, providers, existing
   own-prefix resources, resource-name availability and relevant permissions.
3. Implement/validate the exact setup/CD configuration and present the concrete
   resource plan for authorization before creating resources, changing roles or deploying.
4. Document actual setup commands in the technical README as they are run,
   without secrets. After setup, changes/deployments run through the pipeline.

## Mandatory migration checkpoint

Deploy 001-only baseline through the pipeline and populate synthetic records.
Stop for the user's before evidence. Do not create/deploy 002 until the populated
baseline and captured evidence are explicitly confirmed. Applied migrations must
never be edited. AI usage, ADR-8, report/disclosure and evidence are user-owned.

Sources: supplied updated Azure deployment guide, searchable copy in
[AZURE_DEPLOYMENT_GUIDE.txt](AZURE_DEPLOYMENT_GUIDE.txt), and the 18/19 November
course announcements supplied by the user. The original BRIEF.txt is historical;
see [requirement updates](REQUIREMENT_UPDATES.md) for the changes applied here.
