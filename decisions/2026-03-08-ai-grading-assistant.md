# AI Grading Assistant — Local LLM for Assessment Grading

**Date:** 2026-03-08
**Status:** Implemented
**Category:** Teaching Automation

## Decision
Use the local Ollama LLM (qwen3:14b) as a grading assistant that pre-fills rubric grades for assessment submissions. Teacher always reviews before grades are finalized (human-in-the-loop).

## Architecture
- **Script:** `tools/grade-assistant.py` — Python script that pulls ungraded subs from Firestore, sends to Ollama, writes `aiSuggestedGrade` back
- **Skill:** `.claude/skills/grade-assistant/SKILL.md` — invocable via `/grade-assistant`
- **Types:** `AISuggestedGrade` and `AISuggestedSkillGrade` added to `types.ts`
- **Data layer:** `saveAISuggestedGrade`, `acceptAISuggestedGrade`, `dismissAISuggestedGrade` in `dataService.ts`
- **UI:** TeacherDashboard shows amber "AI Suggested" badges, stat card, and filter; RubricViewer shows AI rationale + confidence per skill
- **Venv:** `tools/.venv/` with `firebase-admin` and `requests` packages

## Why Local LLM
- Free compute on 7900 XTX (no API cost)
- ~2.1M tokens/semester offloaded from Claude API
- Real value is time savings: ~40-80 hours/semester grading reduction
- Acceptable quality for pre-filling (teacher still validates)

## Feedback Loop
When the teacher modifies an AI-suggested tier before saving, the delta is recorded to `grading_corrections` in Firestore:
- Stores: skill text, AI tier, teacher tier, AI rationale, student answer snippet
- Next grading run fetches up to 5 corrections per assessment as few-shot examples
- Injected into prompt as "Teacher Corrections (learn from these)" section
- Self-improving: accuracy increases as more corrections accumulate

## Reliability Strategies
- Structured JSON output format (`format: "json"` in Ollama)
- Per-skill grading (focused decisions)
- Rubric tier descriptors included as context
- Confidence scores (low confidence flagged in UI)
- Auto-grade results passed as context (correct/incorrect/needs-review)
- Few-shot calibration from teacher corrections (feedback loop)

## What This Does NOT Do
- Assign final grades without teacher review
- Grade without a rubric attached
- Work on non-assessment assignments
- Send notifications to students (only final save does that)

## Trade-offs
- qwen3:14b may hallucinate rubric alignment on nuanced responses
- Requires Ollama running on desktop (not available on laptop)
- Firebase ADC or service account needed for the script
