# Workflow: Remember

Consolidate session learnings into persistent memory. Run at session end, after significant tasks, or when the user explicitly asks to remember something.

## Step 1: Analyze Conversation

Review the recent conversation for:
- **User corrections** — "Don't do X", "Actually, use Y instead", "That's wrong because..."
- **User preferences** — communication style, workflow preferences, tool choices
- **Project facts** — deadlines, decisions, architecture changes, team updates
- **Technical gotchas** — bugs found, patterns discovered, things that broke unexpectedly
- **External references** — URLs, tools, services, dashboards mentioned

## Step 2: Check Existing Memory

Read `memory/MEMORY.md` to:
- Avoid creating duplicate memories
- Find existing memories that should be updated rather than duplicated
- Check the line count (must stay under 200)

## Step 3: Categorize and Write

For each learning worth persisting:

1. **Determine type:** `user`, `feedback`, `project`, or `reference`
2. **Create a memory file** in `memory/` with this format:

```markdown
---
name: descriptive-slug
description: One-line description used for relevance matching in future sessions
type: user | feedback | project | reference
---

[Content. For feedback/project types, structure as:]
[Rule or fact statement.]
**Why:** [The reason — often a past incident or strong preference]
**How to apply:** [When and where this guidance should influence behavior]
```

3. **Update `memory/MEMORY.md`** — Add a link to the new file with a brief description.

## Step 4: Prune Stale Memories

Check for memories that are no longer accurate:
- Project states that have changed
- Feedback that's been superseded by newer guidance
- References to systems no longer in use

Remove or update stale entries.

## Step 5: Report

Tell the user what was remembered:
```
**Memories saved:**
- [type] `filename.md` — description
- [type] `filename.md` — description

**Memories updated:** [list if any]
**Memories pruned:** [list if any]
```
