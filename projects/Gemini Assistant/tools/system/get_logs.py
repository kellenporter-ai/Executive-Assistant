import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

LOG_FILE = Path("memory/operational_logs.jsonl")
DB_PATH = Path("memory/state.db")

def get_archived_sessions():
    """Returns a list of archived session IDs from the state database."""
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT session_id FROM sessions WHERE status = 'archived'").fetchall()
        conn.close()
        return [row['session_id'] for row in rows]
    except Exception:
        return []

def get_recent_logs(hours=24, session_id=None, show_all=False):
    """Retrieves and summarizes logs from the last N hours."""
    if not LOG_FILE.exists():
        return {"error": "No logs found."}

    # If no session_id provided, try to get it from environment
    if not session_id and not show_all:
        session_id = os.environ.get("GEMINI_SESSION_ID")

    archived_sessions = get_archived_sessions()
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    recent_entries = []

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                
                # Filter out archived sessions unless specifically requested
                if entry.get("session_id") in archived_sessions and not show_all:
                    continue

                # Parse timestamp: 2026-03-13T17:15:00Z -> remove Z for fromisoformat
                ts_str = entry["timestamp"].replace("Z", "")
                ts = datetime.fromisoformat(ts_str)
                
                if ts > cutoff:
                    if show_all or not session_id or entry.get("session_id") == session_id:
                        recent_entries.append(entry)
        
        return {
            "summary": {
                "session_id": session_id if not show_all else "all",
                "total_actions": len(recent_entries),
                "successes": len([e for e in recent_entries if e["status"] == "success"]),
                "failures": len([e for e in recent_entries if e["status"] == "failure"]),
            },
            "entries": recent_entries[-20:] # Return last 20 for context efficiency
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrieve recent operational logs.")
    parser.add_argument("--hours", type=int, default=24, help="How many hours back to look")
    parser.add_argument("--session_id", help="Filter by session ID")
    parser.add_argument("--all", action="store_true", help="Show all sessions")
    
    args = parser.parse_args()
    print(json.dumps(get_recent_logs(args.hours, args.session_id, args.all), indent=2))
