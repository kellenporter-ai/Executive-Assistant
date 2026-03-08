---
name: sign-off
description: >
  Clean shutdown when Kellen is done working. Use when the user says "sign off",
  "I'm done", "wrap up", "end session", "call it a day", "shut it down",
  "good night", or any variation of ending a work session. Commits outstanding work,
  pushes to remote, and summarizes the session.
model: claude-sonnet-4-6
---

# Sign Off

You are wrapping up Kellen's work session. The goal is a clean shutdown: nothing lost, everything pushed, priorities updated, and a clear record of what happened. Be thorough but don't drag it out.

## Steps

### 1. Survey Uncommitted Work

Check both repos for any uncommitted changes:

```bash
# EA repo
cd "/home/kp/Desktop/Executive Assistant"
echo "=== EA Repo ==="
git status --short
git diff --stat

# All project repos
for dir in /home/kp/Desktop/Executive\ Assistant/projects/*/; do
  if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
    echo "=== $(basename "$dir") ==="
    cd "$dir"
    git status --short
    git diff --stat
  fi
done
```

Present a clear summary of what's uncommitted in each repo. If everything is clean, say so and move to step 4.

### 2. Stage and Commit

For each repo with uncommitted changes:

1. Show Kellen exactly what will be committed (the summary from step 1).
2. Draft a concise commit message that summarizes the work. Follow the repo's existing commit style (check `git log --oneline -5` for reference).
3. **Ask Kellen to confirm** the commit message before committing. Present it like:
   > Proposed commit for EA repo: "Update skills and sync context files"
   > Proposed commit for Portal: "Add assessment analytics and fix grading UX"
   > Good to commit? (or suggest edits)
4. Once confirmed, stage and commit:

```bash
# EA repo
cd "/home/kp/Desktop/Executive Assistant"
git add -A
git commit -m "the confirmed message"

# Each project repo with uncommitted changes
cd "/home/kp/Desktop/Executive Assistant/projects/<project>"
git add -A
git commit -m "the confirmed message"
```

**Important:** If any submodule project was committed, also update the submodule reference in the EA repo:

```bash
cd "/home/kp/Desktop/Executive Assistant"
git add projects/<project>
git commit -m "Update <project> submodule reference"
```

### 3. Push to Remote

Push both repos after commits are made:

```bash
# EA repo
cd "/home/kp/Desktop/Executive Assistant"
git push

# All project repos that were committed
for dir in /home/kp/Desktop/Executive\ Assistant/projects/*/; do
  if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
    cd "$dir"
    git push
  fi
done
```

If a push fails (e.g., rejected due to remote changes), report the issue and ask how to proceed rather than force-pushing.

### 4. Check for Priority Drift

Read `context/current_priorities.md` and consider what was worked on during this session (look at the commits just made plus any conversation context).

Ask Kellen: "Did your priorities shift at all today? Here's what's currently listed: [top-level items]. Anything to add, remove, or reorder?"

If Kellen says yes, update the file. If no, move on.

### 5. Surface Unfinished Work

Scan for signals of incomplete work:

```bash
# Check for TODO/FIXME/HACK comments in recently modified files
cd "/home/kp/Desktop/Executive Assistant"
git diff HEAD~1 --name-only 2>/dev/null | head -20

# All project repos
for dir in /home/kp/Desktop/Executive\ Assistant/projects/*/; do
  if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
    echo "=== $(basename "$dir") ==="
    cd "$dir"
    git diff HEAD~1 --name-only 2>/dev/null | head -20
  fi
done
```

If recently modified files exist, scan them for TODO/FIXME/HACK markers. Also note any work that was discussed during the session but not completed.

Present any findings as a brief list:
> **Unfinished items to pick up next time:**
> - TODO in `src/grading.js:42` — implement rubric scoring
> - Discussed but didn't start: parent communication automation

### 6. Memory Consolidation

Run the `/remember` skill to capture any learnings from this session before wrapping up. Fold its output into the session summary (step 7) rather than printing it separately.

### 7. Decision Log Check

If significant decisions were made during this session (architecture choices, priority changes, tool adoptions, workflow changes), check whether they're logged in `decisions/`:

```bash
ls -t /home/kp/Desktop/Executive\ Assistant/decisions/ | head -5
```

If a decision from today's session isn't logged, ask: "We made a decision about [X] today — want me to log it?"

### 8. Session Summary

End with a concise summary of what got done:

```
## Session Wrap-Up

### Committed & Pushed
- EA repo: "commit message here" (N files changed)
- Portal: "commit message here" (N files changed)

### Priorities
[Updated / No changes]

### Pick Up Next Time
- [Any unfinished items or TODOs]

### Decisions Logged
- [Any new decision log entries, or "None needed"]

See you next time.
```

Keep it brief and human. This is the last thing Kellen sees before closing the laptop.
