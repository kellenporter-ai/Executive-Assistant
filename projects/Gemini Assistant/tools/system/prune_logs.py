import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

LOG_FILE = Path("memory/operational_logs.jsonl")
ARCHIVE_DIR = Path("memory/archives")

def prune_logs(days_to_keep=7):
    """
    Moves logs older than N days to the archive directory.
    Keeps the main log file small for token efficiency.
    """
    if not LOG_FILE.exists():
        return {"status": "no logs to prune"}

    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
    
    to_keep = []
    to_archive = []

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                ts_str = entry["timestamp"].replace("Z", "")
                ts = datetime.fromisoformat(ts_str)
                
                if ts > cutoff:
                    to_keep.append(line)
                else:
                    to_archive.append(line)

        if not to_archive:
            return {"status": "nothing to archive", "kept": len(to_keep)}

        # Ensure archive dir exists
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_name = f"logs_{datetime.utcnow().strftime('%Y_%m')}.jsonl"
        archive_path = ARCHIVE_DIR / archive_name

        # Write to archive (append mode)
        with open(archive_path, "a", encoding="utf-8") as af:
            af.writelines(to_archive)

        # Rewrite main log with only recent entries
        with open(LOG_FILE, "w", encoding="utf-8") as lf:
            lf.writelines(to_keep)

        return {
            "status": "pruned",
            "archived_count": len(to_archive),
            "kept_count": len(to_keep),
            "archive_file": str(archive_path)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prune old operational logs.")
    parser.add_argument("--days", type=int, default=7, help="How many days of logs to keep")
    
    args = parser.parse_args()
    print(json.dumps(prune_logs(args.days), indent=2))
