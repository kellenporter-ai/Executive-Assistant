---
name: daily-briefing
description: >
  Summarize recent activity — what was done, what changed, what's next.
  Use when Kellen says "briefing", "daily briefing", "what happened",
  "catch me up", "what's the status", "what did we do", or any variation
  of wanting a session/day summary.
model: claude-sonnet-4-6
effort: medium
tools: [Read, Bash, Glob, Grep]
---

# Daily Briefing

Generate a concise summary of recent activity across the EA workspace. This is a read-only operation — gather info and present it clearly.

## Inputs
- **Time range** (optional): defaults to "since yesterday". Kellen may say "this week", "last 3 days", etc.
- **Save to file** (optional): if requested, save to `assets/Briefings/YYYY-MM-DD.md`

## Steps

### 1. Load Current Priorities

Read `context/current_priorities.md` to understand what Kellen is focused on. Extract the top 3 active priorities.

### 2. Gather Git Activity

```bash
cd "/home/kp/Desktop/Executive Assistant"
echo "=== EA Repo ==="
git log --oneline --since="yesterday"

echo ""
echo "=== Porters-Portal ==="
cd projects/Porters-Portal 2>/dev/null && git log --oneline --since="yesterday" || echo "(no activity or not available)"
```

Adjust `--since` based on the requested time range.

### 3. Check Decision Log

```bash
ls -lt "/home/kp/Desktop/Executive Assistant/decisions/" | head -10
```

Read any entries created within the time range. Note new decisions.

### 4. Check Memory Updates

Scan `~/.claude/projects/-home-kp-Desktop-Executive-Assistant/memory/MEMORY.md` for recently added content (look at the file — recent additions tend to be near the bottom or have recent dates).

### 5. Scan for Open Threads

```bash
# Check for TODO/FIXME in recently modified files
cd "/home/kp/Desktop/Executive Assistant"
git diff --name-only HEAD~5 2>/dev/null | head -20

cd projects/Porters-Portal 2>/dev/null
git diff --name-only HEAD~5 2>/dev/null | head -20
```

If recently modified files exist, scan them for TODO/FIXME/HACK markers.

### 6. Compile and Present

Format the briefing as:

```
## Daily Briefing — YYYY-MM-DD

### Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

### Completed
- [Commit/change summary — grouped by repo]

### Decisions Made
- [Any new decision log entries, or "None"]

### Open Threads
- [TODOs, in-progress items, unfinished work]

### Attention Needed
- [Blockers, stale priorities, anything flagged]
```

If nothing happened in a section, say "None" — don't pad or fabricate.

### 7. Save (if requested)

If Kellen asked to save:

```bash
mkdir -p "/home/kp/Desktop/Executive Assistant/assets/Briefings"
```

Write the briefing to `assets/Briefings/YYYY-MM-DD.md`.

## Output
- Terminal output (default): formatted briefing printed to the conversation
- File output (optional): `assets/Briefings/YYYY-MM-DD.md`

## Error Handling
- On git log failure: skip that repo's section, note "(git log unavailable)"
- On empty activity: report "No activity in the requested time range" — don't fabricate
- On missing submodule: skip it, note it's not available
- Escalation: none needed — this is a read-only, informational skill
