#!/usr/bin/env python3
"""
AI Grading Assistant — uses local LLM (Ollama) to suggest rubric grades.

Pulls ungraded assessment submissions from Firestore, sends each to qwen3:14b
with the rubric context, and writes suggested grades back. Teacher reviews
in the Portal UI before any grade is finalized.

Usage:
  ./grade-assistant.py                          # Grade all ungraded submissions
  ./grade-assistant.py --assessment "Blood"     # Filter by assessment title substring
  ./grade-assistant.py --dry-run                # Preview without writing to Firestore
  ./grade-assistant.py --verbose                # Show LLM prompts and responses
"""

import argparse
import json
import os
import sys
import re
import requests
from datetime import datetime
from tool_logger import get_tool_logger

# Add venv packages
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_SITE = os.path.join(SCRIPT_DIR, ".venv", "lib")
for d in os.listdir(VENV_SITE) if os.path.isdir(VENV_SITE) else []:
    site_pkg = os.path.join(VENV_SITE, d, "site-packages")
    if os.path.isdir(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

import firebase_admin
from firebase_admin import credentials, firestore

# --- Config ---
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("GRADE_MODEL", "qwen3:14b")
PROJECT_ID = "porters-portal"

TIER_LABELS = ["Missing", "Emerging", "Approaching", "Developing", "Refining"]
TIER_PERCENTAGES = [0, 55, 65, 85, 100]

logger = get_tool_logger("grade-assistant")


def init_firestore():
    """Initialize Firestore using service account key, ADC, or project-only init."""
    if not firebase_admin._apps:
        sa_path = os.path.join(SCRIPT_DIR, "service-account.json")
        if os.path.exists(sa_path):
            cred = credentials.Certificate(sa_path)
            firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
        else:
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
            except Exception:
                firebase_admin.initialize_app(options={"projectId": PROJECT_ID})
    return firestore.client()


def check_ollama():
    """Verify Ollama is running and the model is available."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        # Check if our model is available (handle tag formats like "qwen3:14b")
        model_base = MODEL.split(":")[0]
        available = any(model_base in m for m in models)
        if not available:
            print(f"Warning: Model '{MODEL}' not found. Available: {', '.join(models)}")
            return False
        return True
    except Exception as e:
        print(f"Error: Ollama not available at localhost:11434 — {e}")
        return False


def get_ungraded_submissions(db, assessment_filter=None):
    """Fetch assessment submissions that need AI grading."""
    # Get all assignments that are assessments
    assignments_ref = db.collection("assignments")
    assignments = {}
    for doc in assignments_ref.stream():
        data = doc.to_dict()
        if data.get("isAssessment"):
            if assessment_filter and assessment_filter.lower() not in data.get("title", "").lower():
                continue
            assignments[doc.id] = data

    if not assignments:
        print("No matching assessments found.")
        return []

    print(f"Found {len(assignments)} assessment(s):")
    for aid, a in assignments.items():
        print(f"  - {a.get('title', 'Untitled')} ({a.get('classType', '?')})")

    # Get submissions for these assessments
    results = []
    for assignment_id, assignment in assignments.items():
        if not assignment.get("rubric"):
            print(f"  Skipping '{assignment.get('title')}' — no rubric attached")
            continue

        subs_ref = db.collection("submissions").where("assignmentId", "==", assignment_id)
        for sub_doc in subs_ref.stream():
            sub = sub_doc.to_dict()
            sub["id"] = sub_doc.id

            # Skip if already has a final rubric grade
            if sub.get("rubricGrade"):
                continue

            # Skip if already has a pending AI suggestion
            ai_grade = sub.get("aiSuggestedGrade")
            if ai_grade and ai_grade.get("status") == "pending_review":
                continue

            # Skip trivial/started submissions
            if sub.get("status") == "STARTED":
                continue
            engagement = sub.get("metrics", {}).get("engagementTime", 0)
            score = sub.get("assessmentScore", {}).get("percentage", sub.get("score", 0))
            if engagement < 30 and score == 0:
                continue

            results.append({
                "submission": sub,
                "assignment": assignment,
            })

    return results


def get_corrections_for_assignment(db, assignment_id, max_examples=5):
    """Fetch recent teacher corrections for this assignment to use as few-shot examples."""
    try:
        corrections_ref = (
            db.collection("grading_corrections")
            .where("assignmentId", "==", assignment_id)
            .order_by("correctedAt", direction="DESCENDING")
            .limit(max_examples * 3)  # Fetch extra, then deduplicate by skill
        )
        corrections = []
        seen_skills = set()
        for doc in corrections_ref.stream():
            c = doc.to_dict()
            skill_key = c.get("skillId", "")
            if skill_key in seen_skills:
                continue
            seen_skills.add(skill_key)
            corrections.append(c)
            if len(corrections) >= max_examples:
                break
        return corrections
    except Exception as e:
        print(f"  Note: Could not fetch corrections (expected on first run): {e}")
        return []


def build_grading_prompt(assignment, submission, corrections=None):
    """Build a structured prompt for the LLM to grade a submission against a rubric."""
    rubric = assignment.get("rubric", {})
    title = assignment.get("title", "Assessment")
    block_responses = submission.get("blockResponses", {})
    assessment_score = submission.get("assessmentScore", {})
    per_block = assessment_score.get("perBlock", {})
    lesson_blocks = assignment.get("lessonBlocks", [])

    # Build question-answer pairs
    qa_pairs = []
    block_lookup = {b["id"]: b for b in lesson_blocks} if lesson_blocks else {}

    for block_id, response in block_responses.items():
        block = block_lookup.get(block_id, {})
        block_type = block.get("type", "UNKNOWN")
        question_text = block.get("content", f"Block {block_id[:8]}")
        auto_result = per_block.get(block_id, {})

        # Extract the answer
        if isinstance(response, dict):
            if "answer" in response:
                answer = str(response["answer"])
            elif "selected" in response:
                selected = response["selected"]
                options = block.get("options", [])
                answer = options[selected] if isinstance(selected, int) and selected < len(options) else str(selected)
            else:
                answer = json.dumps(response)
        else:
            answer = str(response) if response else "No answer"

        # Add auto-grade info if available
        auto_info = ""
        if auto_result:
            if auto_result.get("correct"):
                auto_info = " [AUTO-GRADED: CORRECT]"
            elif auto_result.get("needsReview"):
                auto_info = " [NEEDS MANUAL REVIEW]"
            else:
                auto_info = " [AUTO-GRADED: INCORRECT]"

                # Add correct answer for MC
                if block_type == "MC" and block.get("correctAnswer") is not None:
                    correct_idx = block["correctAnswer"]
                    options = block.get("options", [])
                    if correct_idx < len(options):
                        auto_info += f" (Correct: {options[correct_idx]})"

        qa_pairs.append({
            "question": question_text,
            "type": block_type,
            "answer": answer,
            "auto_info": auto_info,
        })

    # Build rubric context
    rubric_context = []
    question_ids = []
    for q in rubric.get("questions", []):
        q_id = q.get("id", "")
        question_ids.append(q_id)
        rubric_context.append(f"\n### {q.get('questionLabel', 'Question')}")
        for skill in q.get("skills", []):
            rubric_context.append(f"\n**Skill:** {skill.get('skillText', '')}")
            rubric_context.append(f"  Skill ID: {skill.get('id', '')}")
            for tier in skill.get("tiers", []):
                rubric_context.append(
                    f"  - {tier['label']} ({tier['percentage']}%): {tier.get('descriptor', 'No descriptor')}"
                )

    # Build the output schema
    output_schema = {"grades": {}}
    for q in rubric.get("questions", []):
        q_grades = {}
        for skill in q.get("skills", []):
            q_grades[skill["id"]] = {
                "suggestedTier": "integer 0-4 (0=Missing, 1=Emerging, 2=Approaching, 3=Developing, 4=Refining)",
                "confidence": "float 0.0-1.0",
                "rationale": "1-2 sentence explanation",
            }
        output_schema["grades"][q["id"]] = q_grades

    # Build few-shot correction examples
    correction_section = ""
    if corrections:
        examples = []
        for c in corrections:
            ai_tier = TIER_LABELS[c["aiSuggestedTier"]] if 0 <= c["aiSuggestedTier"] < 5 else "?"
            teacher_tier = TIER_LABELS[c["teacherSelectedTier"]] if 0 <= c["teacherSelectedTier"] < 5 else "?"
            examples.append(
                f"- Skill: \"{c.get('skillText', '?')[:80]}\"\n"
                f"  AI suggested: {ai_tier} ({c['aiSuggestedTier']}), Teacher corrected to: {teacher_tier} ({c['teacherSelectedTier']})\n"
                f"  AI rationale was: \"{c.get('aiRationale', 'N/A')[:100]}\""
            )
        correction_section = f"""

## Teacher Corrections (learn from these)
The teacher has previously corrected the following AI suggestions for this assessment.
Use these to calibrate your grading — if the teacher consistently grades higher or lower on certain skills, adjust accordingly.

{chr(10).join(examples)}
"""

    # Sanitize student answers to prevent prompt injection
    def sanitize(text, max_len=500):
        """Escape student text to prevent prompt injection via JSON-like or instruction-like content."""
        s = text[:max_len]
        # Escape triple-quotes and markdown fences that could break prompt structure
        s = s.replace('"""', '\\"\\"\\"')
        s = s.replace("```", "\\`\\`\\`")
        # Strip any instruction-like prefixes that could confuse the LLM
        s = re.sub(r'^\s*(system|assistant|user)\s*:', '', s, flags=re.IGNORECASE)
        return s

    prompt = f"""You are an expert teacher grading a student's assessment submission using a rubric.

## Assessment: {title}

## Student Responses
{chr(10).join(f"Q{i+1} ({qa['type']}): {sanitize(qa['question'], 200)}{qa['auto_info']}{chr(10)}Answer: {sanitize(qa['answer'])}" for i, qa in enumerate(qa_pairs))}

## Rubric
{''.join(rubric_context)}
{correction_section}
## Instructions
1. Evaluate each rubric skill against the student's responses
2. Select the tier (0-4) that best matches the evidence in their answers
3. For auto-graded correct answers, lean toward Developing (3) or Refining (4)
4. For auto-graded incorrect answers, evaluate partial understanding
5. For free-response answers needing review, carefully assess quality
6. Provide a brief rationale for each skill grade
7. Report your confidence (0.0-1.0) — lower if the response is ambiguous
8. If teacher corrections are provided above, adjust your grading tendencies to match the teacher's preferences

## CRITICAL: Output Format
Respond with ONLY valid JSON matching this exact structure (no markdown, no explanation outside the JSON):
{json.dumps(output_schema, indent=2)}

Replace the description strings with actual values. Use integer tier indices (0-4), float confidence (0.0-1.0), and string rationale."""

    return prompt, rubric


def call_ollama(prompt, verbose=False):
    """Send a grading prompt to the local LLM."""
    messages = [
        {
            "role": "system",
            "content": "You are a precise assessment grading assistant. You MUST respond with valid JSON only — no markdown fences, no explanations outside the JSON object. Be fair and consistent in your grading. /no_think"
        },
        {"role": "user", "content": prompt},
    ]

    if verbose:
        print(f"\n--- Prompt ({len(prompt)} chars) ---")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 4096,
        },
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
    resp.raise_for_status()
    content = resp.json().get("message", {}).get("content", "")

    if verbose:
        print(f"\n--- Response ({len(content)} chars) ---")
        print(content[:500] + "..." if len(content) > 500 else content)

    return content


def parse_llm_response(response_text, rubric):
    """Parse the LLM's JSON response into an AISuggestedGrade structure."""
    # Strip any markdown fences or think blocks
    text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  Error parsing LLM JSON: {e}")
        print(f"  Raw response: {text[:300]}")
        return None

    grades_data = data.get("grades", data)  # Handle both {"grades": {...}} and flat format

    # Build the AISuggestedGrade structure
    ai_grades = {}
    total_pct = 0
    count = 0

    for question in rubric.get("questions", []):
        q_id = question["id"]
        q_grades = grades_data.get(q_id, {})
        ai_grades[q_id] = {}

        for skill in question.get("skills", []):
            s_id = skill["id"]
            skill_grade = q_grades.get(s_id, {})

            tier = skill_grade.get("suggestedTier", 2)
            # Clamp tier to valid range
            tier = max(0, min(4, int(tier)))

            confidence = skill_grade.get("confidence", 0.5)
            confidence = max(0.0, min(1.0, float(confidence)))

            rationale = skill_grade.get("rationale", "No rationale provided")
            if not isinstance(rationale, str):
                rationale = str(rationale)

            percentage = TIER_PERCENTAGES[tier]

            ai_grades[q_id][s_id] = {
                "suggestedTier": tier,
                "percentage": percentage,
                "confidence": round(confidence, 2),
                "rationale": rationale[:300],  # Cap length
            }

            total_pct += percentage
            count += 1

    overall = round(total_pct / count) if count > 0 else 0

    return {
        "grades": ai_grades,
        "overallPercentage": overall,
        "suggestedAt": datetime.utcnow().isoformat() + "Z",
        "model": MODEL,
        "status": "pending_review",
    }


def grade_submissions(db, submissions, dry_run=False, verbose=False):
    """Grade a list of submissions using the local LLM."""
    total = len(submissions)
    success = 0
    failed = 0

    # Pre-fetch corrections per assignment (cached so we don't re-query for each sub)
    corrections_cache = {}

    for i, item in enumerate(submissions):
        sub = item["submission"]
        assignment = item["assignment"]
        student = sub.get("userName", "Unknown")
        title = assignment.get("title", "Assessment")
        aid = sub.get("assignmentId", "")

        # Fetch corrections for this assignment (once per assignment)
        if aid not in corrections_cache:
            corrections_cache[aid] = get_corrections_for_assignment(db, aid)
            if corrections_cache[aid]:
                print(f"  Loaded {len(corrections_cache[aid])} teacher corrections for few-shot calibration")

        print(f"\n[{i+1}/{total}] Grading {student} — {title}")

        try:
            prompt, rubric_raw = build_grading_prompt(assignment, sub, corrections=corrections_cache.get(aid))
            rubric = assignment.get("rubric", {})

            response = call_ollama(prompt, verbose=verbose)
            ai_grade = parse_llm_response(response, rubric)

            if not ai_grade:
                print(f"  FAILED: Could not parse LLM response")
                failed += 1
                continue

            # Show summary
            overall = ai_grade["overallPercentage"]
            grade_count = sum(len(skills) for skills in ai_grade["grades"].values())
            avg_confidence = 0
            conf_count = 0
            for q_grades in ai_grade["grades"].values():
                for s_grade in q_grades.values():
                    avg_confidence += s_grade["confidence"]
                    conf_count += 1
            avg_confidence = round(avg_confidence / conf_count, 2) if conf_count > 0 else 0

            print(f"  Suggested: {overall}% | {grade_count} skills graded | Avg confidence: {avg_confidence}")

            # Show per-skill breakdown
            for q in rubric.get("questions", []):
                q_grades = ai_grade["grades"].get(q["id"], {})
                for skill in q.get("skills", []):
                    sg = q_grades.get(skill["id"], {})
                    tier_idx = sg.get("suggestedTier", -1)
                    tier_name = TIER_LABELS[tier_idx] if 0 <= tier_idx < 5 else "?"
                    conf = sg.get("confidence", 0)
                    conf_bar = "!" if conf < 0.5 else "~" if conf < 0.75 else "+"
                    print(f"    [{conf_bar}] {tier_name:12s} ({sg.get('percentage', 0):3d}%) | {skill.get('skillText', '')[:60]}")

            if not dry_run:
                db.collection("submissions").document(sub["id"]).update({
                    "aiSuggestedGrade": ai_grade,
                })
                print(f"  Written to Firestore")

            logger.info(f"Graded {student} — {title}: {overall}%", extra={"data": {
                "submissionId": sub["id"],
                "assignmentId": aid,
                "overall": overall,
                "model": MODEL,
                "confidence": avg_confidence,
            }})
            success += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            logger.error(f"Failed to grade {student} — {title}: {e}", extra={"data": {
                "submissionId": sub.get("id", "unknown"),
                "error": str(e),
            }})
            failed += 1

    logger.info(f"Batch complete: {success}/{total} graded, {failed} failed")
    print(f"\n{'='*50}")
    print(f"Done. {success} graded, {failed} failed, {total} total.")
    if dry_run:
        print("(Dry run — no changes written to Firestore)")


def main():
    parser = argparse.ArgumentParser(description="AI Grading Assistant")
    parser.add_argument("--assessment", "-a", help="Filter by assessment title (substring match)")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Preview without writing to Firestore")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show LLM prompts and responses")
    args = parser.parse_args()

    # Check Ollama
    if not check_ollama():
        print("Start Ollama first: systemctl start ollama")
        sys.exit(1)

    # Init Firestore
    print("Connecting to Firestore...")
    db = init_firestore()

    # Find ungraded submissions
    print("Finding ungraded submissions...")
    submissions = get_ungraded_submissions(db, assessment_filter=args.assessment)

    if not submissions:
        print("No ungraded submissions found. Nothing to do.")
        return

    print(f"\nFound {len(submissions)} submission(s) to grade.")

    if args.dry_run:
        print("(Dry run mode — will not write to Firestore)")

    grade_submissions(db, submissions, dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
