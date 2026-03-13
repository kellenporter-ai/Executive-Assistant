---
name: parallel-session-isolation
description: User prefers multiple parallel chat sessions without context bleeding.
type: user
---

The user expects the Assistant to handle independent tasks in parallel across different chat windows/tabs.
**Why:** Previous behavior caused context from one chat to "bleed" into others, disrupting distinct workflows.
**How to apply:** Always distinguish between the global project state (priorities, state databases) and the session-specific activity (logs filtered by `GEMINI_SESSION_ID`). Treat each new session as a fresh context unless specifically asked to reference global history or other sessions.
