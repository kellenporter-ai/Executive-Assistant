---
name: ui-connection-timeouts
description: Prevent UI connection loss by avoiding long-running or high-output shell commands.
type: feedback
---

Avoid running shell commands that produce massive output (like unrestricted `grep` searches over large directories) or take a long time to execute.

**Why:** The local proxy server (`app/server.py`) or the subprocess communication between the UI and CLI can time out, causing a "Connection lost. Partial response preserved above" error in the user interface.
**How to apply:** When running searches or complex commands, redirect output, use specific files/paths instead of root, and try to keep command execution times and outputs brief.
