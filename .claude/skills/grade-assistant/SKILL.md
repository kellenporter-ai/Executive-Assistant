---
name: grade-assistant
description: Run the local LLM grading assistant to suggest rubric grades for ungraded assessment submissions. Use when Kellen says "grade", "run grading", "AI grade", "suggest grades", "grade assessments", or wants to batch-grade student submissions using the local LLM.
model: claude-sonnet-4-6
---

# AI Grading Assistant

## Purpose
Use the local Ollama LLM (qwen3:14b) to pre-grade assessment submissions against their rubrics, writing suggested grades to Firestore for teacher review in the Portal UI.

## Steps

1. **Check Ollama availability:**
```bash
curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo "available" || echo "unavailable"
```
If unavailable, tell Kellen to start it: `systemctl start ollama`

2. **Check for the Firebase auth:**
```bash
gcloud auth application-default print-access-token > /dev/null 2>&1 && echo "authenticated" || echo "need auth"
```
If not authenticated, run: `gcloud auth application-default login`

3. **Run the grading script.** Choose the appropriate command based on what Kellen wants:

Grade ALL ungraded submissions:
```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python tools/grade-assistant.py
```

Grade a specific assessment (filter by title):
```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python tools/grade-assistant.py --assessment "TITLE"
```

Dry run (preview without writing):
```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python tools/grade-assistant.py --dry-run
```

Verbose mode (show prompts/responses for debugging):
```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python tools/grade-assistant.py --verbose
```

4. **Report results** to Kellen:
   - How many submissions were graded
   - Any failures
   - Remind them to review in the Portal's Assessments tab (suggested grades appear with an amber "AI Suggested" badge)

## Inputs
- Optional: assessment title filter (substring match)
- Optional: `--dry-run` flag to preview
- Optional: `--verbose` flag for debugging

## Output
- AI suggested grades written to Firestore (`aiSuggestedGrade` field on each submission)
- Grades appear in Portal's TeacherDashboard Assessments tab with "AI Suggested — Needs Review" indicator
- Teacher accepts/modifies/rejects each suggestion before it becomes final

## Requirements
- Ollama running locally with qwen3:14b model
- Firebase auth (gcloud ADC or service account)
- Python venv at `tools/.venv/` with `firebase-admin` and `requests`
