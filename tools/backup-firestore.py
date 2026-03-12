#!/usr/bin/env python3
"""
Firestore collection backup tool.

Exports key collections to JSON files for local backup/recovery.

Usage:
  python3 tools/backup-firestore.py [--collections users,submissions] [--output DIR]

Requires firebase-admin (available in tools/.venv/).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EA_ROOT = SCRIPT_DIR.parent
SERVICE_ACCOUNT = SCRIPT_DIR / "service-account.json"
DEFAULT_OUTPUT = EA_ROOT / "temp" / "backups" / datetime.now(timezone.utc).strftime("%Y-%m-%d")
DEFAULT_COLLECTIONS = [
    "users",
    "submissions",
    "assignments",
    "lesson_block_responses",
    "assessment_sessions",
]
PAGE_SIZE = 500


def init_firestore():
    """Initialize and return a Firestore client."""
    if not SERVICE_ACCOUNT.is_file():
        print(f"ERROR: Service account not found at {SERVICE_ACCOUNT}", file=sys.stderr)
        print("Place your Firebase service account JSON there or check the path.", file=sys.stderr)
        sys.exit(1)

    import firebase_admin
    from firebase_admin import credentials, firestore

    # Avoid re-initializing if already done
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SERVICE_ACCOUNT))
        firebase_admin.initialize_app(cred)

    return firestore.client()


def serialize_doc(doc) -> dict:
    """Convert a Firestore document to a JSON-safe dict."""
    data = doc.to_dict()
    if data is None:
        data = {}
    data["_id"] = doc.id
    return _make_serializable(data)


def _make_serializable(obj):
    """Recursively convert Firestore types to JSON-safe Python types."""
    from google.cloud.firestore_v1 import DocumentReference, GeoPoint

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, DocumentReference):
        return obj.path
    if isinstance(obj, GeoPoint):
        return {"lat": obj.latitude, "lng": obj.longitude}
    # Handle Firestore Timestamp and DatetimeWithNanoseconds
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    # Fallback
    return str(obj)


def export_collection(db, collection_name: str) -> list[dict]:
    """Export all docs from a collection using paginated queries."""
    docs = []
    query = db.collection(collection_name).order_by("__name__").limit(PAGE_SIZE)

    while True:
        page = list(query.stream())
        if not page:
            break

        for doc in page:
            docs.append(serialize_doc(doc))

        # Cursor for next page
        if len(page) < PAGE_SIZE:
            break
        query = (
            db.collection(collection_name)
            .order_by("__name__")
            .start_after(page[-1])
            .limit(PAGE_SIZE)
        )

    return docs


def fmt_size(size_bytes: int) -> str:
    """Format bytes for display."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(description="Back up Firestore collections to JSON.")
    parser.add_argument(
        "--collections",
        type=str,
        default=None,
        help="Comma-separated list of collections to export",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: temp/backups/YYYY-MM-DD/)",
    )
    args = parser.parse_args()

    collections = (
        [c.strip() for c in args.collections.split(",") if c.strip()]
        if args.collections
        else DEFAULT_COLLECTIONS
    )
    output_dir = (args.output or DEFAULT_OUTPUT).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing Firestore...")
    db = init_firestore()

    total_size = 0
    print(f"\nBacking up {len(collections)} collections to {output_dir}\n")
    print(f"{'Collection':<30} {'Docs':>8} {'Size':>10}")
    print("-" * 52)

    for coll_name in collections:
        docs = export_collection(db, coll_name)
        out_path = output_dir / f"{coll_name}.json"
        with open(out_path, "w") as f:
            json.dump(docs, f, indent=2, ensure_ascii=False)

        file_size = out_path.stat().st_size
        total_size += file_size
        print(f"{coll_name:<30} {len(docs):>8} {fmt_size(file_size):>10}")

    print("-" * 52)
    print(f"{'TOTAL':<30} {'':>8} {fmt_size(total_size):>10}")
    print(f"\nBackup complete: {output_dir}")


if __name__ == "__main__":
    main()
