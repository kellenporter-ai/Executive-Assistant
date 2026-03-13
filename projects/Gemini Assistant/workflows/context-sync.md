# Workflow: Context Sync

Weekly context maintenance. Ensures priorities, project state, and memory stay aligned with reality.

## Step 1: Gather Current State

Read all context files:
- `context/current_priorities.md`
- `context/me.md`
- `context/work.md`
- `context/team.md`

Read recent git activity:
```bash
git log --oneline --since="2 weeks ago"
```

For each project repo:
```bash
cd projects/<dir> && git log --oneline --since="2 weeks ago"
```

## Step 2: Detect Priority Drift

Compare stated priorities against actual work done (git commits):
- Are there priorities with no recent commits? → May be stale or blocked.
- Is there significant work not reflected in priorities? → May need to be added.
- Have any priorities been completed? → Should be marked done.

## Step 3: Audit Memory

Read `memory/MEMORY.md` and scan memory files for:
- Stale project memories (decisions that have been superseded)
- Feedback memories that may no longer apply
- Missing memories for recent important decisions

## Step 4: Present Findings

```
## Context Sync Report

### Priority Alignment
| Priority | Recent Activity | Status |
|----------|----------------|--------|
| [priority] | [commits/work] | [Active / Stale / Complete] |

### Emerging Work (not yet in priorities)
- [work happening that isn't captured]

### Stale Memories
- [memories that may need updating or removal]

### Recommended Changes
1. [specific change to priorities]
2. [specific memory to update/remove]
```

## Step 5: Apply Changes

After user confirmation, update:
- `context/current_priorities.md`
- Any stale memory files
- `memory/MEMORY.md` index if needed

## Step 6: Log

Create a decision log entry:
```bash
# decisions/YYYY-MM-DD-context-sync.md
```

With the sync findings and changes made. Tag as `CONTEXT-SYNC`.
