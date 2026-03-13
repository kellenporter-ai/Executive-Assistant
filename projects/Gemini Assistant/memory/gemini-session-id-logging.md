---
name: gemini-session-id-logging
description: GEMINI_SESSION_ID is passed to tools via environment variables for session-aware logging.
type: project
---

The backend now passes `GEMINI_SESSION_ID` to all CLI subprocesses.
**Why:** To support parallel session isolation and auditability.
**How to apply:** 
- `tools/system/log_action.py` records the `session_id` in `memory/operational_logs.jsonl`.
- `tools/system/get_logs.py` defaults to filtering by the current session's ID.
- The `sign-on` workflow and `GEMINI.md` core instructions are updated to be session-aware.
- If troubleshooting context bleeding, verify that `GEMINI_SESSION_ID` is being correctly propagated from the server/client to the tools.
