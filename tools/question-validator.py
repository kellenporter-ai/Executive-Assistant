#!/usr/bin/env python3
"""Validate question bank JSON files.

Usage: python3 question-validator.py <path-to-question-bank.json>

Checks for missing fields, answer index bounds, duplicate stems,
MC length bias, empty options, and reports tier/type distributions.

Exit code 0 if no critical/high issues, 1 otherwise.
No external dependencies — stdlib only.
"""

import json
import re
import string
import sys
from collections import Counter
from itertools import combinations


def normalize(text: str) -> set[str]:
    """Lowercase, strip punctuation, return set of words."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return set(text.split())


def word_overlap(a: set[str], b: set[str]) -> float:
    """Fraction of overlapping words relative to the larger set."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / max(len(a), len(b))


REQUIRED_FIELDS = {"id", "stem", "options", "correctAnswer", "tier", "type"}


def validate(questions: list[dict]) -> tuple[list[tuple[str, str]], Counter, Counter]:
    """Return (issues, tier_counts, type_counts)."""
    issues: list[tuple[str, str]] = []  # (severity, message)
    tier_counts: Counter = Counter()
    type_counts: Counter = Counter()

    # For duplicate detection: collect (id, normalized stem words)
    stem_index: list[tuple[str, set[str]]] = []
    # For MC length bias
    longest_is_correct = 0
    single_answer_count = 0

    for q in questions:
        qid = q.get("id", "UNKNOWN")

        # --- Missing fields ---
        missing = REQUIRED_FIELDS - set(q.keys())
        if missing:
            issues.append(("CRITICAL", f"Q-{qid}: missing fields: {', '.join(sorted(missing))}"))
            # Can't do further checks if core fields are missing
            if "options" in missing or "correctAnswer" in missing:
                continue

        options = q.get("options", [])
        correct = q.get("correctAnswer")
        tier = q.get("tier")
        qtype = q.get("type")
        stem = q.get("stem", "")

        if tier is not None:
            tier_counts[tier] += 1
        if qtype is not None:
            type_counts[qtype] += 1

        # --- Options must be a list ---
        if not isinstance(options, list):
            issues.append(("CRITICAL", f"Q-{qid}: options is not an array"))
            continue

        # --- Collect valid option ids ---
        option_ids = set()
        for i, opt in enumerate(options):
            if isinstance(opt, dict):
                oid = opt.get("id")
                text = opt.get("text", "")
                if oid is not None:
                    option_ids.add(oid)
                # Empty/blank option text
                if isinstance(text, str) and text.strip() == "":
                    issues.append(("LOW", f"Q-{qid}: Option {oid or i} is empty"))
            elif isinstance(opt, str):
                option_ids.add(str(i))
                if opt.strip() == "":
                    issues.append(("LOW", f"Q-{qid}: Option index {i} is empty"))

        # --- Answer index bounds ---
        if isinstance(correct, str):
            if correct not in option_ids:
                issues.append(("CRITICAL", f"Q-{qid}: correctAnswer '{correct}' not in option ids {sorted(option_ids)}"))
        elif isinstance(correct, list):
            for ans in correct:
                if ans not in option_ids:
                    issues.append(("CRITICAL", f"Q-{qid}: correctAnswer element '{ans}' not in option ids {sorted(option_ids)}"))
        elif isinstance(correct, int):
            if correct < 0 or correct >= len(options):
                issues.append(("CRITICAL", f"Q-{qid}: correctAnswer index {correct} out of bounds (only {len(options)} options)"))

        # --- MC length bias (single-answer string questions only) ---
        if isinstance(correct, str) and options:
            single_answer_count += 1
            # Find the option text for the correct answer and check if it's the longest
            option_texts = {}
            for opt in options:
                if isinstance(opt, dict):
                    option_texts[opt.get("id")] = len(opt.get("text", ""))
                elif isinstance(opt, str):
                    pass  # skip non-dict options for length check
            if option_texts and correct in option_texts:
                max_len = max(option_texts.values())
                if option_texts[correct] == max_len:
                    # Check it's strictly longest (not tied)
                    count_at_max = sum(1 for v in option_texts.values() if v == max_len)
                    if count_at_max == 1:
                        longest_is_correct += 1

        # --- Collect for duplicate detection ---
        if stem:
            stem_index.append((qid, normalize(stem)))

    # --- MC length bias report ---
    if single_answer_count > 0:
        bias_pct = (longest_is_correct / single_answer_count) * 100
        if bias_pct > 30:
            issues.append(("HIGH", f"MC length bias: {bias_pct:.1f}% of single-answer questions have longest correct answer (threshold: 30%)"))

    # --- Duplicate detection ---
    # Only check if reasonable number of questions (O(n^2) but with early skip)
    if len(stem_index) <= 5000:
        for (id_a, words_a), (id_b, words_b) in combinations(stem_index, 2):
            overlap = word_overlap(words_a, words_b)
            if overlap > 0.90:
                issues.append(("MEDIUM", f"Potential duplicates: Q-{id_a} and Q-{id_b} ({overlap:.0%} word overlap)"))

    return issues, tier_counts, type_counts


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 question-validator.py <path-to-question-bank.json>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, list):
        print(f"Error: expected top-level JSON array, got {type(data).__name__}", file=sys.stderr)
        sys.exit(2)

    issues, tier_counts, type_counts = validate(data)

    # Sort issues by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    issues.sort(key=lambda x: severity_order.get(x[0], 99))

    # Count by severity
    sev_counts = Counter(sev for sev, _ in issues)

    print("=== Question Bank Validation Report ===")
    print(f"File: {filepath}")
    print(f"Total questions: {len(data)}")
    print()

    print("TIER DISTRIBUTION:")
    for tier in sorted(tier_counts.keys()):
        print(f"  Tier {tier}: {tier_counts[tier]}")
    print()

    print("TYPE DISTRIBUTION:")
    for qtype in sorted(type_counts.keys()):
        print(f"  {qtype}: {type_counts[qtype]}")
    print()

    print(f"ISSUES FOUND: {len(issues)}")
    for severity, msg in issues:
        print(f"  [{severity}] {msg}")
    print()

    crit = sev_counts.get("CRITICAL", 0)
    high = sev_counts.get("HIGH", 0)
    med = sev_counts.get("MEDIUM", 0)
    low = sev_counts.get("LOW", 0)
    print(f"SUMMARY: {crit} critical, {high} high, {med} medium, {low} low")

    if crit > 0 or high > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
