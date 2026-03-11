#!/usr/bin/env python3
"""
Student Progress Report Generator — bilingual (EN/ES) progress comments.

Pulls telemetry from Porter's Portal Firestore, aggregates per-student metrics,
generates personalized 25-50 word bilingual comments via Claude API, and outputs
CSV for copy-paste into Infinite Campus.

Usage:
  ./progress-reports.py                        # All classes, all students
  ./progress-reports.py --class "AP Physics"   # Filter by class
  ./progress-reports.py --section "Period 3"   # Filter by section/period
  ./progress-reports.py --dry-run              # Preview data without generating comments
  ./progress-reports.py --output report.csv    # Custom output file
  ./progress-reports.py --verbose              # Show raw data and API calls

Prerequisites:
  1. tools/service-account.json (Firebase service account key)
  2. ANTHROPIC_API_KEY in .env or environment variable
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

# Add venv packages
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_SITE = os.path.join(SCRIPT_DIR, ".venv", "lib")
for d in os.listdir(VENV_SITE) if os.path.isdir(VENV_SITE) else []:
    site_pkg = os.path.join(VENV_SITE, d, "site-packages")
    if os.path.isdir(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

# Load .env file
ENV_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

import firebase_admin
from firebase_admin import credentials, firestore
import anthropic

# --- Config ---
PROJECT_ID = "porters-portal"
CLAUDE_MODEL = "claude-sonnet-4-6-20250514"

TIER_LABELS = ["Missing", "Emerging", "Approaching", "Developing", "Refining"]
BUCKET_LABELS = {
    "THRIVING": "thriving",
    "ON_TRACK": "on track",
    "COASTING": "coasting",
    "SPRINTING": "sprinting",
    "STRUGGLING": "struggling",
    "DISENGAGING": "disengaging",
    "INACTIVE": "inactive",
    "COPYING": "showing academic integrity concerns",
}


def init_firestore():
    """Initialize Firestore using service account key or ADC."""
    if not firebase_admin._apps:
        sa_path = os.path.join(SCRIPT_DIR, "service-account.json")
        if os.path.exists(sa_path):
            cred = credentials.Certificate(sa_path)
            firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
            print("  Authenticated via service account key")
        else:
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
                print("  Authenticated via Application Default Credentials")
            except Exception:
                print("ERROR: No service account key found at tools/service-account.json")
                print("       Download from Firebase Console → Project Settings → Service Accounts")
                sys.exit(1)
    return firestore.client()


def init_claude():
    """Initialize Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment or .env file")
        print("       Add ANTHROPIC_API_KEY=sk-ant-... to .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


# =============================================================================
# DATA PULL
# =============================================================================

def fetch_students(db, class_filter=None, section_filter=None):
    """Fetch all students, optionally filtered by class and section."""
    query = db.collection("users").where("role", "==", "STUDENT")
    students = {}
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id

        # Filter by class
        enrolled = data.get("enrolledClasses", [])
        class_type = data.get("classType", "")
        if class_filter:
            if class_filter not in enrolled and class_filter != class_type:
                continue

        # Filter by section
        if section_filter:
            class_sections = data.get("classSections", {})
            section = data.get("section", "")
            matching = any(s == section_filter for s in class_sections.values())
            if not matching and section != section_filter:
                continue

        students[doc.id] = data
    return students


def fetch_submissions(db, student_ids, class_filter=None):
    """Fetch all submissions for the given students."""
    submissions = defaultdict(list)
    # Firestore 'in' queries limited to 30 items — batch
    id_list = list(student_ids)
    for i in range(0, len(id_list), 30):
        batch = id_list[i:i+30]
        query = db.collection("submissions").where("userId", "in", batch)
        if class_filter:
            query = query.where("classType", "==", class_filter)
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            submissions[data["userId"]].append(data)
    return submissions


def fetch_assignments(db, class_filter=None):
    """Fetch all assignments (for completion rate calculation)."""
    query = db.collection("assignments").where("status", "==", "ACTIVE")
    if class_filter:
        query = query.where("classType", "==", class_filter)
    assignments = {}
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        assignments[doc.id] = data
    return assignments


def fetch_buckets(db, student_ids, class_filter=None):
    """Fetch most recent engagement bucket for each student+class pair."""
    buckets = {}  # keyed by (studentId, classType)
    id_list = list(student_ids)
    for i in range(0, len(id_list), 30):
        batch = id_list[i:i+30]
        query = db.collection("student_buckets").where("studentId", "in", batch)
        if class_filter:
            query = query.where("classType", "==", class_filter)
        for doc in query.stream():
            data = doc.to_dict()
            key = (data["studentId"], data.get("classType", ""))
            # Keep the most recent bucket per student+class
            existing = buckets.get(key)
            if existing is None:
                buckets[key] = data
            else:
                # Compare createdAt safely (handles Timestamp, str, or missing)
                new_ts = data.get("createdAt")
                old_ts = existing.get("createdAt")
                if new_ts and old_ts and type(new_ts) == type(old_ts):
                    try:
                        if new_ts > old_ts:
                            buckets[key] = data
                    except TypeError:
                        buckets[key] = data
                elif new_ts and not old_ts:
                    buckets[key] = data
    return buckets


def fetch_alerts(db, student_ids, class_filter=None):
    """Fetch active (non-dismissed) alerts for students."""
    alerts = defaultdict(list)
    id_list = list(student_ids)
    for i in range(0, len(id_list), 30):
        batch = id_list[i:i+30]
        query = db.collection("student_alerts").where("studentId", "in", batch)
        if class_filter:
            query = query.where("classType", "==", class_filter)
        for doc in query.stream():
            data = doc.to_dict()
            if not data.get("isDismissed"):
                alerts[data["studentId"]].append(data)
    return alerts


# =============================================================================
# AGGREGATION
# =============================================================================

def aggregate_student_data(student, subs, assignments, buckets_map, alert_list):
    """Aggregate a single student's data into a report-ready dict."""
    name = student.get("name", "Unknown")
    enrolled = student.get("enrolledClasses", [])
    class_sections = student.get("classSections", {})
    section = student.get("section", "")
    gamification = student.get("gamification", {})
    stats = student.get("stats", {})

    # Per-class aggregation
    class_reports = {}
    for class_type in enrolled:
        class_subs = [s for s in subs if s.get("classType") == class_type]
        class_assignments = {k: v for k, v in assignments.items() if v.get("classType") == class_type}

        # Scores — best per assignment (handles retakes)
        best_scores = {}
        for sub in class_subs:
            aid = sub.get("assignmentId", "")
            if sub.get("status") == "STARTED":
                continue
            score = sub.get("assessmentScore", {}).get("percentage", sub.get("score", 0)) or 0
            if aid not in best_scores or score > best_scores[aid]:
                best_scores[aid] = score

        scores = list(best_scores.values())
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        # Completion rate — unique assignments submitted / total active assignments
        submitted_ids = set(s.get("assignmentId") for s in class_subs if s.get("status") != "STARTED")
        total_assignments = len(class_assignments)
        completion_rate = round(len(submitted_ids) / total_assignments * 100, 1) if total_assignments else 0
        completion_rate = min(completion_rate, 100.0)

        # Engagement metrics from submissions
        total_time = sum(s.get("metrics", {}).get("engagementTime", 0) for s in class_subs)
        total_keystrokes = sum(s.get("metrics", {}).get("keystrokes", 0) for s in class_subs)
        total_pastes = sum(s.get("metrics", {}).get("pasteCount", 0) for s in class_subs)
        submission_count = len([s for s in class_subs if s.get("status") != "STARTED"])

        # Rubric tier distribution (from graded work)
        tier_counts = defaultdict(int)
        graded_count = 0
        for sub in class_subs:
            rubric_grade = sub.get("rubricGrade")
            if rubric_grade and isinstance(rubric_grade, dict):
                for q_grades in rubric_grade.values():
                    if isinstance(q_grades, dict):
                        for s_grade in q_grades.values():
                            if isinstance(s_grade, dict) and "tier" in s_grade:
                                tier_counts[s_grade["tier"]] += 1
                                graded_count += 1

        # Engagement bucket — keyed by (studentId, classType)
        bucket_data = buckets_map.get((student["id"], class_type))
        bucket = bucket_data.get("bucket", "UNKNOWN") if bucket_data else "UNKNOWN"
        engagement_score = bucket_data.get("engagementScore", 0) if bucket_data else 0

        # Alerts for this class
        class_alerts = [a for a in alert_list if a.get("classType") == class_type]
        risk_level = None
        risk_reasons = []
        for alert in class_alerts:
            level = alert.get("riskLevel")
            if risk_level is None or {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}.get(level, 0) > \
                    {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}.get(risk_level, 0):
                risk_level = level
            risk_reasons.append(alert.get("reason", ""))

        # XP
        class_xp = gamification.get("classXp", {}).get(class_type, 0)
        level = gamification.get("level", 1)

        period = class_sections.get(class_type, section) or "?"

        class_reports[class_type] = {
            "period": period,
            "avg_score": avg_score,
            "completion_rate": completion_rate,
            "submission_count": submission_count,
            "total_time_minutes": round(total_time / 60, 1),
            "total_keystrokes": total_keystrokes,
            "total_pastes": total_pastes,
            "bucket": bucket,
            "engagement_score": round(engagement_score, 1),
            "risk_level": risk_level,
            "risk_reasons": list(set(risk_reasons)),
            "xp": class_xp,
            "level": level,
            "tier_distribution": dict(tier_counts),
            "graded_skills": graded_count,
            "assignments_submitted": len(submitted_ids),
            "assignments_total": total_assignments,
        }

    return {
        "id": student["id"],
        "name": name,
        "email": student.get("email", ""),
        "classes": class_reports,
    }


# =============================================================================
# COMMENT GENERATION
# =============================================================================

def generate_comments_batch(client, student_reports, class_type, verbose=False):
    """Generate bilingual progress comments for a batch of students via Claude API.
    Returns dict keyed by student ID."""
    # Build indexed student data for the prompt
    indexed_students = []  # (index, report, summary_text)
    for idx, report in enumerate(student_reports):
        cr = report["classes"].get(class_type)
        if not cr:
            continue

        bucket_label = BUCKET_LABELS.get(cr["bucket"], cr["bucket"].lower())
        risk_info = ""
        if cr["risk_level"]:
            reasons = ", ".join(r.replace("_", " ").lower() for r in cr["risk_reasons"] if r)
            risk_info = f" RISK: {cr['risk_level']} ({reasons})."

        tier_info = ""
        if cr["tier_distribution"]:
            tier_parts = []
            for t in range(5):
                count = cr["tier_distribution"].get(t, 0)
                if count > 0:
                    tier_parts.append(f"{TIER_LABELS[t]}: {count}")
            tier_info = f" Rubric tiers: {', '.join(tier_parts)}."

        summary = (
            f"- [{idx}] {report['name']} | "
            f"Avg: {cr['avg_score']}%, "
            f"Completion: {cr['completion_rate']}% ({cr['assignments_submitted']}/{cr['assignments_total']}), "
            f"Engagement: {bucket_label} (ES: {cr['engagement_score']}), "
            f"Time: {cr['total_time_minutes']}min, "
            f"Submissions: {cr['submission_count']}, "
            f"XP: {cr['xp']}.{risk_info}{tier_info}"
        )
        indexed_students.append((idx, report, summary))

    if not indexed_students:
        return {}

    student_summaries = [s[2] for s in indexed_students]

    prompt = f"""You are writing brief progress report comments for a high school {class_type} class at Perth Amboy High School. The student population is ~91% Hispanic with 71% Spanish-speaking homes.

For each student below, write TWO comments:
1. **English** (25-50 words): A personalized, growth-oriented progress comment suitable for an official report card. Address strengths and areas for growth. Be specific to their data — don't be generic. Use the student's first name.
2. **Spanish** (25-50 words): A natural Spanish translation of the English comment. Not robotic Google Translate — write it how a bilingual teacher would actually say it to a parent.

Tone: warm, professional, encouraging but honest. If a student is struggling or at risk, be direct about it while framing it constructively. If a student is thriving, celebrate specifically.

Key data points to reference:
- Avg score: their average across graded work
- Completion rate: what percentage of assigned work they've submitted
- Engagement bucket: behavioral pattern (thriving, on track, coasting, struggling, etc.)
- Risk alerts: early warning flags if present
- Rubric tiers: distribution of skill ratings (Missing/Emerging/Approaching/Developing/Refining)

STUDENT DATA (each prefixed with [index]):
{chr(10).join(student_summaries)}

OUTPUT FORMAT — respond with ONLY valid JSON, no markdown fences.
Use the numeric index (as a string) as the key for each student:
{{
  "comments": {{
    "0": {{
      "en": "English comment here.",
      "es": "Spanish comment here."
    }},
    "1": {{
      "en": "...",
      "es": "..."
    }}
  }}
}}"""

    if verbose:
        print(f"\n--- API Prompt ({len(prompt)} chars) ---")
        print(prompt[:800] + "..." if len(prompt) > 800 else prompt)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        temperature=0.4,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    if verbose:
        print(f"\n--- API Response ({len(text)} chars) ---")
        print(text[:800] + "..." if len(text) > 800 else text)

    # Parse JSON response — strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
        raw_comments = data.get("comments", {})
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing API response: {e}")
        print(f"  Raw: {text[:300]}")
        return {}

    # Map indexed keys back to student IDs
    result = {}
    for idx, report, _ in indexed_students:
        comment = raw_comments.get(str(idx))
        if comment:
            result[report["id"]] = comment
        else:
            print(f"    Warning: no comment generated for [{idx}] {report['name']}")

    return result


# =============================================================================
# OUTPUT
# =============================================================================

def write_csv(student_reports, comments_by_class, output_path, class_filter=None):
    """Write the final CSV report."""
    rows = []
    for report in student_reports:
        for class_type, cr in report["classes"].items():
            if class_filter and class_type != class_filter:
                continue

            comments = comments_by_class.get(class_type, {})
            student_comments = comments.get(report["id"], {})
            en_comment = student_comments.get("en", "")
            es_comment = student_comments.get("es", "")

            bucket_label = BUCKET_LABELS.get(cr["bucket"], cr["bucket"].lower())
            risk_str = cr["risk_level"] or "None"

            rows.append({
                "Student Name": report["name"],
                "Email": report["email"],
                "Class": class_type,
                "Period": cr["period"],
                "Avg Score (%)": cr["avg_score"],
                "Completion (%)": cr["completion_rate"],
                "Submitted/Total": f"{cr['assignments_submitted']}/{cr['assignments_total']}",
                "Engagement": bucket_label,
                "Engagement Score": cr["engagement_score"],
                "Risk Level": risk_str,
                "Time (min)": cr["total_time_minutes"],
                "Submissions": cr["submission_count"],
                "XP": cr["xp"],
                "Comment (EN)": en_comment,
                "Comment (ES)": es_comment,
            })

    # Sort by class, then period, then name
    rows.sort(key=lambda r: (r["Class"], r["Period"], r["Student Name"]))

    if not rows:
        print("No data to write.")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nReport written to: {output_path}")
    print(f"  {len(rows)} student-class rows")


def print_summary(student_reports, class_filter=None):
    """Print a quick summary table to terminal."""
    print(f"\n{'='*80}")
    print(f"  STUDENT PROGRESS SUMMARY")
    print(f"{'='*80}")

    # Group by class
    by_class = defaultdict(list)
    for report in student_reports:
        for class_type, cr in report["classes"].items():
            if class_filter and class_type != class_filter:
                continue
            by_class[class_type].append((report["name"], cr))

    for class_type, students in sorted(by_class.items()):
        print(f"\n  {class_type} ({len(students)} students)")
        print(f"  {'─'*76}")
        print(f"  {'Name':<25} {'Score':>6} {'Comp':>6} {'Engage':<12} {'Risk':<10} {'XP':>6}")
        print(f"  {'─'*76}")

        students.sort(key=lambda x: x[1]["period"])
        current_period = None
        for name, cr in students:
            if cr["period"] != current_period:
                current_period = cr["period"]
                print(f"  --- {current_period} ---")

            bucket = BUCKET_LABELS.get(cr["bucket"], cr["bucket"][:10])
            risk = cr["risk_level"] or "—"
            print(f"  {name:<25} {cr['avg_score']:>5.1f}% {cr['completion_rate']:>5.1f}% {bucket:<12} {risk:<10} {cr['xp']:>5}")

        # Class averages
        avg_score = sum(s[1]["avg_score"] for s in students) / len(students) if students else 0
        avg_comp = sum(s[1]["completion_rate"] for s in students) / len(students) if students else 0
        print(f"  {'─'*76}")
        print(f"  {'CLASS AVG':<25} {avg_score:>5.1f}% {avg_comp:>5.1f}%")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Student Progress Report Generator")
    parser.add_argument("--class", "-c", dest="class_filter", help="Filter by class (e.g., 'AP Physics')")
    parser.add_argument("--section", "-s", help="Filter by section/period (e.g., 'Period 3')")
    parser.add_argument("--output", "-o", default=None, help="Output CSV path (default: temp/progress-report-YYYY-MM-DD.csv)")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Pull data and show summary without generating comments")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show raw data and API calls")
    args = parser.parse_args()

    # Output path
    if args.output:
        output_path = args.output
    else:
        os.makedirs(os.path.join(os.path.dirname(SCRIPT_DIR), "temp"), exist_ok=True)
        output_path = os.path.join(
            os.path.dirname(SCRIPT_DIR), "temp",
            f"progress-report-{datetime.now().strftime('%Y-%m-%d')}.csv"
        )

    # Init services
    print("Connecting to Firestore...")
    db = init_firestore()

    if not args.dry_run:
        print("Initializing Claude API...")
        claude = init_claude()

    # Fetch data
    print("Fetching students...")
    students = fetch_students(db, class_filter=args.class_filter, section_filter=args.section)
    print(f"  Found {len(students)} students")

    if not students:
        print("No students found matching filters.")
        return

    student_ids = set(students.keys())

    print("Fetching submissions...")
    submissions = fetch_submissions(db, student_ids, class_filter=args.class_filter)
    total_subs = sum(len(v) for v in submissions.values())
    print(f"  Found {total_subs} submissions")

    print("Fetching assignments...")
    assignments = fetch_assignments(db, class_filter=args.class_filter)
    print(f"  Found {len(assignments)} active assignments")

    print("Fetching engagement buckets...")
    buckets = fetch_buckets(db, student_ids, class_filter=args.class_filter)
    print(f"  Found {len(buckets)} bucket profiles")

    print("Fetching risk alerts...")
    alerts = fetch_alerts(db, student_ids, class_filter=args.class_filter)
    total_alerts = sum(len(v) for v in alerts.values())
    print(f"  Found {total_alerts} active alerts")

    # Aggregate
    print("\nAggregating student data...")
    student_reports = []
    for sid, student in students.items():
        report = aggregate_student_data(
            student,
            submissions.get(sid, []),
            assignments,
            buckets,
            alerts.get(sid, []),
        )
        if report["classes"]:
            student_reports.append(report)

    print(f"  Aggregated {len(student_reports)} students with class data")

    # Summary
    print_summary(student_reports, class_filter=args.class_filter)

    if args.dry_run:
        print("\n(Dry run — skipping comment generation and CSV output)")
        return

    # Generate comments — batch by class (max ~30 students per API call)
    print("\nGenerating bilingual progress comments...")
    comments_by_class = {}

    # Determine which classes to process
    all_classes = set()
    for report in student_reports:
        for ct in report["classes"]:
            if args.class_filter and ct != args.class_filter:
                continue
            all_classes.add(ct)

    for class_type in sorted(all_classes):
        class_students = [r for r in student_reports if class_type in r["classes"]]
        print(f"\n  {class_type}: {len(class_students)} students")

        # Batch into groups of 25 to stay within token limits
        for batch_start in range(0, len(class_students), 25):
            batch = class_students[batch_start:batch_start+25]
            batch_end = min(batch_start + 25, len(class_students))
            print(f"    Generating comments for students {batch_start+1}-{batch_end}...")

            batch_comments = generate_comments_batch(
                claude, batch, class_type, verbose=args.verbose
            )

            if class_type not in comments_by_class:
                comments_by_class[class_type] = {}
            comments_by_class[class_type].update(batch_comments)

            # Rate limit between batches
            if batch_end < len(class_students):
                time.sleep(2)

    # Write CSV
    print("\nWriting CSV...")
    write_csv(student_reports, comments_by_class, output_path, class_filter=args.class_filter)

    # Final stats
    total_comments = sum(len(v) for v in comments_by_class.values())
    print(f"\nDone! Generated {total_comments} bilingual comments.")
    print(f"CSV ready for Infinite Campus: {output_path}")


if __name__ == "__main__":
    main()
