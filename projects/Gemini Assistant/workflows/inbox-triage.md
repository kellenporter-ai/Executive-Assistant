# Workflow: Inbox Triage & Classification

Autonomous pipeline for ingesting unstructured data from Gmail and organizing it into an actionable database.

## Prerequisites

This workflow requires Gmail tools to be configured. Calendar tools are optional but needed for meeting-related emails.

```bash
# Verify Gmail is set up (required)
app/.venv/bin/python3 -c "from tools.productivity.gmail.auth import get_gmail_service; svc, err = get_gmail_service(); print('Gmail ready' if svc else f'Not configured: {err}')"

# Verify Calendar is set up (optional — meeting triage will be skipped if unavailable)
app/.venv/bin/python3 -c "from tools.productivity.google_calendar.auth import get_calendar_service; svc, err = get_calendar_service(); print('Calendar ready' if svc else f'Not configured: {err}')"
```

If Gmail is not configured, inform the user and suggest they set up `GOOGLE_CLIENT_SECRET_FILE` or `GOOGLE_SERVICE_ACCOUNT_FILE` in their `.env` file. See `SETUP.md` for details. Do not proceed without working Gmail access.

If Calendar is not configured, proceed with email triage but skip meeting-related availability checks. Note this in the triage report.

## Step 1: Ingestion
1. **Search for new communications** using deterministic tools:
   ```bash
   app/.venv/bin/python3 tools/productivity/gmail/list_messages.py "is:unread"
   ```
2. **Identify the sender and intent.** Is it an internal request, a client inquiry, or general research?

## Step 2: Classification
Analyze the content and classify:
- **Actionable:** Contains specific deliverables, action verbs, and temporal deadlines → create a task.
- **Informational:** Contains valuable reference material or updates → log for reference.
- **Meeting-related:** Contains scheduling requests → check calendar availability using `tools/productivity/google_calendar/list_events.py` (skip if Calendar not configured — see Prerequisites).
- **Archive:** Completed items, outdated information, or resolved inquiries → no action needed.

## Step 3: Action & Delegation
1. **Update State Database:**
   - If a **Project** is identified:
     ```bash
     python3 tools/system/state_db.py add-project --name "[Project Name]" --category "Projects" --desc "[Brief Context]"
     ```
   - If a **Task** is identified:
     ```bash
     python3 tools/system/state_db.py add-task --project "[Project Name]" --desc "[Task Description]" --priority 2
     ```
2. **Log the classification** using the operational logger:
   ```bash
   python3 tools/system/log_action.py --agent "Manager" --action "Triage" --category "[Category]"
   ```
3. **Delegate to Sub-Agents:**
   - **Inquiry?** Pass to `research-agent` for context gathering.
   - **Meeting?** If Calendar is configured, check availability using `app/.venv/bin/python3 tools/productivity/google_calendar/list_events.py`, then draft a reply via `email-agent`. If Calendar is not configured, flag the meeting email for manual review.
   - **Reply needed?** Pass to `email-agent` to draft a response.

## Step 4: Verification
1. **Verify the database update.**
2. **Surface the triage results** to the user in the Daily Briefing.

## Error Handling
- **Ambiguous sender?** Flag for human review.
- **Tool failure?** Retry once, then log the error as "failure" in the operational log.
- **Gmail not configured?** Skip email ingestion and inform the user.
