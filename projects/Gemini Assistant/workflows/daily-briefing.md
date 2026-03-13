# Workflow: Daily Briefing

Summarize recent activity and surface what's next. Quick catch-up for the user.

## Step 1: Recent Activity

```bash
# Last 48 hours of commits
git log --oneline --since="2 days ago" --all
```

For each project repo:
```bash
cd projects/<dir> && git log --oneline --since="2 days ago" --all
```

## Step 2: Current State

- Read `context/current_priorities.md`
- Read `memory/MEMORY.md` for any recent project memories
- Check for uncommitted work: `git status --short`

## Step 3: Present Briefing

```
## Briefing

### What Happened Recently
- [bullet points of recent commits/work, grouped by project]

### Current Priorities
- [top items from current_priorities.md with progress notes]

### Open Items
- [uncommitted work, pending decisions, blocked tasks]

### Suggested Focus
[Based on priorities and recent momentum, suggest what to work on next]
```

Keep it scannable. No walls of text.
