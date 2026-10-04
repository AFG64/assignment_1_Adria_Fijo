# Assignment 1 project plan

This file tracks the work needed for `assignment_1.md`. It is a planning aid, not a substitute for the required deliverables.

## Proposed application scope

**Restaurant discovery and dining history:** a personal app for saving restaurants to visit or already visited, filtering the saved places, and recording what happened on each visit. The student confirmed professor approval on 2026-09-29.

The two backend feature domains would be:

1. **Restaurant collection:** create and update restaurant details and the single user's saved entry, mark it as visited or wanted, and filter by category, location, price, or personal rating. It owns `restaurants`, `saved_restaurants`, `restaurant_images`, and `restaurant_emails`.
2. **Dining history:** record visits at a saved restaurant, including date, rating, notes, amount spent, party size, ordered items, and bill records. It owns `visits`, `bills`, and `visit_items`.

The restaurant collection can work without any visits. Dining history refers to a saved restaurant by ID; the Flask layer coordinates visit recording and status updates. The detailed ownership and interaction contract is in `DOMAIN_BOUNDARIES.md`. Both domains must save and read their own records through SQLite.

The student added `add_restaurant`, `remove_restaurant`, and `save_existing_restaurant` on 2026-09-30. The home page adds restaurants and removes saved entries. A separate All restaurants page reads every catalog row, including unsaved ones, and can save an existing row as Want to go or Visited. Filtering was added on 2026-10-04; other editing remains pending.

On 2026-10-01, the student added `get_restaurant_details`. Both restaurant lists now link to a detail page backed by that function. The page displays general facts, saved details, and visit history.

The add form now opens from the + control beside the app title. A validation error keeps it open with the entered values; the saved-list page remains visible when the form is closed.

The student added `add_visit` and `add_bill` in `backend/dining_history.py` on 2026-10-01. The restaurant detail page now records and lists visits, accepts bill uploads for each visit, and provides downloads. The UI validates dates, ratings, and uploaded files; ordered items, spend, and party size remain planned.

On 2026-10-02, Codex added optional location entry and coordinate lookup to the restaurant add form, plus a location editor on the detail page. Address, latitude, and longitude already existed in the student-supplied `restaurants` table, so no schema change was needed. The lookup service caches results under `DATA_DIR` and is used only when the user submits a location.

On 2026-10-03, the location flow was corrected so a complete address is not combined with an unrelated saved city. The detail page also gained manual coordinate entry for locations the search cannot find or matches incorrectly. No schema change was needed.

On 2026-10-04, the All restaurants page gained combinable cuisine, city, price, minimum personal rating, and saved-status filters. Filtering reads the restaurant collection tables and keeps the two backend domain boundary unchanged.

## Decisions needed before implementation

- [x] Get the specific app idea and its two backend feature domains approved by the professor (§2).
- [x] Choose a backend stack the student can explain unaided (§1d, §6): Python and Flask.
- [x] Define the two domains' ownership and interaction boundary in `DOMAIN_BOUNDARIES.md`.
- [ ] Decide whether the app needs login before exposing private notes and bills beyond local use.
- [x] Implement the student-supplied seven-table SQLite schema at the documented path; recheck against implemented features later.

## Required repository contents

- [ ] Working monolithic app with two distinct backend domains, each using SQLite.
- [x] One dependency manifest at the repository root.
- [x] Automated unit tests of both domains' business logic; 97% combined domain coverage measured on 2026-10-03.
- [x] `README.md`: install, run, configuration, SQLite path, test/coverage command and measured result.
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
