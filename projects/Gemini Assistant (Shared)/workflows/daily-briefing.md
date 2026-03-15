# Workflow: Daily Briefing

Summarize recent activity and surface what's next using the local state database and operational logs.

## Step 1: Gather Intelligence
1. **Query State Database:** Get active projects and pending tasks.
   ```bash
   python3 tools/system/state_db.py summary
   ```
2. **Retrieve Recent Activity:** Use the log analysis tool.
   ```bash
   python3 tools/system/get_logs.py --hours 24
   ```
3. **Check Git Activity:** (Optional) See recent code changes.
   ```bash
   git log --oneline --since="2 days ago"
   ```

## Step 2: Synthesis
- **Accomplishments:** Summarize successful actions from the logs.
- **Current Load:** List active projects and their top-priority tasks.
- **Blockers:** Identify any "failure" or "blocked" statuses in the logs/database.

## Step 3: Present Briefing
Present a clean, scannable dashboard to the user.
