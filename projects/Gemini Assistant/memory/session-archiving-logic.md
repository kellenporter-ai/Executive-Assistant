---
name: session-archiving-logic
description: Use state_db.py to archive sessions and hide them from active logs.
type: project
---

Sessions should be archived using the local state database when completed, not just by pruning logs.

**Why:** The user noted that archived sessions were still appearing in the active chat history summary. We implemented a `sessions` table in `state_db.py` to track archived status and filter them out in `get_logs.py`.
**How to apply:** During the `sign-off` workflow, present the option to archive the session. If confirmed, use `python3 tools/system/state_db.py archive-session --id [GEMINI_SESSION_ID]`. To view archived sessions, run `get_logs.py` with the `--all` flag.
