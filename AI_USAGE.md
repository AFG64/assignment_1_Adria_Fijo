# AI usage log

This is a working log. The student should review each row against the actual changes and rewrite the last column in their own words before submission. Add a row for every later meaningful AI interaction; disclosure itself is grade-neutral.

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-09-29 | OpenAI Codex | “read the assingment md and htne set up the repo so it fills all the required documents fo the assingment”; later: “just build the scaffold dont one shot the whole app” | Modified | Scope was narrowed from a complete application and documents to a Flask/SQLite scaffold plus working document outlines. | **Student to complete after reading `app.py` and `storage.py`:** explain how `create_app`, `database_path`, and `initialize_database` cooperate, including where the SQLite file is created. |
| 2026-09-29 | OpenAI Codex | “Define restaurant and visit feature boundaries” | Modified | Expanded the initial two-domain description into explicit table ownership, rules, and two cross-domain interactions. | **Student to complete after reviewing `DOMAIN_BOUNDARIES.md`:** explain why a visit stores `restaurant_id`, how a recorded visit changes `saved_status`, and where rating summaries are used. |
