---
name: gemini-session-file-naming
description: Gemini CLI session files use an 8-character short ID in their filenames.
type: project
---

When interacting with Gemini CLI session files stored in `~/.gemini/tmp/<project>/chats/`, note that the JSON filenames use only the first 8 characters of the session UUID (the "short ID").

**Why:** We discovered a bug where UI archiving failed because the backend tried to match the file using the full `session_id` UUID, which yielded no matches since the files use the short ID format.
**How to apply:** Whenever searching for or matching a session file by its ID programmatically (using `glob` or similar tools), always extract the short ID using `session_id.split('-')[0]` and use it in the glob pattern (e.g., `f"session-*{short_id}*.json"`).