# Static UI — collection and dining workflows

The same green/neutral Picky layout now runs as plain HTML, CSS and JavaScript in
ui/, served by stock nginx locally. No page rendering from the Flask monolith is
needed. The original Assignment 1 templates/static assets remain untouched.

Implemented routes are #/saved, #/catalog (five filters in the URL), and
#/restaurants/<id>. Hash routing supports refresh and Back/Forward on static
hosting. Catalog/saved lists, new restaurant creation, saving an existing catalog
entry with status, confirmed removal, restaurant details, personal rating/notes/
return-preference editing and location editing work with the restaurant API.
Details load dining history and support visit entry, ordered items and PNG/JPEG/
PDF bill upload/download. History failure does not hide restaurant facts.
Each visit submission crosses the server-side seam and marks the place visited.
Dates use the Europe/Madrid calendar in both browser and API, including the
midnight boundary when Azure hosts still use UTC.

## Public configuration

ui/config.js contains public API base URLs only. Generate it before serving or
uploading the site:

```sh
python scripts/configure_ui.py --restaurants-url http://localhost:8001 --dining-url http://localhost:8002
```

Committed generated defaults make the documented clean-checkout compose flow
work locally. Deployment will regenerate the same file with actual HTTPS service
addresses and upload ui/ to the Storage static website. Never put database URLs,
passwords or tokens here. The generator rejects credentials, query/fragment
values, unsupported schemes and invalid ports. HTTPS pages require HTTPS API URLs.
App code reads config instead of embedding service addresses. No npm runtime,
bundler, custom frontend image or proxy is required.

Use http://localhost:8080 with compose's current UI_ORIGIN; using a different
browser origin requires matching service CORS configuration. Origin and
Content-Type preflight remain handled in the existing service application code.

## States and recovery

Lists/details show loading, empty, not-found/request failure and reload controls.
Mutation buttons disable in flight and requests are never retried automatically.
Unknown POST outcomes tell the user to check the saved list before retrying.
Inputs are retained after errors. Read generations prevent stale responses from
replacing a newer route. Untrusted text is escaped or assigned with textContent;
website links accept only HTTP(S), not executable URL schemes.

Removal requires confirmation that visits/items/bills will be deleted and the
catalog row retained. If DELETE cannot be confirmed, a persistent pending-cleanup
panel retains the original saved ID/title in browser localStorage. A confirmed
204 clears the entry; repeated DELETE is safe even after the saved row is gone.
The queue survives reload/browser restart when storage is available. If storage
is blocked, it works in page memory only; do not close the page before cleanup.
No pending cleanup is retried without user action. This does not add server-side
authentication or protect personal data from other users of the same browser.

## Checks

Python tests check public config URL validation; CI also checks JS syntax with
Node 22. Backend contracts and coverage gates remain enforced. Browser checks
were performed locally against the two real API containers, not mocked endpoints:
create a synthetic restaurant, literal HTML-like title display, all five filters,
empty result, reload/Back preservation, read-only details/history, save existing
as visited, confirmed/cancelled removal, dining-down history degradation and
pending cleanup recovery after restart/reload. Restaurant-down page recovery
was checked with the original nginx UI still running.

320px layout had no horizontal overflow and was visually inspected; desktop and
200% CSS zoom checks supplement it. Keyboard skip-link, focus movement and Escape
are checked locally. This is not a screen-reader or cross-browser certification.
Browser QA artifacts stay outside user-owned assignment evidence and are not
committed. Screenshots/logs for the report remain the user's task.

## Dining and edit forms (milestone 7)

Native details/form controls keep related actions next to their records. Every
field has a unique associated label; number/date/file constraints provide local
feedback, with the API retaining final validation. Empty personal values clear
to null, including the tri-state return preference. Inputs remain after request
errors; the form fieldset disables during a submission. Cancel/Escape closes the
composer and returns focus to its summary. Successful saves reload the current
restaurant only if the route generation still matches; a late response does not
replace another route.

Visits, items and bill uploads are non-idempotent: no automatic retries. Uncertain
network/server failures explicitly ask the user to refresh history and inspect
current visits/items/bills before resubmitting. A Refresh visit history button
provides that read-only recovery. File uploads use browser-generated multipart
boundaries, with no JSON Content-Type override, at most 5 MiB. The API checks
file signatures; a rejected file can be replaced without losing the form. Bill
downloads fetch scoped attachments as blobs, handle API failures in place, use
the returned MIME type for the download extension and revoke temporary URLs.

Location editing supports OpenStreetMap address lookup and explicit manual
coordinates. Lookup failure preserves the address and explains the manual
option. Coordinates are required only in manual mode. Existing coordinates link
to OpenStreetMap without embedding a map or loading tiles on every detail view.
The external lookup disclosure remains beside the form.

Milestone 7 browser verification (20 November): real local APIs/SQL, personal
false/null values and clearing, manual location and OpenStreetMap link, failed
address lookup with retained input/manual recovery, cross-service visit creation
and status, current Madrid date at the UTC boundary, ordered item/zero-quantity
validation, invalid-signature replacement, client rejection over 5 MiB, real PDF
upload and byte-exact browser download. Dining-down submission/download and
restaurant-peer-down submission show recoverable errors without losing input or
creating a visit after failed validation. 320px form layout and 200% CSS zoom
checked for overflow; mobile/desktop QA screenshots inspected. Escape restores
summary focus. This is Chromium verification, not native browser zoom, screen
reader or cross-browser certification. All unique local test rows are cleaned
after verification; test screenshots are not the user's assignment evidence.
