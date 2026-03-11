#!/usr/bin/env python3
"""
Student Progress Report — Firestore Data Extractor

Pulls student telemetry from Porter's Portal Firestore, aggregates per-student
metrics, and outputs JSON for comment generation by Claude Code (subscription
tokens). No API keys needed beyond the Firebase service account.

Usage:
  ./progress-reports.py                        # All classes, all students
  ./progress-reports.py --class "AP Physics"   # Filter by class
  ./progress-reports.py --section "Period 3"   # Filter by section/period
  ./progress-reports.py --output data.json     # Custom output path

Output: JSON file at temp/progress-data-YYYY-MM-DD.json
  → Feed this to Claude Code for bilingual comment generation + CSV export.

Prerequisites:
  1. tools/service-account.json (Firebase service account key)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

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
PROJECT_ID = "porters-portal"

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
    id_list = list(student_ids)
    for i in range(0, len(id_list), 30):
        batch = id_list[i:i+30]
        query = db.collection("submissions").where("userId", "in", batch)
        if class_filter:
            query = query.where("classType", "==", class_filter)
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            # Convert Firestore Timestamps to ISO strings for JSON serialization
            for key in ("submittedAt", "createdAt", "updatedAt"):
                if hasattr(data.get(key), "isoformat"):
                    data[key] = data[key].isoformat()
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
            existing = buckets.get(key)
            if existing is None:
                buckets[key] = data
            else:
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

        # Completion rate
        submitted_ids = set(s.get("assignmentId") for s in class_subs if s.get("status") != "STARTED")
        total_assignments = len(class_assignments)
        completion_rate = round(len(submitted_ids) / total_assignments * 100, 1) if total_assignments else 0
        completion_rate = min(completion_rate, 100.0)

        # Engagement metrics
        total_time = sum(s.get("metrics", {}).get("engagementTime", 0) for s in class_subs)
        total_keystrokes = sum(s.get("metrics", {}).get("keystrokes", 0) for s in class_subs)
        total_pastes = sum(s.get("metrics", {}).get("pasteCount", 0) for s in class_subs)
        submission_count = len([s for s in class_subs if s.get("status") != "STARTED"])

        # Rubric tier distribution
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

        # Alerts
        class_alerts = [a for a in alert_list if a.get("classType") == class_type]
        risk_level = None
        risk_reasons = []
        for alert in class_alerts:
            level = alert.get("riskLevel")
            if risk_level is None or {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}.get(level, 0) > \
                    {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}.get(risk_level, 0):
                risk_level = level
            risk_reasons.append(alert.get("reason", ""))

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
            "risk_reasons": list(set(r for r in risk_reasons if r)),
            "xp": class_xp,
            "level": level,
            "tier_distribution": {str(k): v for k, v in tier_counts.items()},
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
# OUTPUT
# =============================================================================

def print_summary(student_reports, class_filter=None):
    """Print a quick summary table to terminal."""
    print(f"\n{'='*80}")
    print(f"  STUDENT PROGRESS SUMMARY")
    print(f"{'='*80}")

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

        avg_score = sum(s[1]["avg_score"] for s in students) / len(students) if students else 0
        avg_comp = sum(s[1]["completion_rate"] for s in students) / len(students) if students else 0
        print(f"  {'─'*76}")
        print(f"  {'CLASS AVG':<25} {avg_score:>5.1f}% {avg_comp:>5.1f}%")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Student Progress Report — Firestore Data Extractor")
    parser.add_argument("--class", "-c", dest="class_filter", help="Filter by class (e.g., 'AP Physics')")
    parser.add_argument("--section", "-s", help="Filter by section/period (e.g., 'Period 3')")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path (default: temp/progress-data-YYYY-MM-DD.json)")
    args = parser.parse_args()

    # Output path
    if args.output:
        output_path = args.output
    else:
        os.makedirs(os.path.join(os.path.dirname(SCRIPT_DIR), "temp"), exist_ok=True)
        output_path = os.path.join(
            os.path.dirname(SCRIPT_DIR), "temp",
            f"progress-data-{datetime.now().strftime('%Y-%m-%d')}.json"
        )

    # Init Firestore
    print("Connecting to Firestore...")
    db = init_firestore()

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

    # Write JSON
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "filters": {
            "class": args.class_filter,
            "section": args.section,
        },
        "summary": {
            "total_students": len(student_reports),
            "total_submissions": total_subs,
            "total_assignments": len(assignments),
            "total_alerts": total_alerts,
        },
        "students": student_reports,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nData written to: {output_path}")
    print(f"Next step: feed this JSON to Claude Code for bilingual comment generation + CSV export.")


if __name__ == "__main__":
    main()
