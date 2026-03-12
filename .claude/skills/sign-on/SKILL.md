---
name: sign-on
description: >
  Workspace initialization when Kellen starts a session. Use when the user says "sign on",
  "good morning", "start session", "open up shop", "let's get started", or any variation
  of beginning a work session. Detects machine type, syncs repos, checks services,
  and shows a status dashboard.
model: claude-haiku-4-5-20251001
effort: low
tools: [Read, Bash, Glob]
---

# Sign On

You are initializing Kellen's workspace for a new session. This is the first thing that runs when he sits down to work. Be fast, surface problems early, and give him everything he needs to pick up where he left off.

## Steps

### 1. Detect Machine

Identify which machine Kellen is on by checking hardware:

```bash
# Check CPU model to distinguish desktop (9800x3d) from laptop
cat /proc/cpuinfo | grep "model name" | head -1
```

- **Desktop:** CPU contains "9800X3D" — full power mode, local LLM available
- **Laptop:** Anything else — note that local LLM (Ollama) is not available this session

Report which machine was detected.

### 2. Sync Repos

Pull latest changes on all repos. Handle errors gracefully — report them, don't crash.

```bash
# EA repo
cd "/home/kp/Desktop/Executive Assistant"
git fetch --all
git status
git pull --rebase

# Discover and sync all project repos (submodules and git repos in projects/)
for dir in /home/kp/Desktop/Executive\ Assistant/projects/*/; do
  if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
    echo "=== $(basename "$dir") ==="
    cd "$dir"
    git fetch --all
    git status
    git pull --rebase
  fi
done
```

**Check for problems:**
- If `git pull` fails due to merge conflicts, report the conflicting files and stop the pull. Tell Kellen which files conflict and ask how he wants to resolve them.
- If branches have diverged (ahead AND behind), report the divergence and ask before force-pulling or rebasing.
- If there are uncommitted changes that would be overwritten, stash them first and note that a stash was created.

### 3. Desktop-Only: Verify Ollama

Only run this if the machine was identified as the desktop:

```bash
# Check if Ollama service is running
systemctl status ollama --no-pager

# Check loaded/available models
ollama list
```

- If Ollama is running and qwen3:14b is available, report it as ready.
- If Ollama is not running, attempt to start it: `systemctl start ollama`
- If the model isn't pulled, note it but don't auto-pull (it's large).
- If on laptop, simply note: "Local LLM not available this session (laptop)."

### 4. Status Dashboard

Display a concise dashboard with this information:

```bash
# EA repo status
cd "/home/kp/Desktop/Executive Assistant"
echo "=== EA Repo ==="
git branch --show-current
git log --oneline -5
echo "--- Uncommitted ---"
git status --short

# All project repos
for dir in /home/kp/Desktop/Executive\ Assistant/projects/*/; do
  if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
    echo "=== $(basename "$dir") ==="
    cd "$dir"
    git branch --show-current
    git log --oneline -5
    echo "--- Uncommitted ---"
    git status --short
  fi
done
```

### 5. Show Current Priorities

Read and display `context/current_priorities.md` so Kellen can see what's on deck without having to ask.

### 6. Check Context Sync Freshness

Look at the most recent decision log entry tagged `CONTEXT-SYNC` to determine when the last context sync happened:

```bash
# Find most recent context sync
ls -t /home/kp/Desktop/Executive\ Assistant/decisions/ | head -20
```

Read any files that look like context sync entries. If the last sync was 7+ days ago (compare against today's date), nudge:

> "It's been [N] days since your last context sync. Want me to run one?"

If no sync has ever been logged, note that too.

## Output Format

Present everything as a clean dashboard:

```
## Good morning, Kellen

**Machine:** Desktop (9800X3D + 7900 XTX) / Laptop
**Local LLM:** Ready (qwen3:14b) / Not available (laptop)

### Repo Status
| Repo | Branch | Status | Last Commit |
|------|--------|--------|-------------|
| EA | master | Clean / 2 uncommitted | abc1234 — commit message |
| Portal | main | Clean / 1 uncommitted | def5678 — commit message |

### Uncommitted Work
[List any uncommitted changes, or "All clean"]

### Current Priorities
[Summary from current_priorities.md — just the top-level items, not the full file]

### Heads Up
- [Any sync nudges, merge issues, or service problems]
```

Keep it casual and scannable. Don't dump raw git output — summarize it.
