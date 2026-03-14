---
name: gemini-cli-session-deletion
description: Gemini CLI session deletion requires index-based targeting and reverse-order processing for batches.
type: project
---

To fully remove a session from the Gemini CLI's active list, moving the JSON file is insufficient; you must also use the CLI's deletion command.

**Why:** The Gemini CLI maintains an internal state of active sessions. Even if a session's JSON file is moved to an archive directory, `gemini --list-sessions` may still report it until it is explicitly deleted via `gemini --delete-session <index>`.

**How to apply:**
1. **Index Targeting:** When listing sessions with `gemini --list-sessions`, parse and store the numerical index (e.g., "1.", "2.") provided in the output. Use this index for deletion calls.
2. **Reverse Batch Deletion:** When deleting multiple sessions in a single operation, always sort the sessions by their indices in **descending order** (highest to lowest) before executing the deletion calls. This prevents the deletion of one session from shifting the indices of subsequent sessions in the batch.
3. **Redundancy:** Combine CLI deletion with file moving/archiving to ensure both the CLI state is clean and the session data is preserved in the project's archive if needed.