# Restaurant and dining-history feature boundaries

**Status:** design for the next iterations. The current repository contains the SQLite schema, but these operations have not been implemented. This document makes the two backend responsibilities explicit before adding routes or business logic.

## Restaurant collection

**Purpose:** keep a personal collection of restaurants to try or revisit. A restaurant can be saved without any visit.

**Owns:** the `restaurants` table and its `id`, `name`, `cuisine`, `city`, `price_level`, `saved_status`, and `created_at` fields. In the initial model, `city` is the location used for filtering, `price_level` is an integer from 1 to 4, and `saved_status` is `want` or `visited`.

**Planned operations:**

- Save a restaurant with a name, cuisine, city, price level, and status.
- Update those restaurant facts and status.
- Get one restaurant by ID; list saved restaurants and filter by cuisine, city, price level, or status.
- Combine a visit rating summary with restaurant results when a rating filter is requested.

**Rules to test:** required text fields cannot be blank; price level must be 1–4; status must be one of the two allowed values. A rating filter means the average of all recorded visit ratings for a restaurant, with a requested minimum from 1 to 5. Restaurants with no visits appear in an unfiltered list but cannot match a minimum rating.

The collection does **not** own visit dates, orders, notes, bills, or per-visit ratings. It must not write to `visits` or `ordered_items`.

## Dining history

**Purpose:** preserve what happened on each visit to a saved restaurant. One restaurant can have many visits, and one visit can list many ordered items.

**Owns:** the `visits` and `ordered_items` tables. A visit stores `restaurant_id`, date, 1–5 rating, notes, whether the user would return, and optional bill metadata and bytes. Each order stores a name, positive quantity, and nonnegative unit price in cents.

**Planned operations:**

- Record a visit for an existing restaurant, including zero or more ordered items and an optional bill.
- List visits for a restaurant and get a visit's details.
- Return the average rating for each restaurant as a read-only summary used by the collection view.
- Download the bill attached to a visit, when one exists.

**Rules to test:** a visit must reference a saved restaurant; date and rating must be valid; `would_return` must be a yes/no value. Each order requires a name, positive quantity, and nonnegative price. Before bill uploads are enabled, choose and enforce a size limit and permitted file types; the current schema alone does not validate file content.

Dining history does **not** edit restaurant names, cuisine, city, or price level. It refers to a restaurant by its stable ID rather than copying those fields into each visit.

## Interaction between the domains

The Flask layer will coordinate the two domains in the same process. When recording a visit, it will check that the restaurant exists, save the visit and its ordered items in SQLite, and mark the restaurant `visited` through the restaurant collection's operation. These changes should use one transaction so a failed visit does not leave a misleading status. Rating-based filtering will ask dining history for rating summaries and pass them to the collection's filter; it will not let the collection write visit rows.

The seam for Assignment 2 is the restaurant ID and two narrow interactions: **restaurant existence/status** for a new visit, and **rating summaries** for filtering. The planned modules are `restaurant_domain.py` and `visit_domain.py`, both called by `app.py`; they remain inside one process and use the same SQLite file in Assignment 1. If the later assignment separates them, these two interactions are the ones that need an API or replicated read model.

## Scope still to decide

Authentication and access to private notes and bill images need an explicit decision before the app is used by anyone beyond its local owner. The current scaffold has no login. Deleting restaurants or visits and editing past visits are not part of the initial feature contract; add them only if there is time to define their data and referential-integrity rules.
