---
name: grade-assistant
description: Batch-grade ungraded Portal assessments using local LLM (Ollama). Use when Kellen says "grade submissions", "run the grader", "AI grade", "suggest grades", or wants to process ungraded assessment work.
model: claude-sonnet-4-6
effort: medium
tools: [Bash, Read]
---

# AI Grading Assistant

## Purpose
Run the local LLM grading pipeline to suggest rubric grades for ungraded Portal assessment submissions.

## Prerequisites
- Ollama running at `localhost:11434` with `qwen3:14b`
- `tools/service-account.json` present (Firebase access)
- `tools/.venv/` set up with dependencies

## Steps

1. **Check Ollama availability:**
   ```bash
   curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo "available" || echo "unavailable"
   ```
   If unavailable, tell Kellen and stop.

2. **Run the grading script.** Choose flags based on Kellen's request:
   - All ungraded: `tools/.venv/bin/python tools/grade-assistant.py`
   - Specific assessment: `tools/.venv/bin/python tools/grade-assistant.py --assessment "TITLE"`
   - Preview only: add `--dry-run`
   - Debug: add `--verbose`

3. **Report results.** Summarize:
   - How many submissions were graded
   - Any errors or skipped submissions
   - Remind Kellen that grades are `pending_review` — teacher must accept in TeacherDashboard

## Output
- AI suggested grades written to Firestore (`aiSuggestedGrade` on submission docs)
- Status: `pending_review` until teacher accepts/rejects in Portal UI
- Visible in TeacherDashboard as amber Sparkles badges

## Error Handling
- **Ollama down:** Tell Kellen to start it (`systemctl start ollama`). Do not retry.
- **Service account missing:** Tell Kellen to download from Firebase Console. Do not retry.
- **LLM returns malformed JSON:** Script handles this internally with retries. If persistent, suggest `--verbose` to diagnose.
- **Firestore permission error:** Check service account has read/write access to `submissions` collection.
