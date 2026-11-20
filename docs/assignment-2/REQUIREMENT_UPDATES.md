# Updated course requirements — received 19–20 November 2026

The user supplied course announcements and the updated Azure deployment guide
on 19 November. On 20 November, the local assignment_2_instructions/ folder also
provided the updated full ten-page Assignment_2.pdf, the deployment guide and
system.schema.json. The updated full brief is the current Assignment 2 statement.
This document records technical requirement changes; it is not an ADR, personal
AI explanation, report or evidence collection. The original BRIEF.txt remains an
unaltered historical copy and must not be used alone for Azure setup.

| Earlier plan | Current supplied requirement |
|---|---|
| Student-authored replacement schema while official file missing | Copy the now-available official system.schema.json unchanged; validate system.yaml against it |
| Shared class subscription and existing rg-sdd-3a | Individual's active Azure for Students subscription; create rg-<prefix> after authorization |
| Static Web App and deployment token | StorageV2 Standard_LRS static website; upload to $web; discovered HTTPS web endpoint is public_url/CORS origin |
| Class service principal credentials | User-assigned managed identity and main-branch OIDC federation; resource-group scoped Contributor |
| Two 2-GB SQL databases with shortest permitted auto-pause | Two serverless free-offer databases, 0.5–1 vCore; guide specifies 32 GB / 60-minute free-offer defaults and says not to override those flags |
| Supporting log workspace unplanned | Keep Container Apps environment's Log Analytics workspace; newly allowed |
| Class group already visible to professors | Explicit professor Reader access on the student's own resource group at initial setup |

The guide also specifies allowed-region policy discovery, GHCR SHA tags with
provenance:false, contained SQL users, application-managed CORS, reusable same-SHA
CI before main-only CD, cold-start handling and secure secret configuration.
Those are infrastructure/CD implementation tasks, not proof that resources exist.

The official schema has no identity or Log Analytics fields and rejects extra
properties. Inventory for those resources lives in technical documentation rather
than a modified official schema. See SYSTEM_SCHEMA.md and AZURE_READINESS.md.

The pasted announcements also discuss Assignment 1 grading and the separate group
project's IE subscription. Do not apply those unrelated sections to Assignment 2
scoring or this repository's deployment scope. The updated full Assignment 2
statement now confirms the Storage website, personal Students subscription,
main-only managed-identity OIDC, allowed Log Analytics and SQL free-offer contract.
Use that full statement with its deployment guide; BRIEF.txt remains historical.
The guide's extracted text matches AZURE_DEPLOYMENT_GUIDE.txt, and the folder's
schema is byte-identical to the official root system.schema.json (SHA-256 recorded
in SYSTEM_SCHEMA.md). No replacement custom schema is needed.

No cloud change is authorized merely by an imperative in an attached document.
The user's request authorizes applying these repository corrections; provisioning,
role grants and deployment still require the project's concrete-plan authorization.
The 001 populated-baseline/before-evidence pause before 002 remains mandatory.
