import os
import sys
import subprocess
import json

def trigger_background_remember(session_id):
    """
    Spawns a background Gemini CLI process to run the 'remember' workflow
    for a specific session.
    """
    if not session_id:
        return {"status": "error", "message": "No session_id provided"}

    # Command to run the remember workflow autonomously
    # We use -p to provide the instruction and ensure it's non-interactive
    prompt = f"Run the 'remember' workflow for session {session_id}. Read the logs for this session, extract learnings, and save them to memory/ files. Do not ask for user confirmation. Report results to memory/background_remember_results.json."
    
    cmd = [
        "gemini",
        "-p", prompt,
        "--approval-mode", "yolo" # Ensure it doesn't wait for tool confirmations
    ]

    try:
        # Start the process and detach
        # We redirect stdout/stderr to a log file to avoid filling up the terminal
        log_file = open("memory/background_tasks.log", "a")
        subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True # Detach from parent
        )
        return {"status": "success", "message": f"Background remember triggered for session {session_id}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Trigger a background memory consolidation.")
    parser.add_argument("--session_id", required=True)
    
    args = parser.parse_args()
    result = trigger_background_remember(args.session_id)
    print(json.dumps(result, indent=2))
