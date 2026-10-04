# AI usage log

The Prompt column contains edited paraphrases of my requests for clarity; these are not verbatim chat quotations. I supplied the restaurant idea, the seven-table schema, and the first versions of `add_restaurant`, `remove_restaurant`, `save_existing_restaurant`, `get_restaurant_details`, `add_visit`, and `add_bill`. Codex implemented the surrounding app and later additions. **I need to check and rewrite the last column in my own words before submission**, because it must reflect my actual understanding.

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-09-29 / `c243063` | OpenAI Codex | Read the assignment and set up the approved restaurant app and required document outlines, but build only a scaffold for now. | Modified | Codex created a one-process Flask starter and document outlines; the scope was kept small at my request. | `app.py` starts Flask. Startup creates the SQLite database under `DATA_DIR`. |

| 2026-09-29 / `c3861b2` | OpenAI Codex | Define the responsibilities and boundary between restaurant collection and dining history. | Modified | Codex wrote an initial boundary document, later updated for my seven-table schema. | Restaurant collection owns catalog and saved-list data. Dining history owns visits, items, and bills. |

| 2026-09-30 / `38eda01` | OpenAI Codex | Implement the seven-table SQLite schema I supplied, draw a matching diagram, and record that I designed the schema. | Modified | I designed the seven tables; Codex put them in SQLite, enabled foreign keys, and wrote matching diagrams. | `restaurants` holds general facts. `saved_restaurants` holds my personal record. Visits link to a saved entry; bills and items link to visits. |
| 2026-09-30 / `eeab93f` | OpenAI Codex | Connect my add_restaurant function to a simple form and show the saved restaurants on the page. | Modified | Codex added the add form, saved list, POST route, and validation feedback around my `add_restaurant` function. | The form sends fields to Flask, which calls `add_restaurant`; that function inserts a restaurant and its saved entry. |

| 2026-09-30 / `bf9a079` | OpenAI Codex | Write clear README instructions for installing dependencies, starting Flask, and opening the app. | Accepted | Codex added install, start, and browser instructions to the README. | `python app.py` serves the templates at `http://localhost:8000/`; opening an HTML template as a file does not run Flask. |


| 2026-09-30 / 2026-10-01 | OpenAI Codex | Reorganize the database, Python backend, and frontend into clearer folders;| Modified | Codex moved Python, SQL, and frontend files into clear folders and updated imports. | Root app.py starts Flask; backend handles requests, database holds SQLite setup, and frontend holds the pages. |


| 2026-09-30 / 2026-10-01 | OpenAI Codex | Connect my remove_restaurant function to a Remove button and show what happens after removal. | Modified | Codex added a Remove button and POST route, then adapted them when I changed removal to target the saved entry. | Removing deletes the personal saved row and its visits, but keeps the catalog restaurant. |

| 2026-09-30 / 2026-10-01 | OpenAI Codex | Add a page showing every restaurant in the database, whether it is saved or not. | Accepted | Codex added a page listing saved and unsaved restaurant rows. | A left join keeps unsaved restaurants visible even when there is no saved row. |

| 2026-09-30 / 2026-10-01 | OpenAI Codex | Connect my save_existing_restaurant function to the catalog and ask whether the place is wanted or already visited. | Modified | I wrote save_existing_restaurant; Codex added the status choice and POST route. | The route inserts one saved entry linked to the existing restaurant ID. |

| 2026-10-01 / `42124ad` | OpenAI Codex | Make each restaurant card open a detail page using my get_restaurant_details function. | Modified | Codex linked restaurant cards to a page that calls my `get_restaurant_details` function. | The function reads a restaurant plus any saved entry. If the ID is missing, the page returns 404. |

| 2026-10-01 / `0d4ef24` | OpenAI Codex | Connect my add_visit and add_bill functions to the detail page so I can record visits and upload bills. | Modified | I supplied `add_visit` and `add_bill`; Codex added forms, file checks, download routes, and visit queries. | A visit links to a saved restaurant. A bill row stores a path to its uploaded file, and the download route checks ownership. |


| 2026-10-02 / `0237641`–`27adad4` | OpenAI Codex | Let me enter a restaurant address, find its latitude and longitude, show it on a map | Accepted | Codex used address and coordinate columns already in my schema, added an optional lookup, cache, rate limit, UI, and tests. | Submitting an address can find latitude and longitude. The result is saved on the restaurant row; basic app use works without lookup. |


| 2026-10-03 / `769b531`–`6248c2d` | OpenAI Codex | Fix the Location not found problem and add a simple way to save a location when search fails. | Accepted | Codex stopped appending an unrelated city to full addresses and added manual coordinate entry. | Full addresses are searched as entered. Manual latitude and longitude are validated before saving. |


| 2026-10-04 | OpenAI Codex | Rename the app to Picky throughout the interface and report, then run it. | Modified | Codex changed the visible name, README, report source, PDF, and address-service User-Agent while retaining the existing SQLite filename so saved data stays available. | The new name appears in page titles and the report; startup still reads the same database under `DATA_DIR`. |

| 2026-10-04 | OpenAI Codex | Improve the app's main flow, fill the empty bill-file tests, and check whether it meets the assignment. | Modified | Codex added saving from the detail page, clearer catalog and empty-list content, bill-file tests, a path-safety fix, and updated the measured test result in the documents. | A newly saved restaurant gets a row in `saved_restaurants` and stays on its detail page; bill files use generated names under `DATA_DIR/bills`. |
