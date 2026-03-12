---
name: skill-name-here
description: Describe exactly when and why this skill should be used.
model: claude-sonnet-4-6
effort: high          # low | medium | high | max — cognitive effort directive (optional, default: high)
tools: []             # authorized tools/agents for this skill (optional)
---

# Skill Name

## Purpose
What this skill does in one sentence.

## Steps

0. **(If applicable) Verify required references.** If this skill depends on reference files (e.g., `block-schema.md`, `rubric-format.md`), read them first. If any are missing, stop and tell Kellen which file is needed and where it should be created.

1. First step
2. Second step
3. ...

## Inputs
- What information is needed to run this skill

## Output
- What the skill produces

## Error Handling

Use the 5-step self-correction loop before escalating to Kellen:

1. **Read** — Parse the error message. Identify the failing component, line, or tool.
2. **Research** — Check if this is a known pattern (search codebase, read docs, check `agents/memory/SHARED.md`).
3. **Patch** — Apply a targeted fix. Change one thing at a time.
4. **Retry** — Re-run the failed step. If it fails again with a *different* error, loop back to step 1 (max 3 loops).
5. **Log** — Whether fixed or not, note what happened. If escalating, include: error message, what you tried, and why it didn't work.

**When to escalate immediately (skip self-correction):**
- Authentication or permission failures (can't self-fix credentials)
- Ambiguous requirements (need Kellen's decision, not a code fix)
- Data loss risk (destructive operations that can't be undone)

**Skill-specific error handling:**
- On [failure type]: [specific recovery action for this skill]
- Escalation: [when to surface to Kellen vs. retry for this skill]

## API Keys (if applicable)
This skill requires the following keys in `.env`:
- `API_KEY_NAME` — where to get it and what it's for
