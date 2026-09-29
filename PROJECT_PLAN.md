# Assignment 1 project plan

This file tracks the work needed for `assignment_1.md`. It is a planning aid, not a substitute for the required deliverables.

## Proposed application scope

**Restaurant discovery and dining history:** a personal app for saving restaurants to visit or already visited, filtering the saved places, and recording what happened on each visit. The student confirmed professor approval on 2026-09-29.

The two backend feature domains would be:

1. **Restaurant collection:** create and update saved restaurants, mark them as visited or wanted, and filter by cuisine, location, price range, and rating. It owns restaurant facts and saved-list state.
2. **Dining history:** record a visit at a saved restaurant, including date, rating, private notes, ordered items, a bill upload, and whether the user would return. It owns visit facts and references a restaurant by its ID.

The restaurant collection can work without any visits. Dining history refers to a restaurant by ID; the Flask layer coordinates visit recording and rating summaries. The detailed ownership and interaction contract is in `DOMAIN_BOUNDARIES.md`. Both domains must save and read their own records through SQLite.

## Decisions needed before implementation

- [x] Get the specific app idea and its two backend feature domains approved by the professor (§2).
- [x] Choose a backend stack the student can explain unaided (§1d, §6): Python and Flask.
- [x] Define the two domains' ownership and interaction boundary in `DOMAIN_BOUNDARIES.md`.
- [ ] Decide whether the app needs login before exposing private notes and bills beyond local use.
- [x] Choose the initial SQLite path and data model; recheck against implemented features later.

## Required repository contents

- [ ] Working monolithic app with two distinct backend domains, each using SQLite.
- [x] One dependency manifest at the repository root.
- [ ] Automated unit tests of both domains' business logic; measure at least 70% coverage.
- [ ] `README.md`: install, run, configuration, SQLite path, test/coverage command and measured result.
- [ ] `ADR.md`: exactly five decided entries in the prescribed format, written as decisions are made.
- [ ] `AI_USAGE.md`: one accurate row per meaningful AI interaction, reviewed and explained in the student's own words.
- [ ] Four to five page report with SMART goals, SDLC reflection, matching architecture and database diagrams, and the syllabus AI disclosure statement.
- [ ] At least 12 meaningful commits across at least six actual calendar days, with no one day exceeding 40% of commits; push promptly so remote timestamps corroborate the sequence.
- [ ] Attend the closed-book written comprehension check.

## Deployment contract to verify

- [x] One documented command starts one process bound to `0.0.0.0`.
- [x] Port and all configuration come from environment variables; a default port works.
- [x] Fresh clone, dependency installation, and start need no interactive step.
- [x] SQLite is created at one documented path, under `DATA_DIR`.
- [ ] Startup takes only a few seconds and requires no external managed service.
- [ ] No authored Dockerfile, Compose file, CI workflow, or infrastructure as code.

## Schedule

The deadline is **2026-10-04 23:59**. The repository currently has an initial commit dated 2026-09-29. To meet the six-day rule with genuine work, continue making and pushing meaningful changes on each calendar day through 2026-10-04. Never backdate or split changes into empty commits to manufacture a history.
