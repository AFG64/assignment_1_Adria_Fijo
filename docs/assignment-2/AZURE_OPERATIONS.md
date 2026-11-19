# Azure setup and operation

This is technical documentation, not a personal ADR or report. No resources are
claimed deployed. `infra/azure/plan.json` is the nonsecret proposed target,
derived from the authenticated IE username and verified GitHub IDs. It proposes
France Central for both app and SQL, within the subscription's current allowlist.
Name availability and actual free-offer acceptance must pass before use.

## Initial setup

Run from the repository root with the project environment, Azure CLI, Bicep CLI
(validated with 0.39.26), GitHub CLI and Docker available. Review the plan first:

```sh
az account set --subscription fba03120-1f24-4f01-9d1f-038a4b705cad
python scripts/azure_setup.py plan
python scripts/azure_setup.py preflight
az bicep build --file infra/azure/main.bicep --outfile /tmp/picky-template.json
```

The plan and preflight do not create resources. Preflight checks the exact
Students subscription/tenant, permitted regions, system manifest, real GitHub
numeric IDs, professor directory identities and globally unique resource names.
Fresh subscription resource providers may initially return SubscriptionNotFound;
record that failure instead of switching to the enterprise IE subscription.

After the user approves the concrete plan, the one-time setup command is:

```sh
python scripts/azure_setup.py apply --client-ip <your-public-IPv4>
```

This command is not run by CI and must not be run before authorization. It prompts
for `AZURE_SQL_ADMIN_PASSWORD`, `RESTAURANTS_DB_PASSWORD` and `DINING_DB_PASSWORD`
(or reads those environment variables). Keep three distinct strong passwords in
your password manager, including for any partial-setup retry. Never pass them in
shell command text or save them in the repository. The admin password is not
stored in GitHub or a service. Temporary secure parameter files live outside the
repository and are removed on normal completion/error; CLI failure details are
suppressed because Azure may echo input values.

The setup performs these operations in order:

1. Verify the exact target and identities; validate secrets before cloud writes.
2. Register App, OperationalInsights, Sql, Storage and ManagedIdentity. Recheck
   names and create only the tagged personal resource group.
3. Deploy `infra/azure/main.bicep`: Standard_LRS StorageV2, retained 30-day
   Log Analytics workspace, Consumption environment, one SQL logical server,
   two GP Gen5 serverless databases (0.5–1 vCore), and one managed identity.
   SQL uses the free offer with exhaustion AutoPause and local backups; it never
   substitutes a paid SKU. Size/auto-pause overrides are omitted per course guide.
4. Grant the managed identity Contributor on this group and Blob Data Contributor
   on this storage account. Grant the setup user Blob Data Contributor on this
   account so website hosting can be enabled without storage keys. Shared-key
   authentication is disabled. Give the two named professors group Reader.
   Both main-branch OIDC subject forms are derived from verified repository IDs.
5. Enable Storage static website with index.html; create the two placeholder
   Container Apps only if missing, 0–1 replicas and 0.25 CPU/0.5 GiB each. A setup
   retry does not reset an app's existing image to the placeholder.
6. Temporarily allow only the supplied personal IPv4 through SQL's firewall.
   Create a contained `picky_<service>` user in each database, granting
   db_ddladmin/datareader/datawriter, verify its password/own database, and remove
   the temporary rule in a finally block. Azure-services firewall access remains.
   Applied schemas/data are never dropped or recreated by setup.
7. Store the five declared repository secrets and three variables with GitHub CLI.
   Database passwords go over stdin, not shell arguments. No application image
   is deployed by setup; application changes must subsequently use the pipeline.

If setup fails, inspect Azure's actual deployment/resource state before retrying.
Retain the same passwords, verify removal of `temporary-bootstrap`, and do not
delete databases to recover. An existing group without the Picky ownership tag is
refused. Initial setup can grant roles; the pipeline cannot change role grants.
Do not rerun initial setup as the routine deployment mechanism.

## Before migration 002

The first application deployment must contain only migration 001. Populate
synthetic records, verify both domains and bill bytes, and stop so the user can
capture the baseline. Never deploy 002 until the user explicitly confirms those
records and their before evidence. Do not automatically transfer private local
Assignment 1 records to the public cloud. The existing offline transfer tool is
available for an explicitly chosen, quiescent, copied source; it is not run by CD.

The user writes the hosting/migration/pipeline ADRs and AI usage records, and
collects screenshots/run links/logs. Passing local tests does not establish cloud
deployment, access, successful OIDC, public GHCR pulls or evidence completion.

References: supplied course guide (`AZURE_DEPLOYMENT_GUIDE.txt`),
[SQL database resource properties](https://learn.microsoft.com/en-us/azure/templates/microsoft.sql/2023-08-01/servers/databases),
[Storage static website setup](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-static-website-how-to),
and [Container Apps probes](https://learn.microsoft.com/en-us/azure/container-apps/health-probes).
