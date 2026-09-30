# Restaurant and dining-history feature boundaries

**Status:** the student-supplied schema is implemented, and restaurant creation and listing now work through `restaurant_domain.py` and the Flask home page. The remaining collection operations and dining-history behavior are planned. See `SCHEMA.md` for the full database diagram.

## Restaurant collection

**Purpose:** hold general restaurant facts and the single user's saved list. A restaurant can exist without a saved entry, and a saved entry can exist without any visits.

**Owns:** `restaurants`, `saved_restaurants`, `restaurant_images`, and `restaurant_emails`. `restaurants` holds title, category, description, location, contact details, general score and review count, price, menu, and a main image URL. `saved_restaurants` holds `want_to_go` or `visited`, the user's overall rating, personal notes, and whether they would go back. One restaurant can have at most one saved entry because `saved_restaurants.restaurant_id` is unique.

**Implemented operations:** `add_restaurant` creates a restaurant and its saved entry; `list_restaurants` returns saved restaurants for the home page. **Planned:** edit restaurant facts or saved details and filter by category, location, price, or personal rating. The planned personal-rating filter uses `saved_restaurants.rating`, rather than the general `restaurants.total_score` or any individual `visits.rating`.

**Rules to test later:** title is required; supplied scores and personal ratings are 0–5; price is 1–4 when present; saved status is `want_to_go` or `visited`; return preference is yes/no when present. Optional fields can remain empty, as allowed by the supplied schema.

The collection does **not** create visits, bill records, or ordered items.

## Dining history

**Purpose:** hold dated experiences at restaurants already in the user's saved list. A saved restaurant can have many visits.

**Owns:** `visits`, `bills`, and `visit_items`. Each visit points to `saved_restaurants.id` and can record date, its own 0–5 rating, notes, total amount, number of people, and whether the user would go back. A bill row holds an image path and optional extracted fields; an item row holds a dish name, quantity, unit price, optional rating, and notes.

**Planned operations:** record and list visits for a saved restaurant, record ordered items, attach one or more bill records, and retrieve bill paths for later download. Receipt extraction is not implemented; `extracted_total` and `extracted_text` are optional schema fields only.

**Rules to test later:** the saved restaurant must exist; number of people and item quantity are positive when present; amounts and prices are nonnegative; ratings are 0–5; return preference is yes/no. Upload implementation must validate file type and size, then store bill files under `DATA_DIR` and store their paths in SQLite.

Dining history does **not** change restaurant title, category, contact details, or the personal overall rating in `saved_restaurants`.

## Interaction and later split

The Flask layer will coordinate both modules in one process. When recording a visit, it will resolve the saved restaurant by ID, save the visit and its items, and mark the saved entry `visited` through the restaurant collection operation. These database changes should occur in one transaction. The later service seam is `saved_restaurants.id` plus a narrow saved-entry existence/status operation; personal-rating filtering stays inside the restaurant collection and no longer needs a visit-rating summary.

Deleting a restaurant cascades to its saved entry and then visits, bills, and items. Deleting a saved entry cascades to its visits. The future UI should make this effect clear before it offers deletion. Authentication remains undecided; the current scaffold is single-user and has no login, so personal notes and bills should not be treated as access-controlled yet.
