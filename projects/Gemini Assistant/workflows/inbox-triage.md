# Workflow: Inbox Triage & P.A.R.A Classification

Autonomous pipeline for ingesting unstructured data from Gmail/Slack and organizing it into an actionable database.

## Step 1: Ingestion
1. **Search for new communications** using deterministic tools:
   ```bash
   # List unread Gmail messages
   app/.venv/bin/python3 tools/productivity/gmail/list_messages.py "is:unread"
   ```
2. **Identify the sender and intent.** Is it an internal request, a client inquiry, or general research?

## Step 2: Classification (P.A.R.A)
Analyze the content and classify into one of four categories:
- **Projects:** Contains specific deliverables, action verbs, and temporal deadlines.
- **Areas:** Relates to ongoing spheres of responsibility (e.g., Finance, HR, Admin).
- **Resources:** Contains valuable reference material, market research, or industry news.
- **Archive:** Completed project data, outdated information, or resolved inquiries.

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
2. **Delegate to Sub-Agents:**
   - **Inquiry?** Pass to `backend-engineer` or `researcher` for context gathering.
   - **Meeting?** Pass to `Calendar Agent` to check availability.
   - **Reply needed?** Pass to `content-writer` (Email Agent) to draft a response.

## Step 4: Verification
1. **Verify the database update** (Airtable/Notion/Local Log).
2. **Surface the triage results** to the user in the Daily Briefing.

## Error Handling
- **Ambiguous sender?** Mark as "Archive" and flag for human review.
- **Tool failure?** Retry once, then log the error as "failure" in the operational log.
