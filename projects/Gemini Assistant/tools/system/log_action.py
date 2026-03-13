import os
import sys
import json
import datetime
from pathlib import Path

LOG_FILE = Path("memory/operational_logs.jsonl")

def log_action(agent, action, status, details=None, category="Archive"):
    """
    Logs an agent action for auditability and state tracking.
    Categories: Projects, Areas, Resources, Archive (P.A.R.A)
    """
    # Ensure directory exists
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "session_id": os.environ.get("GEMINI_SESSION_ID"),
        "agent": agent,
        "action": action,
        "status": status,
        "category": category, # P.A.R.A classification
        "details": details or {}
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return {"status": "logged", "file": str(LOG_FILE)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Log an EA action.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--status", choices=["success", "failure", "pending"], default="success")
    parser.add_argument("--category", choices=["Projects", "Areas", "Resources", "Archive"], default="Archive")
    parser.add_argument("--details", help="JSON string of additional details")

    args = parser.parse_args()
    
    details = json.loads(args.details) if args.details else None
    result = log_action(args.agent, args.action, args.status, details, args.category)
    print(json.dumps(result, indent=2))
