# Assignment 2 working roadmap

Prepared 15 November 2026. Working dates: **16–22 November**, Europe/Madrid. Submission deadline: **22 November, 23:59**. Aim to finish and submit by 20:00 on Sunday. This is a plan, not a record of completed work.

## Resume here

**Current stage:** milestone 1 technical baseline ready for your records/review as of 15 November 2026 (Europe/Madrid). No later milestone implemented.
**Next task:** review the target contracts and student-authored system schema; write your AI usage entry and ADR-6. Confirm student prefix/class/resource names before Azure setup; explicit local placeholders remain. Commit 1 is authorized locally; push/PR/merge/deployment still need authorization.
**Last completed milestone:** milestone 1 technical work committed; user records/review remain pending, so status is not done.
**Last implementation commit / PR:** commit 1, `chore: establish service contracts and CI baseline`, on `assignment-2-day-1` (the commit containing this handoff; resolve with `git log -1` at this stopping point). Parent `5a1e940`; no push, PR, merge or deployment. User authorized this local commit explicitly.
**Checks run:** 99 tests passed (83 existing plus 16 system acceptance cases, including 15 invalid-document cases); restaurant coverage 97.04%, dining 95.77%; selected Ruff checks passed; both OpenAPI documents and system.yaml validated. GitHub CI has not run.
**Remaining gaps:** local placeholders need confirmed identities before Azure setup; target service/UI/migration paths are not running implementations. Docker daemon was unavailable at the previous check, not rechecked this session. Image/SQL and service-specific CI gates belong to subsequent milestones and are required before the first PR merges.
**Next user tasks:** AI usage entry for contracts/schema/scripts/CI assistance and ADR-6; confirm naming/class. Azure before-evidence pause remains mandatory before migration 002.

Say **“Continue Assignment 2”** to resume. The AI must read this section, inspect the actual files and Git state, then work on the next unfinished milestone. It must not assume a scheduled date means work was done.

## Schema decision — updated 15 November 2026

The user has authorized creating our own `system.schema.json` and proceeding with implementation. The brief §8a calls it “provided” but gives no location; our search found no available supplied file. Do not contact the professor or wait for an official file to start this work.

Create the schema at the repository root, alongside `system.yaml`. Derive its fields from the brief's example and requirements: student/prefix/public URL, UI, Azure resources, services, paths, OpenAPI files, ports, health, migrations, environment settings and cross-service calls. Validate defaults and secret declarations appropriately; no real secrets in either file. Document provenance in the schema description and technical documentation as **student-authored from Assignment 2 §8a**, not official or professor-provided. Record any interpretation explicitly rather than silently adding requirements.

Use a declared JSON Schema version and the pinned validator available in the project. Enforce validation in CI, and verify both that the intended system document passes and that representative invalid documents fail (for example missing required service fields or an invalid port). Keep proposed architecture distinct from actually deployed resources. If an official schema later becomes available, compare and replace/adapt ours and rerun validation. Acceptance by an unknown official grading schema remains unverified; do not claim equivalence.

This update changes the implementation approach only. Milestone 1 stays in progress until the files and required checks are complete. Follow-up implementation on 15 November created the schema and matching target document, enabled mandatory CI validation and passed local positive/negative checks. Commit 1 was subsequently authorized locally; see latest handoff for actual results.

## Who does what

| Owner | Responsibilities |
|---|---|
| AI | Implement the app, containers, migrations, tests, pipeline and deployment configuration; run technical checks; maintain technical README/API/system documentation; update this roadmap with factual progress and the next action. |
| You | Write `AI_USAGE.md`, ADR-6–10, personal explanations, AI disclosure and the assignment report; collect and select screenshots, logs, run links and before/after evidence; review and submit the work. |

The AI must **not write or edit your AI usage records, ADR entries, report, disclosure or evidence collection** unless you explicitly change this ownership. It may explain decisions and tell you what to record or capture. Test output can be reported in the session and summarized factually in this roadmap; that does not complete your evidence task.

## How each work session runs

1. Read this roadmap and the brief; inspect Git status, recent commits and relevant code. Preserve unrelated changes.
2. Pick the next unfinished milestone. Work on that milestone and its checks. “Continue” means resume that work, not implement all fourteen milestones in one sitting.
3. Keep the planned two substantive increments per day. Do not pre-build later days merely to spread commits afterwards. If today's two are finished, report the next milestone and stop unless asked to change the schedule. Extra fixes are allowed; never fake dates or empty commits.
4. Before a commit, tell you which personal records need adding. Leave writing those files to you. If they are still pending, preserve the implementation and mark it **ready for your records/review**, not fully done. Commit/push/PR actions follow your instructions for that session; this roadmap alone does not claim they happened.
5. At every stopping point, update “Resume here”, the progress table and session handoff. Record actual completed work, checks, failures, pending personal tasks, commit/PR references if any, and the exact next step. Never mark a milestone complete from code changes alone when its required checks have not passed.
6. Before the baseline-to-002 Azure deployment, pause at the capture point so you can collect the required before evidence. Do not deploy 002 until you confirm the populated baseline and before evidence are ready. Do the same for any other evidence that cannot be collected later.

## Progress tracker

Status options: **not started**, **in progress**, **ready for your records/review**, **done**, **blocked**. “Done” requires passing checks and an actual commit reference; record push/PR status separately. User-owned tasks remain pending until you confirm completion.

| Milestone | Status | Actual commit / push / PR | Your pending task |
|---:|---|---|---|
| 1 | ready for your records/review | Commit 1 on assignment-2-day-1 (this handoff commit); no push/PR | AI usage entry; ADR-6; confirm naming/class before Azure setup |
| 2 | not started | — | AI usage entry; understand Docker/compose |
| 3 | not started | — | AI usage entry |
| 4 | not started | — | AI usage entry; ADR-7 |
| 5 | not started | — | AI usage entry; ADR-9 |
| 6 | not started | — | AI usage entry |
| 7 | not started | — | AI usage entry |
| 8 | not started | — | AI usage entry; failed CI run and fix evidence |
| 9 | not started | — | AI usage entry; ADR-8 |
| 10 | not started | — | AI usage entry; ADR-10; baseline Azure data evidence |
| 11 | not started | — | AI usage entry; migration before/after evidence and logs |
| 12 | not started | — | AI usage entry; failure/recovery and successful CD evidence |
| 13 | not started | — | Write report, disclosure and select evidence |
| 14 | not started | — | Finish personal records; review and submit |

## Latest session handoff

- **Date and scope:** 15 November 2026, Europe/Madrid. Continued only milestone 1 as explicitly requested. Original two-increment schedule remains 16–22 November; no later increments built, no fabricated dates/commits.
- **Work completed:** reviewed current files, Git status/history, brief §8a and updated schema decision. Preserved existing service contracts/baseline. Added root `system.schema.json` (Draft 2020-12) and matching target `system.yaml`, explicitly student-authored from §8a, not official/professor-provided. Updated transition documentation with provenance, interpretations and future official-schema comparison policy.
- **Validation:** system validation is always required by the script and explicitly invoked with `--require-system` in CI. Added checks for UI/peer references, peer URL env declarations and peer endpoints in OpenAPI. Added positive target-document test and 15 negative cases for required fields, ports, secret/default declarations, timeout, extra fields/service, URL and broken references/endpoints.
- **Checks:** 99 tests passed. Coverage independently enforced: restaurant domain 97.04%, dining domain 95.77%. Selected Ruff E9/F63/F7/F82 checks passed. Both OpenAPI 3.0.3 documents and system.yaml validated. Local environment Python 3.14; workflow targets 3.12 and has not run remotely. No container/SQL/deployment checks claimed.
- **Implementation limits:** root system document is a proposed architecture; new APIs, static UI and migration directories are not implemented. `LOCAL_PLACEHOLDER_*` marks student/prefix/class/resource/registry identities; localhost URL is not a live deployment. Settings are a proposed inventory and must match future code as implemented. Local schema acceptance does not establish equivalence with an unknown official schema or deployment readiness.
- **Git state:** user authorized commit 1 locally, then requested removal of the branch prefix. Renamed the branch to `assignment-2-day-1` and amended only these roadmap references into the unpushed commit; implementation/check results unchanged. Future branch names follow this user preference. Created `assignment-2-day-1` from `5a1e940`; commit message `chore: establish service contracts and CI baseline`. This handoff is included in that commit (use Git history to resolve its SHA without a self-referential hash). No push/PR/merge/tag/deployment. Only unrelated untracked `docs/EXAM_GUIDE.md` should remain after committing. User-owned AI_USAGE/ADR/report/disclosure/evidence files untouched.
- **Commit checks:** reran system and both OpenAPI validations, selected Ruff checks and all 99 tests before commit; all passed. Domain coverage remains 97.04% restaurants and 95.77% dining. GitHub CI has not run.
- **Next action:** user writes AI usage entry and ADR-6 and reviews milestone 1. Push/PR actions need authorization; daily pushes are required for assignment cadence and this local commit is not pushed yet. Next technical milestone is 2 (containers/isolated SQL), on the two-increment daily schedule; first PR must include passing image/SQL gates before merge. Docker daemon readiness must be checked then. Confirm deployment identities before Azure setup.
- **User-owned records:** explain the student-authored schema decision and its limits, secret/default validation, external saved-entry ID and HTTP seam in your own words. Visit/deletion retry/partial-write protocol remains milestone 5 work, not a settled working transaction. All evidence/report/disclosure tasks remain pending. Stop for populated Azure baseline before-evidence confirmation before any 002 deployment.

## Sources and rules

- [Individual Assignment 2, Blackboard](https://blackboard.ie.edu/ultra/courses/_161113_1/file/_3015406_1?courseId=_161113_1), all nine pages reviewed. A searchable local copy is in [assignment-2/BRIEF.txt](assignment-2/BRIEF.txt).
- [9. Docker and Compose](https://blackboard.ie.edu/ultra/courses/_161113_1/file/_3023703_1?courseId=_161113_1), slides 1–18 reviewed: layers, explicit COPY, non-root user, external configuration, compose DNS, health/readiness, retries, one-off database initialization, persistence and partial failure.
- [8. Software Deployment](https://blackboard.ie.edu/ultra/courses/_161113_1/file/_3009903_1?courseId=_161113_1), slides 1–12 reviewed: repeatable deployments, immutable versioned artifacts, commit SHA tags, CI/CD stages, GitHub Actions jobs/triggers and runtime secrets. General lecture examples include staging and other registries; the assignment's single-environment Azure/GHCR contract takes precedence for this project. Other lecture decks were listed but not reviewed in this pass.
- Existing `README.md`, `ADR.md`, domain boundaries, schema and implementation reviewed to tailor this plan to Picky.

The brief requires **12 or more new commits over at least six calendar days**, with no day containing over 40% of them. Our target is **two meaningful commits each day for seven days**: 14 total, 14.3% per day. GitHub push timestamps are checked: push each day, not everything on Sunday. Never backdate or manufacture empty commits.

Changes reach `main` through pull requests. Use one daily `assignment-2-day-N` branch with two commits; merge through a fast-forward or rebase method that preserves both commits where supported. Do not squash away the two commits. If repository policy requires merge commits, retain the two substantive commits and accept additional merge commits; fourteen is a work target, not a maximum. Day 1 adds CI before its PR merges; every later PR must pass CI before merging. Do not bypass a failed gate to keep the calendar.

## Intended Picky architecture

Keep Python/Flask and the Assignment 1 seam:

| Part | Owns | Boundary |
|---|---|---|
| `services/restaurants/` | `restaurants`, `saved_restaurants`, `restaurant_images`, `restaurant_emails` | Catalog, saved list, filters, saved details and location |
| `services/dining/` | `visits`, `bills`, `visit_items` | Visits, ordered items and bills; saved-entry ID becomes a plain external ID |
| `ui/` | Static HTML/CSS/JS | Browser calls both JSON APIs, using configured base URLs |

Exactly two custom service containers. Locally, a stock nginx image serves `ui/`, one SQL Server container contains two databases, and a one-off initialization container creates the databases/logins. These supporting containers are permitted by the brief. Azure uses two Consumption Container Apps, two serverless Azure SQL databases on one logical server, and one Static Web App.

Recommended server-side seam flow: recording a visit calls the restaurant service to validate the saved entry and update its visited status. Decide and test ordering, retry/idempotency and the response if only one write succeeds; a distributed transaction does not exist. Never silently claim success when the two writes disagree. All outbound calls, including geocoding, need explicit timeouts.

Removal is another seam to design: Assignment 1 cascades saved-entry deletion to dining data and bill files. Preserve that behavior through explicit HTTP coordination or document and justify a deliberate change in ADR-6/7, with tests. No cross-database joins or access.

Bill files need durable storage across container replacement. Prefer evaluating storage in the dining SQL database for this constrained assignment; confirm suitability and document the decision. Container-local files alone will not preserve uploaded bills on redeployment. Use synthetic demonstration data on the public deployment.

## Daily workload

Budget roughly **four focused hours per day**: two 100-minute implementation/check blocks, 20 minutes for records/evidence and 20 minutes explaining the work without notes. These are estimates, not a promise; SQL Server setup, the static UI conversion and Azure access are the main uncertainties. Prepare Docker/Rosetta, class Azure credentials, resource-group access, username prefix and the student-authored schema described below before completing milestone 1. Never put credentials in this guide.

| Date | Commit | Suggested message | Scope and completion check |
|---|---:|---|---|
| Mon 16 Nov | 1 | `chore: establish service contracts and CI baseline` | Add service folders and pinned manifests, initial OpenAPI files, student-authored system schema based on §8a (clearly labelled) and matching `system.yaml`. Map all existing UI operations to API endpoints. Add push/PR CI for lint, contract validation, tests/coverage and image builds, introducing the image gate with commit 2. Your task: write ADR-6. Check contracts and baseline tests. |
| Mon 16 Nov | 2 | `build: add isolated SQL databases and service containers` | Own Dockerfile per service, `.dockerignore`, SQL Server connection layer, `db/init.sql`, compose, volumes and initial versioned schemas/runners. Health checks and retry/backoff, non-root service users, explicit COPY and environment examples. Run from a clean checkout, boot twice, verify separate login permissions. Complete CI image/SQL test gates before PR merge. |
| Tue 17 Nov | 3 | `feat: port restaurant collection to its SQL API` | Port collection queries/validation from SQLite to SQL Server; expose catalog, saved entries, filters, details and location endpoints. Move idempotent seed data with its tables. Unit/SQL tests and ≥70% core coverage for this service; update OpenAPI. |
| Tue 17 Nov | 4 | `feat: port dining history and preserve existing data` | Port visits, ordered items and bill persistence to the dining database; own health and request logs. Add repeatable data transfer from an Assignment 1 database copy, preserving IDs and checking rows/relationships and bill contents. Your task: write ADR-7, including bad-migration recovery. Verify repeat runs do not duplicate data. |
| Wed 18 Nov | 5 | `feat: coordinate visits across service boundaries` | Implement HTTP saved-entry validation/status updates, deletion coordination and explicit timeouts. Test peer failure, timeout, invalid IDs, retries and partial-write handling. Add integration test across the seam; own-domain health remains independent. Your task: write ADR-9. |
| Wed 18 Nov | 6 | `feat: serve catalog and saved places through static UI` | Convert shared layout, saved list, add/save/remove, filters and restaurant details to static files and JSON calls. Generate/serve configurable API URLs locally; CORS only permits UI origin. Verify these flows through the browser with both APIs. |
| Thu 19 Nov | 7 | `feat: complete static dining and bill workflows` | Convert visits, items, bill upload/download, saved-details editing and location flows. Show clear peer-unavailable and loading states. Both domains work end to end; no Flask-rendered UI dependency. Update API/system descriptions. |
| Thu 19 Nov | 8 | `ci: enforce service quality and integration gates` | Finish the full SQL Server CI suite: lint and tests for each service, ≥70% per-service core coverage, seam integration, both image builds, system schema and both OpenAPI validations. Check a real failing run and its fix; you retain links and write the explanation. Verify compose restart preserves records and bills. |
| Fri 20 Nov | 9 | `infra: define constrained Azure hosting and deployment` | Add understandable IaC or repeatable CLI setup and CD using class GitHub secrets, GHCR SHA tags, two Container Apps (min 0/max 1), one SWA and two SQL databases with separate logins. SQL settings follow §7: GP Gen5, min 0.5/max 1 vCore, shortest allowed auto-pause, 2 GB, local backup redundancy. Use existing class resource group and own prefix only. Your task: write ADR-8. Validate configuration before deployment. |
| Fri 20 Nov | 10 | `deploy: publish baseline and verify live workflows` | Gate CD on CI for the same SHA, deploy on main only, inject API URLs/CORS and secrets, deploy static UI and poll health with a bounded cold-start allowance. Obtain a successful live deployment with **001 only**, create synthetic records; stop for you to save before-migration evidence. Check both domains and bill persistence after redeploy. Your task: write ADR-10. |
| Sat 21 Nov | 11 | `db: evolve populated Azure data without losing rows` | Only after commit 10's Azure baseline contains data: add an actual `002` migration (e.g. default/backfill on an existing table), tests and updated schemas. Merge/deploy through CD. You capture Azure before/after IDs and values, run URL and startup migration log. Restart: no migration reapplied and no data lost. Never edit an applied migration. |
| Sat 21 Nov | 12 | `test: verify service recovery and deployment behavior` | Resolve findings from clean-clone, stopped-peer, DB-unavailable, cold-start and restart checks. Check own `/health` read/write probe returns 200/503 correctly and logs include method/path/status/duration and version. You capture user-visible partial failure and a successful main CD run; AI reports checks and explains the system for your diagrams. |
| Sun 22 Nov | 13 | `docs: finish report and operational instructions` | You finalize the 4–5 page report, diagrams, selected evidence, AI disclosure and live URL. AI finishes technical README instructions: compose, one service, tests/coverage, initial Azure setup and deployment. Validate docs and system/OpenAPI files against final behavior. |
| Sun 22 Nov | 14 | `chore: verify submission and finalize process records` | AI checks technical acceptance and applies any final concrete fixes. You complete the AI log, ADRs and evidence. Confirm ADR-6–10, CI, live flows and daily push history. Merge PR, wait for successful deployment of final main SHA, then tag/push `submission` at that SHA. You submit repository URL, full matching SHA, live URL and report before 23:59; target 20:00. |

## Records spread through the week

**Your tasks:** write decisions when made, not retrospectively on Sunday. Keep ADR-1–5 text unchanged except superseded status if needed. Add **exactly** ADR-6–10 in the existing format: context, decision, alternatives and consequences. Planned dates: ADR-6 Monday; ADR-7 Tuesday; ADR-9 Wednesday; ADR-8 Friday; ADR-10 Friday. That spans four distinct commit dates.

You write `AI_USAGE.md` entries for applicable commits, including AI help on Dockerfiles, workflows and infrastructure, entirely in your own words. The AI only reminds you which work needs an entry. Commit this guide with Day 1's first implementation commit if useful; no commits have been made by preparing this plan.

You collect evidence as the work happens under `docs/assignment-2/evidence/`: dated run links, sanitized migration logs and queries, screenshots, and exact tested SHAs. Never store connection strings, tokens, real bills or private notes there. One fixed failed workflow and one successful main deployment are required; use a real failure/fix, not an invented history.

## What to explain without notes each day

| Day | Explain and trace on paper |
|---|---|
| 1 | Image versus container versus registry; each Dockerfile line; build context and layer cache; host ports versus compose DNS; readiness versus startup order. |
| 2 | Table ownership; SQL dialect changes; separate logins; why a cross-service foreign key disappears; migration ledger and safe data transfer. |
| 3 | One visit request across both services; timeouts and failure responses; why two HTTP writes are not one database transaction. |
| 4 | Browser fetch, API configuration and CORS; unit versus integration tests; why 70% applies to each service rather than combined coverage. |
| 5 | Push → CI → SHA image → main-only CD → Azure → health; Container Apps and SQL cold starts, backoff, scaling and cost settings; changes at 100× traffic. |
| 6 | Walk through 001 then 002 on existing rows; why 002 runs once; how to recover from a bad migration; own health versus peer availability. |
| 7 | Draw the deployed system from memory and justify every ADR, configuration value and intentionally omitted component. |

The written check multiplies the project subtotal: working software alone is insufficient. Blackboard lists the written check due **25 November at 23:59**; the brief says it is in class in the first session after the deadline. Verify the actual class/session timing rather than treating that due-time as the exam appointment.

## Final acceptance checklist

- [ ] Same repository and Python stack; two feature-domain services and two owned SQL databases; no direct peer database access.
- [ ] Existing Picky behaviors available through static `ui/`; browser calls both APIs over HTTPS; configurable URLs and restricted CORS.
- [ ] Dockerfiles, pinned dependencies, explicit COPY, non-root users, ignored secrets; clean-clone compose with documented local configuration.
- [ ] Idempotent database/login creation and seeding; automatic ordered migration ledger; existing Assignment 1 data preserved during split.
- [ ] Azure populated baseline precedes 002; before/after evidence, startup log, deployment run and no duplicate migration on restart.
- [ ] Designed server-side seam flow, bounded outbound calls, own-domain availability during peer failure and integration coverage.
- [ ] Independent database read/write health probes, version SHA, 503 on database failure, request logs to stdout.
- [ ] Push/PR CI: lint, SQL tests, ≥70% per service, image builds, system schema and OpenAPI validation; no Azure SQL in CI.
- [ ] Main-only CD after same-SHA CI; GHCR SHA-tagged images, SWA deployment, secret references and bounded post-deploy health checks.
- [ ] Azure contract limits/prefix/resource group honored; cold-start recovery; durable bills; live URL remains up until grades published.
- [ ] Exactly five new ADRs across ≥3 dates; AI log updated and personally understood; ≥12 new commits across ≥6 days, each pushed on its day.
- [ ] 4–5 page report with all diagrams/evidence and AI disclosure; reproducible README with live URL.
- [ ] Final deployed main SHA tagged `submission`; pushed tag, submitted full SHA and report all agree.

## If work slips

Do not remove tests, evidence or daily pushes to reach a cosmetic count. Keep two real increments per day when possible; additional fix commits are allowed. Finish the existing use case instead of adding features or changing frameworks. Front-load access/setup problems and keep a short blocker list in the daily PR. If the Azure baseline is late, prioritize it before writing/deploying 002; local migration evidence alone cannot satisfy §4.6. The 22 November deadline takes priority over the preferred fourteen-commit count.
