import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path("memory/state.db")
OUTPUT_MD = Path("memory/STATE_SUMMARY.md")

def sync_to_md():
    """Reads SQLite state and exports a clean Markdown summary."""
    if not DB_PATH.exists():
        return {"error": "State database not found."}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        projects = conn.execute("SELECT * FROM projects WHERE status = 'active'").fetchall()
        tasks = conn.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority ASC").fetchall()
        conn.close()

        md_content = f"# System State Summary\n\n"
        md_content += f"Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"

        md_content += "## 📂 Active Projects (P.A.R.A)\n"
        if not projects:
            md_content += "*None*\n"
        else:
            for p in projects:
                md_content += f"- **{p['name']}** [{p['category']}]: {p['description']}\n"

        md_content += "\n## ✅ Pending Tasks\n"
        if not tasks:
            md_content += "*None*\n"
        else:
            # Group tasks by project
            p_map = {p['id']: p['name'] for p in projects}
            for t in tasks:
                p_name = p_map.get(t['project_id'], "No Project")
                priority = {1: "🔴 High", 2: "🟡 Med", 3: "🔵 Low"}.get(t['priority'], "🟡 Med")
                md_content += f"- [{priority}] **{p_name}**: {t['description']}\n"

        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {"status": "synced", "file": str(OUTPUT_MD)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    result = sync_to_md()
    print(json.dumps(result, indent=2))
