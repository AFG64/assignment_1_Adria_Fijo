# Static collection UI — milestone 6

The same green/neutral Picky layout now runs as plain HTML, CSS and JavaScript in
ui/, served by stock nginx locally. No page rendering from the Flask monolith is
needed. The original Assignment 1 templates/static assets remain untouched.

Implemented routes are #/saved, #/catalog (five filters in the URL), and
#/restaurants/<id>. Hash routing supports refresh and Back/Forward on static
hosting. Catalog/saved lists, new restaurant creation, saving an existing catalog
entry with status, confirmed removal and read-only restaurant details work with
the restaurant API. Details fetch read-only visit history from dining; history
failure does not hide restaurant facts. Visit/item/bill entry, downloads, personal
saved-detail editing and location editing are milestone 7, not claimed complete.

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
