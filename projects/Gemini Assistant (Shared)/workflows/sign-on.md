# Workflow: Sign On

Session initialization. Runs when the user starts a work session.

## Step 1: Detect Environment

```bash
# Identify OS, CPU, hostname
uname -a
hostname
cat /proc/cpuinfo | grep "model name" | head -1 2>/dev/null || sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown CPU"
```

Report the machine type. If a local LLM (Ollama) is expected on this machine, check:
```bash
curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo "Ollama: available" || echo "Ollama: not available"
```

## Step 2: Sync Repos

Pull latest changes on all git repos in the workspace:
```bash
git fetch --all && git status && git pull --rebase
```

For each subdirectory in `projects/` that is a git repo:
```bash
cd projects/<dir> && git fetch --all && git status && git pull --rebase
```

**Handle problems gracefully:**
- Merge conflicts → report conflicting files, ask user how to resolve
- Diverged branches → report divergence, ask before rebasing
- Uncommitted changes that would be overwritten → stash first, note the stash

## Step 3: Check Context Freshness

Read `memory/MEMORY.md` for cross-session knowledge.

Check recent logs for this session and broadly across all sessions:
```bash
python3 tools/system/get_logs.py # Current session only
python3 tools/system/get_logs.py --all # Overview of all active tasks
```

Look for the most recent context-sync entry in `decisions/`:
```bash
ls -t decisions/ | head -10
```

## Step 4: Dashboard

Present a clean, scannable dashboard:

```
## Good morning (Session ID: [GEMINI_SESSION_ID])

**Machine:** [hostname / CPU summary]
**Local LLM:** [Ready / Not available]

### Your Current Session Activity
[Summary from python3 tools/system/get_logs.py]

### Global Project Status
[Insert query output from: python3 tools/system/state_db.py summary]

### Active Elsewhere (Parallel Tasks)
[If `get_logs.py --all` shows other recent sessions, list their last actions here]

### Current Priorities
[Top items from context/current_priorities.md]
```

Ask for the first task.
