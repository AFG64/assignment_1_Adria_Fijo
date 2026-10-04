# Restaurant and dining-history feature boundaries

**Status:** the student-supplied schema is implemented. The home page handles saved places, the All restaurants page lists and filters catalog rows, and the detail page edits personal saved details and records visits, ordered items, and bills. The location forms fill existing address and coordinate columns. See `SCHEMA.md` for the full database diagram.

## Restaurant collection

**Purpose:** hold general restaurant facts and the single user's saved list. A restaurant can exist without a saved entry, and a saved entry can exist without any visits.

**Owns:** `restaurants`, `saved_restaurants`, `restaurant_images`, and `restaurant_emails`. `restaurants` holds title, category, description, location, contact details, general score and review count, price, menu, and a main image URL. `saved_restaurants` holds `want_to_go` or `visited`, the user's overall rating, personal notes, and whether they would go back. One restaurant can have at most one saved entry because `saved_restaurants.restaurant_id` is unique.

**Implemented operations:** `add_restaurant` creates a restaurant and its saved entry; the student-written `save_existing_restaurant` adds an existing catalog row to the saved list as `want_to_go` or `visited`; `list_saved_restaurants` returns saved places for the home page; `list_all_restaurants` reads every `restaurants` row using a left join and optionally filters by cuisine, city, price, minimum personal rating, or saved status; the student-written `get_restaurant_details` returns one catalog row and any saved details for its page; `remove_restaurant` deletes a saved entry by its own ID. `update_restaurant_location` changes an existing catalog row's address and coordinates. Flask calls the cached address lookup on location-form submission and passes the result to the restaurant domain. The update_saved_details function changes rating, notes, and return preference on a saved entry. The personal-rating filter reads `saved_restaurants.rating`, not `restaurants.total_score` or `visits.rating`. **Planned:** edit other general restaurant facts.

**Location rules:** an address is optional at creation and limited to 300 characters. A full address with commas is searched as entered; a saved city is added only to shorter addresses. The detail page also accepts manual coordinates when search fails or returns the wrong place. Both coordinates must be finite and in valid geographic ranges. Lookup failure or invalid manual input leaves existing data unchanged. Title is required; supplied scores and personal ratings are 0–5; price is 1–4 when present; saved status is `want_to_go` or `visited`; return preference is yes/no when present. Other optional fields can remain empty, as allowed by the supplied schema.

The collection does **not** create visits, bill records, or ordered items.

## Dining history

**Purpose:** hold dated experiences at restaurants already in the user's saved list. A saved restaurant can have many visits.

**Owns:** `visits`, `bills`, and `visit_items`. Each visit points to `saved_restaurants.id` and can record date, its own 0–5 rating, notes, total amount, number of people, and whether the user would go back. A bill row holds an image path and optional extracted fields; an item row holds a dish name, quantity, unit price, optional rating, and notes.

**Implemented operations:** the student wrote `add_visit` to record a dated visit; the saved-status update happens in the same transaction. The student wrote `add_bill` to attach a stored file path to a visit. `add_visit_item` records a dish or drink with quantity and optional unit price. Supporting queries list visits, items, and bills and check ownership for uploads and downloads. The UI stores PNG, JPEG, and PDF files up to 5 MB under `DATA_DIR/bills/`. **Planned:** record spend, party size, and return preference; extract receipt data. `extracted_total` and `extracted_text` are optional schema fields only.

**Current rules:** the saved restaurant must exist; the visit date must be valid and no later than today; visit rating is 0–5 when present; item quantity is a positive whole number and unit price is nonnegative when present; uploaded bills must have a PNG, JPEG, or PDF signature and be at most 5 MB. **Rules for planned fields:** number of people would be positive, total amount nonnegative, and return preference yes/no.

Dining history does **not** change restaurant title, category, contact details, or the personal overall rating in `saved_restaurants`.

## Interaction and later split

The Flask layer coordinates both modules in one process. When recording a visit, it resolves the saved restaurant by ID; `add_visit` saves the visit and marks the saved entry `visited` in one transaction. Items are linked to a visit and read with its history. The later service seam is `saved_restaurants.id` plus a narrow saved-entry existence/status operation; personal-rating filtering stays inside the restaurant collection and does not need a visit-rating summary.

Removing a saved entry leaves the `restaurants` row available on All restaurants. Its visits, bill records, and items cascade away. The UI asks for confirmation, then removes managed bill files associated with that saved entry after the database deletion. Deleting a `restaurants` row would cascade farther, but the current UI does not offer that action. Authentication is deliberately omitted in this local single-user version, so personal notes and bills are not access-controlled.

The All restaurants page offers the save choice only for catalog rows without a saved entry. The database's unique `saved_restaurants.restaurant_id` constraint prevents a second saved entry for the same restaurant; the route reports that conflict if a stale page submits one.
