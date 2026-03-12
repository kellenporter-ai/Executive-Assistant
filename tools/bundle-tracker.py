#!/usr/bin/env python3
"""
Bundle size tracker for Porter's Portal.

Tracks JS/CSS chunk sizes over time, compares to previous builds,
and checks against a gzipped budget.

Usage: python3 tools/bundle-tracker.py [--project PATH]

No external dependencies — stdlib only (Python 3.14).
"""

import argparse
import gzip
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EA_ROOT = SCRIPT_DIR.parent
DEFAULT_PROJECT = EA_ROOT / "projects" / "Porters-Portal"
HISTORY_FILE = EA_ROOT / "temp" / "bundle-history.json"
GZIP_BUDGET_KB = 250  # gzipped total budget in KB
CHUNK_GROWTH_THRESHOLD = 0.10  # 10% per-chunk warning
TOTAL_GROWTH_THRESHOLD = 0.05  # 5% total warning


def run_build(project_path: Path) -> bool:
    """Run npm run build in the project directory. Returns True on success."""
    print(f"Running npm run build in {project_path} ...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=project_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Build FAILED:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    print("Build succeeded.\n")
    return True


def scan_assets(project_path: Path) -> list[dict]:
    """Scan dist/assets/ for .js and .css files. Returns list of chunk info dicts."""
    assets_dir = project_path / "dist" / "assets"
    if not assets_dir.is_dir():
        print(f"ERROR: {assets_dir} not found after build.", file=sys.stderr)
        sys.exit(1)

    chunks = []
    for ext in ("*.js", "*.css"):
        for filepath in sorted(assets_dir.glob(ext)):
            raw_bytes = filepath.read_bytes()
            raw_size = len(raw_bytes)
            gz_size = len(gzip.compress(raw_bytes, compresslevel=6))
            chunks.append({
                "name": filepath.name,
                "size": raw_size,
                "gzip": gz_size,
            })
    return chunks


def load_history() -> list[dict]:
    """Load bundle history from JSON file."""
    if HISTORY_FILE.is_file():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history: list[dict]) -> None:
    """Save bundle history to JSON file."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def fmt_kb(size_bytes: int) -> str:
    """Format bytes as KB string."""
    return f"{size_bytes / 1024:.0f} KB"


def fmt_delta(current: int, previous: int) -> str:
    """Format a size delta as '+12 KB (+5.9%)'."""
    diff = current - previous
    if previous == 0:
        pct = 0.0
    else:
        pct = diff / previous * 100
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff / 1024:.0f} KB ({sign}{pct:.1f}%)"


def print_report(chunks: list[dict], previous_entry: dict | None, today: str) -> bool:
    """Print the bundle report. Returns True if budget passes."""
    total_raw = sum(c["size"] for c in chunks)
    total_gz = sum(c["gzip"] for c in chunks)

    print("=" * 40)
    print("  Bundle Size Report")
    print("=" * 40)
    print(f"Date: {today}\n")

    print("CHUNKS:")
    for c in chunks:
        print(f"  {c['name']:<45} {fmt_kb(c['size']):>8}  (gzipped: ~{fmt_kb(c['gzip'])})")

    print(f"\nTOTAL: {fmt_kb(total_raw)} (gzipped est: ~{fmt_kb(total_gz)})")

    # Compare to previous
    warnings = []
    if previous_entry:
        prev_date = previous_entry["date"]
        prev_chunks = {c["name"]: c for c in previous_entry["chunks"]}
        prev_total_raw = previous_entry["total_raw"]

        print(f"\nvs PREVIOUS ({prev_date}):")
        total_delta = fmt_delta(total_raw, prev_total_raw)
        total_pct = (total_raw - prev_total_raw) / prev_total_raw if prev_total_raw else 0
        ok = abs(total_pct) <= TOTAL_GROWTH_THRESHOLD
        marker = "\u2713" if ok else "\u26A0 OVER 5%"
        if not ok:
            warnings.append(f"Total grew {total_pct * 100:.1f}%")
        print(f"  Total: {total_delta}  {marker}")

        for c in chunks:
            if c["name"] in prev_chunks:
                pc = prev_chunks[c["name"]]
                delta = fmt_delta(c["size"], pc["size"])
                chunk_pct = (c["size"] - pc["size"]) / pc["size"] if pc["size"] else 0
                ok = abs(chunk_pct) <= CHUNK_GROWTH_THRESHOLD
                marker = "\u2713" if ok else "\u26A0 OVER 10%"
                if not ok:
                    warnings.append(f"{c['name']} grew {chunk_pct * 100:.1f}%")
                print(f"  {c['name']:<45} {delta}  {marker}")
            else:
                print(f"  {c['name']:<45} NEW")
    else:
        print("\n(No previous entry to compare against)")

    # Budget check
    budget_bytes = GZIP_BUDGET_KB * 1024
    passed = total_gz <= budget_bytes
    status = "PASS" if passed else "FAIL"
    print(f"\nBUDGET: {GZIP_BUDGET_KB} KB gzipped — {status}")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    return passed


def main():
    parser = argparse.ArgumentParser(description="Track Porter's Portal bundle size.")
    parser.add_argument(
        "--project",
        type=Path,
        default=DEFAULT_PROJECT,
        help="Path to the project directory",
    )
    args = parser.parse_args()

    project_path = args.project.resolve()
    if not (project_path / "package.json").is_file():
        print(f"ERROR: No package.json found in {project_path}", file=sys.stderr)
        sys.exit(1)

    if not run_build(project_path):
        sys.exit(1)

    chunks = scan_assets(project_path)
    if not chunks:
        print("No .js or .css files found in dist/assets/.", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_raw = sum(c["size"] for c in chunks)
    total_gz = sum(c["gzip"] for c in chunks)

    history = load_history()
    previous = history[-1] if history else None

    passed = print_report(chunks, previous, today)

    # Append to history
    entry = {
        "date": today,
        "total_raw": total_raw,
        "total_gzip": total_gz,
        "chunks": chunks,
    }
    history.append(entry)
    save_history(history)
    print(f"\nHistory saved to {HISTORY_FILE}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
