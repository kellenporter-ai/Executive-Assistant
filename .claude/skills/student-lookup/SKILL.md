---
name: student-lookup
description: >
  Look up a student's submission status, enrollment, or investigate lost work.
  Use when Kellen says "look up [student]", "check [student]'s submissions",
  "where is [student]'s work", "student lost their work", "check enrollment for [student]",
  or any variation of investigating a specific student's data in Porter's Portal.
model: claude-haiku-4-5-20251001
---

# Student Lookup

Investigate a student's data in Porter's Portal via Firestore. This is a **read-only diagnostic** skill — it queries data and reports findings but never modifies student records.

## Step 1: Parse the Request

Extract from `<ARGUMENTS>`:
- **Student name** (required)
- **What to investigate** (optional): submissions, enrollment, lost work, draft status, engagement

If no student name is provided, ask: "Which student should I look up?"

## Step 2: Look Up the Student

Use the Firebase service account to query Firestore:

```bash
cd "/home/kp/Desktop/Executive Assistant" && python3 -c "
import json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate('tools/service-account.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()
# Search by name field (NOT displayName — it doesn't exist on student docs)
users = db.collection('users').where('name', '>=', 'STUDENT_NAME').where('name', '<=', 'STUDENT_NAME\uf8ff').limit(5).get()
for u in users:
    d = u.to_dict()
    print(json.dumps({
        'id': u.id,
        'name': d.get('name'),
        'classType': d.get('classType'),
        'section': d.get('section'),
        'enrolledClasses': d.get('enrolledClasses', []),
    }, indent=2))
"
```

**Key field reminders:**
- Enrollment: `classType` (string), `enrolledClasses` (array), `section` (string)
- Legacy/unused: `classes`, `classSections`, `displayName` — do NOT search by these

## Step 3: Investigation Chain (if checking submissions/lost work)

Follow this chain in order, stopping when you find the answer:

1. **`assessment_sessions`** — Check for active/completed sessions for this student
2. **`lesson_block_responses`** — Doc ID format: `{userId}_{assignmentId}_blocks`. Check if draft responses exist
3. **`lesson_block_responses_archive`** — Check if responses were archived (fresh-start anti-cheat)
4. **`submissions`** — Check final submission status, score, rubricGrade

```bash
cd "/home/kp/Desktop/Executive Assistant" && python3 -c "
import json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate('tools/service-account.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()
USER_ID = 'REPLACE_WITH_USER_ID'

# Check submissions
subs = db.collection('submissions').where('userId', '==', USER_ID).order_by('submittedAt', direction='DESCENDING').limit(20).get()
for s in subs:
    d = s.to_dict()
    print(json.dumps({
        'id': s.id,
        'assignmentTitle': d.get('assignmentTitle'),
        'status': d.get('status'),
        'score': d.get('score'),
        'submittedAt': str(d.get('submittedAt')),
        'isAssessment': d.get('isAssessment', False),
    }, indent=2))
"
```

## Step 4: Common Root Causes for Lost Work

If investigating "lost work", check these in order:

1. **Per-block "Lock In" but not "Submit Assessment"** — Student locked in answers on individual blocks but never clicked the final sticky green "Submit Assessment" button. Check `lesson_block_responses` for draft data.
2. **Tab closed before save** — Check `metricsSnapshot.lastActive` on the draft doc. If recent, data may be in localStorage on the student's Chromebook.
3. **Fresh-start anti-cheat** — Check `lesson_block_responses_archive` for archived responses. The Proctor archives old responses when detecting a fresh start.
4. **Submission deduplication** — Student may have retaken. Check for multiple submission docs with same `assignmentId`. Status `RETURNED` means teacher returned it for revision.

## Step 5: Report

Present findings in this format:

```markdown
## Student: [Name]
**ID:** [Firebase UID]
**Class:** [classType] — [section]
**Enrolled:** [enrolledClasses]

### Submission Summary
| Assignment | Status | Score | Date |
|-----------|--------|-------|------|
| ... | ... | ... | ... |

### Investigation Findings (if applicable)
[What was found, root cause assessment, recommended action]
```

## Important Reminders

- `score` field means XP on classwork, percentage on assessments — always check `isAssessment`
- Submissions have NO `classType` field — derive from the assignment's `classType`
- `RETURNED` status is valid — don't count it as a graded attempt
- `STARTED` status submissions are visible to admin — include them in reports
