# Workflow: Sign Off

Clean session shutdown. Runs when the user ends a work session.

## Step 1: Check for Uncommitted Work

```bash
git status --short
```

For each project repo in `projects/`:
```bash
cd projects/<dir> && git status --short
```

If there are uncommitted changes, ask the user:
- Commit now? (draft a commit message)
- Stash for later?
- Leave as-is?

## Step 2: Push to Remote

If there are unpushed commits:
```bash
git log --oneline @{upstream}..HEAD
```

Ask the user if they want to push. Never force-push without explicit permission.

## Step 3: Update Priorities

Read `context/current_priorities.md`. Based on the session's work:
- Are any priorities now complete?
- Should any new priorities be added?
- Has priority ordering changed?

Present proposed updates for user confirmation before writing.

## Step 4: Consolidate Memory

Run the remember workflow (@workflows/remember.md) to extract and persist session learnings.

## Step 5: Session Summary

Present a brief summary:

```
## Session Summary

**Duration:** [approximate]
**Work Done:**
- [bullet points of completed tasks]

**Committed:** [yes/no — commit hashes if yes]
**Pushed:** [yes/no]
**Priorities Updated:** [yes/no]
**Memories Saved:** [count and brief descriptions]

**Open Items:**
- [anything left incomplete or needing follow-up]
```
