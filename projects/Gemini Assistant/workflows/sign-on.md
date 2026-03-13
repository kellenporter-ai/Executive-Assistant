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

Look for the most recent context-sync entry in `decisions/`:
```bash
ls -t decisions/ | head -10
```

If the last context sync was 7+ days ago, nudge:
> "It's been [N] days since your last context sync. Want me to run one?"

## Step 4: Dashboard

Present a clean, scannable dashboard:

```
## Good morning

**Machine:** [hostname / CPU summary]
**Local LLM:** [Ready / Not available]

### Repo Status
| Repo | Branch | Status | Last Commit |
|------|--------|--------|-------------|
| [name] | [branch] | [clean/dirty] | [hash — message] |

### Current Priorities
[Top items from context/current_priorities.md]

### Heads Up
[Any sync nudges, merge issues, service problems, or stale context warnings]
```

Ask for the first task.
