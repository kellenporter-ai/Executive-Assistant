---
name: context-sync
description: >
  Weekly context maintenance — checks what is DIFFERENT now (reality shifts, priority drift,
  changed circumstances). Use this skill whenever the user says "sync my context",
  "review my priorities", "what's changed recently", "update my priorities", "context audit",
  "weekly review", "has anything shifted", "check for priority drift", or "maintenance check".
  NOT for session summaries or task history (use /daily-briefing for "what did we do").
  Also trigger proactively: if you notice it has been 7+ days since the last context sync
  (check the most recent decision log entry tagged CONTEXT-SYNC), nudge the user with
  "It's been over a week since your last context sync — want me to run one?"
model: claude-sonnet-4-6
effort: medium
tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Context Sync

You are performing a weekly maintenance sweep of the Executive Assistant's context files. Your job is to detect what has actually changed in Kellen's work and priorities based on concrete evidence, then update the context files to reflect reality.

This matters because stale context causes bad recommendations. If priorities shifted two weeks ago but the files still reflect old goals, every future conversation starts from a wrong baseline.

## What to Scan

Gather evidence from these sources before making any changes. Read broadly first, decide second.

### 1. Git History (both repos)
```bash
# EA repo — what's been worked on recently
cd "/home/kp/Desktop/Executive Assistant"
git log --oneline --since="2 weeks ago"

# Porter's Portal — what shipped or changed
cd "/home/kp/Desktop/Executive Assistant/projects/Porters-Portal"
git log --oneline --since="2 weeks ago"
```

### 2. Context Files
Read all files in `context/` to understand the current documented state:
- `context/me.md` — identity, courses, philosophy
- `context/work.md` — school, district, union context
- `context/team.md` — collaborators and their roles
- `context/current_priorities.md` — active goals and initiatives
- `context/rules.md` — communication and operating preferences

### 3. Agent Memory
Scan `agents/memory/*/MEMORY.md` for patterns agents have recorded. These often capture real shifts before anyone formally documents them — new bugs becoming a theme, a feature area getting heavy attention, performance issues surfacing.

### 3b. Gemini Memory Bridge
Check `projects/Gemini Assistant/memory/MEMORY.md` for learnings the Gemini system has accumulated. Propagate context-agnostic entries (not Kellen-specific) to `projects/Gemini Assistant (Shared)/memory/MEMORY.md` so the distributable version improves alongside the working version. Skip entries that reference personal data, school-specific details, or student information.

### 4. Decision Log
Read any existing files in `decisions/` to understand what's already been logged and avoid duplicating entries.

### 5. Recent Conversation Patterns (if available)
If the current conversation has prior messages, scan them for signals: new projects mentioned, shifting focus areas, new team members, tools adopted, frustrations expressed.

### 6. Stale Reference Files
Check modification dates of key reference files against recent project changes. If a reference file hasn't been updated in 30+ days but the code it documents has changed significantly, flag it as potentially stale.

```bash
# Check reference file ages vs recent code changes
for f in references/block-types.md references/economy-reference.md references/portal-bridge.md references/reveal-patterns.md; do
  if [ -f "$f" ]; then
    echo "$f: $(stat -c '%y' "$f" | cut -d' ' -f1)"
  fi
done
echo "---"
echo "Last Portal commit: $(cd projects/Porters-Portal && git log -1 --format='%ci' | cut -d' ' -f1)"
```

If any reference file is 30+ days older than the latest relevant code changes, add it to the sync report under a "Potentially Stale References" section.

## How to Detect Drift

Compare what the context files say against what the evidence shows. Look for these specific signals:

| Signal | Example | Likely Update |
|--------|---------|---------------|
| New project or initiative | Git commits to a new directory, repeated mentions | Add to current_priorities.md |
| Abandoned or completed goal | No activity in 2+ weeks on a listed priority | Mark complete or remove |
| Shifted focus | 80% of recent work in one area that's listed as secondary | Reorder priorities |
| New team member or role change | New name in commits, mentioned in conversations | Update team.md |
| New course or school change | Mentioned in conversation or context | Update me.md or work.md |
| Tool/workflow change | New skill created, agent added, process changed | Update current_priorities.md |
| Communication preference change | User corrected tone, asked for different format | Update rules.md |

The bar for "drift" is: would a fresh conversation starting from the current context files give meaningfully wrong assumptions about what Kellen is working on or cares about?

## How to Apply Updates

Once you've identified drift, apply updates directly — don't ask for permission. Use the Edit tool for surgical changes to existing files. Only use Write for new files (like decision log entries).

### Context File Updates
- Edit the specific lines that are outdated — don't rewrite entire files
- Preserve the existing structure and formatting of each file
- If adding a new section, match the style of existing sections
- If removing something, remove it cleanly (no "REMOVED" comments)

### Decision Log (Major Shifts Only)

Only log a decision when a priority is added, removed, or significantly reordered — not for minor wording tweaks. Create a new file in `decisions/` with this format:

**Filename:** `decisions/YYYY-MM-DD-brief-slug.md`

```markdown
# [Brief title of the shift]

**Date:** YYYY-MM-DD
**Type:** CONTEXT-SYNC
**Source:** [What evidence triggered this — git history, conversation, agent memory]

## What Changed
[1-2 sentences on what was updated and why]

## Previous State
[What the context file said before]

## New State
[What it says now]
```

## Output Summary

After applying all updates, report what you did in this format:

```
## Context Sync Complete

**Last sync:** [date of previous CONTEXT-SYNC decision log, or "first sync"]
**Sources scanned:** [list what you checked]

### Changes Applied
- [file]: [what changed and why]
- [file]: [what changed and why]

### No Changes Needed
- [file]: [still accurate because...]

### Decision Log
- [Created/None]: [filename if created]

### Nudge
Next sync recommended: [date 7 days from now]
```

If nothing has drifted, say so clearly — "Everything is current, no changes needed" is a valid and useful outcome. Don't manufacture changes to justify the scan.

## Error Handling

- **Context file unreadable/missing:** If any context file (`me.md`, `work.md`, `team.md`, `current_priorities.md`) is missing or empty, flag it to Kellen — these are foundational files that shouldn't be absent.
- **Git log fails:** Repo may not be initialized or may have no commits. Skip git-based drift detection and rely on file content comparison only.
- **Conflicting information:** If context files contradict each other (e.g., priorities says "3D on hold" but work says "3D is active"), flag the conflict rather than picking a side. Present both to Kellen for resolution.
- **Escalate immediately:** If context files contain what looks like stale student data or PII that shouldn't be there.
