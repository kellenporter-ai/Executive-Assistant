---
name: progress-report
description: Generate parent-friendly student progress reports from Portal Firestore data. Use when Kellen says "progress reports", "parent reports", "student reports", "pull grades", or needs to generate CSV reports for Infinite Campus or parent communication.
model: claude-sonnet-4-6
effort: medium
tools: [Bash, Read]
---

# Student Progress Report Pipeline

## Purpose
Two-stage pipeline that pulls student metrics from Firestore and generates bilingual (EN/ES) parent-friendly CSV reports.

## Prerequisites
- `tools/service-account.json` present (Firebase access)
- `tools/.venv/` set up with dependencies

## Steps

1. **Stage 1 — Pull Firestore data:**
   ```bash
   cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python tools/progress-reports.py
   ```

   Optional filters:
   - By class: `--class "AP Physics"`
   - By section: `--section "Period 3"`
   - Custom output: `--output path/to/output.json`

   Default output: `temp/progress-data-YYYY-MM-DD.json`

2. **Review the JSON.** Quick sanity check:
   - Student count looks right (expect ~106 across all classes)
   - No teacher/sandbox accounts leaked through
   - Engagement buckets are populated

3. **Stage 2 — Generate bilingual comments.** This is done inline by Claude Code (using subscription tokens, NOT an API key). For each class:
   - Read the JSON data for that class's students
   - Generate a personalized EN comment per student based on: completion rate, engagement bucket, time spent, XP earned
   - Generate the matching ES translation
   - Comments reflect **work ethic, not grades** — NO portal jargon (XP, engagement buckets, gamification terms). Translate engagement to plain language: THRIVING → "consistently engaged", INACTIVE → "not participating"
   - Launch parallel agents (one per class) for speed when multiple classes are involved

4. **Stage 3 — Merge into CSV:**
   Combine the JSON metrics + generated comments into `temp/progress-report-YYYY-MM-DD.csv`. Columns: Name, Email, Class, Period, Completion, Submitted/Total, Engagement, Time, XP, Submissions, Comment EN, Comment ES.

   Names in "Last, First" format for Infinite Campus compatibility.

5. **Report results.** Tell Kellen:
   - How many students across how many classes
   - Any data quality issues (missing engagement buckets, zero-completion students)
   - Where the CSV is saved
   - Remind: names are in "Last, First" format for Infinite Campus

## Output
- `temp/progress-data-YYYY-MM-DD.json` — raw metrics per student
- `temp/progress-report-YYYY-MM-DD.csv` — parent-ready bilingual report

## Language Rules
- NO portal jargon (XP, engagement buckets, gamification terms)
- Translate engagement to plain language: THRIVING -> "consistently engaged", INACTIVE -> "not participating", etc.
- Spanish translations included automatically

## Error Handling
- **Service account missing:** Tell Kellen to download from Firebase Console → Project Settings → Service Accounts.
- **No students returned:** Check `--class` filter spelling against actual class names in Firestore.
- **Stale data:** The script pulls live Firestore data. If numbers look wrong, check if assignments are marked `status: ACTIVE`.
