# Official system schema — 19 November 2026

`system.schema.json` is the professor-provided Blackboard schema, copied byte for
byte from the supplied Downloads file. It supersedes the student-authored schema
created while the official file was missing. No official schema fields were
modified. SHA-256: `a6d6b1f8cca72724cdcbf24a0ceaaa7d7ad94210d17456791ab5854bdf94fa05`. A regression check detects accidental edits.

The course announcement supplied by the user explicitly requires replacement of
any custom schema. Its new Storage static website fields match the supplied
Azure deployment guide. Our previous schema acceptance does not establish
compliance; validation now runs against this official document in existing CI.

The official schema requires HTTPS public_url, ui.storage_account (3–24 lowercase
letters/digits), PORT and DATABASE_URL environment declarations, and timeouts no
greater than 30 seconds. Nonsecret defaults cannot be null; secrets have no
default. Calls, service description and health are optional in the official
format. The existing separate semantic checks still validate declared peer
references, URL settings and called OpenAPI endpoints; they do not alter the
schema and now accept omitted optional calls.

system.yaml declares the confirmed afijo2024 naming, proposed personal group
rg-afijo2024 and proposed storage account afijo2024ui. Availability is unverified.
https://not-deployed.invalid is an explicit reserved placeholder, not a live
endpoint. Local UI_ORIGIN stays http://localhost:8080; application behavior is
unchanged. Replace the public URL with the discovered Storage primary web
endpoint and deploy the actual origin to the services once resources exist.

The guide also includes a managed identity and Log Analytics workspace. The
official schema has no fields for these resources and rejects extra properties,
so the full proposed inventory is recorded in AZURE_READINESS.md rather than
inventing schema fields. No Azure setup, identity, permission or deployment is
claimed by a successful schema check.
