# Azure setup and operation

This is technical documentation, not a personal ADR or report. Initial resources
were provisioned on 20 November; see AZURE_READINESS.md for the verified inventory.
`infra/azure/plan.json` is the nonsecret deployment target,
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

## Main release pipeline

`ci.yml` runs on every feature push/PR and is reusable through workflow_call.
`cd.yml` runs only on main pushes and calls those exact CI gates on the same SHA.
CI builds both images and runs SQL tests only against its disposable local
container. Bicep compilation, workflow lint and the migration checkpoint also run
without cloud credentials; none connects to Azure SQL.

After CI succeeds, two publish jobs build linux/amd64 images with VERSION set to
the SHA and publish `ghcr.io/afg64/picky-restaurants:<SHA>` and
`ghcr.io/afg64/picky-dining:<SHA>`. Provenance/SBOM manifests are disabled per the
course deployment guide. The source label connects each package to the repo.
`GITHUB_TOKEN` has packages:write only in this job. GHCR initially makes new
packages private: make the two packages public as part of initial setup, then
rerun the actual failed release if needed. Do not invent a failed run as evidence.

The deploy job signs in via main-only OIDC and has id-token:write. It verifies the
exact subscription and expected variables, and verifies anonymous access to both
SHA images using an empty Docker configuration. Private images stop the release
before app updates. Deployment concurrency is serialized, with in-progress runs
allowed to finish. There is no branch/manual deployment trigger.

After initial setup, discover the actual Storage primaryEndpoints.web address
and commit it as system.yaml public_url **before merging the first release**.
The script refuses a mismatching/reserved URL; it never invents the `z<N>` host.
It discovers both existing Container App HTTPS ingress addresses and injects
each service's peer URL, UI origin, port and version. Each DATABASE_URL is a
Container App secret; the environment references its name. No database secret
goes into UI files or CLI error output. Azure ingress CORS is absent; the Flask
application accepts only the exact website origin.

Each app uses Single revision mode, Consumption, 0–1 replicas and 0.25 CPU/0.5 GiB.
A startup HTTP /health probe permits five minutes for migration/SQL resume;
subsequent readiness/liveness use TCP so probes do not keep SQL awake. TCP health
only proves a listening process; API own-data readiness is assessed by /health
and normal API error responses. Independent release checks poll both services
for at most six minutes each in parallel, requiring HTTP 200, status/db ok and
the **new SHA**, so the old running revision cannot make a release appear passed.

Only after both APIs pass does the job copy ui/ to a temporary staging directory,
generate public config.js and release.json, and upload to Storage's `$web` with
identity authentication and no-store cache headers. Published config and SHA are
read back before success. No service schema/data is reset, and CI/CD never imports
the private SQLite source. These app updates and UI uploads are separate writes,
not an atomic release; if one fails, inspect the run/startup logs and rerun the
same commit after fixing its cause. Do not restore an image missing an applied
migration; recover schema through a new forward migration.

## Before migration 002

The first application deployment must contain only migration 001. Populate
synthetic records, verify both domains and bill bytes, and stop so the user can
capture the baseline. Never deploy 002 until the user explicitly confirms those
records and their before evidence. Do not automatically transfer private local
Assignment 1 records to the public cloud. The existing offline transfer tool is
available for an explicitly chosen, quiescent, copied source; it is not run by CD.

`infra/azure/migration-checkpoint.json` currently permits version 001 only, with
before_evidence_confirmed false. CI and deployment both reject a later migration.
Only after the user's explicit confirmation may a change raise maximum_version
and record before_evidence_confirmed true alongside the new migration. The file
is an operational release gate, not an authored evidence/AI/ADR record.

After an authorized, successful 001 application release:

```sh
python scripts/azure_baseline.py plan      # offline description only
python scripts/azure_baseline.py populate  # explicitly creates synthetic records
python scripts/azure_baseline.py inspect   # reads IDs, item values and exact bill bytes
```

Population is not part of CI/CD. It checks the reviewed Azure target, warms both
own-health endpoints, then reads existing synthetic records before each optional
write. It never automatically retries a POST, imports private data or deletes a
record. Repeating after an uncertain write first reads the current state; duplicate
markers are an error. Inspection returns stable IDs, visited status and the bill
hash for technical verification; the user still captures/selects their own
before/after evidence. An incomplete or changed baseline fails explicitly.

`scripts/check_baseline_local.py` exercises this exact population/inspection flow
against local real HTTP/SQL and cleans only its UUID-named synthetic records.
`scripts/check_azure_roles.py` creates disposable databases inside the local SQL
container with contained users and precisely the proposed Azure roles. It verifies
first/repeat migrations, health writes, app locks, repeat seeding, absence of
db_owner and denial of peer-database access. Test databases are removed and the
instance's original contained-authentication/advanced-options settings restored.
Both checks run in CI; neither contacts Azure. Local compatibility does not replace
verifying the real Azure service users during initial deployment.

The user writes the hosting/migration/pipeline ADRs and AI usage records, and
collects screenshots/run links/logs. Passing local tests does not establish cloud
deployment, access, successful OIDC, public GHCR pulls or evidence completion.

References: supplied course guide (`AZURE_DEPLOYMENT_GUIDE.txt`),
[SQL database resource properties](https://learn.microsoft.com/en-us/azure/templates/microsoft.sql/2023-08-01/servers/databases),
[Storage static website setup](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-static-website-how-to),
and [Container Apps probes](https://learn.microsoft.com/en-us/azure/container-apps/health-probes).
Pipeline references:
[reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows),
[GHCR publishing and visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## Initial setup execution — 20 November

The user requested completion of milestone 7 and Azure after reviewing the plan.
Registered the five providers, then preflight verified the Students subscription,
allowed France Central region, real repository/owner IDs, professor identities
and resource-name availability. Ran the documented apply command using the
current personal public IPv4 and three distinct generated credentials retained
in macOS Keychain (details in AZURE_READINESS.md, no values).

The first Bicep operation partially succeeded but failed one federated credential
with ConcurrentFederatedIdentityCredentialsWritesForSingleManagedIdentity. Added
@batchSize(1) to serialize this resource loop, compiled and resumed the same
owned group/resources/passwords. The second deployment succeeded. This is a real
initial ARM setup failure, not a failed GitHub CI run. See Microsoft's
[concurrent credential restriction](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-considerations).

Both free-offer databases reported the required SKU/limits. Contained user
verification passed, the temporary SQL rule was removed in finally, and the
repository secret/variable names were verified after configuration. The discovered
website endpoint was committed to system.yaml before the first application PR
merge. Subsequent application/image/environment/UI changes use the main pipeline;
do not rerun bootstrap as the release procedure.

## Live operating checks

The first main application release succeeded on 20 November. Public component
links are at the top of README.md. Read /health on each service and compare its
version with the successful main workflow; neither service's health depends on
its peer. release.json at the website reports the published UI SHA. config.js
contains only the two public API origins; no database credentials belong there.

To inspect a startup/SQL-resume problem, read console/system logs on the named
app. For example (no credential values):

```sh
az containerapp logs show --resource-group rg-afijo-ieu2024 --name afijo-ieu2024-dining --type console --tail 100 --format text
az containerapp logs show --resource-group rg-afijo-ieu2024 --name afijo-ieu2024-dining --type system --tail 100 --format text
```

The JSON log format is JSON Lines, not one JSON document. Migration startup logs
identify applied filenames and no-op reruns. Never fix a startup failure by
deleting a populated database or editing an applied migration. After a successful
release/release retry, verify stable synthetic IDs/item values and exact bill
bytes using azure_baseline.py inspect. This technical check does not collect or
confirm the user's report evidence or authorize 002.
