import sqlite3
import json
import sys
import argparse
import datetime
from pathlib import Path

DB_PATH = Path("memory/state.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Projects table (P.A.R.A)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT CHECK(category IN ('Projects', 'Areas', 'Resources', 'Archive')) DEFAULT 'Projects',
            status TEXT DEFAULT 'active',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            description TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'completed', 'blocked')) DEFAULT 'pending',
            priority INTEGER DEFAULT 2, -- 1: High, 2: Med, 3: Low
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    # Key-Value state for ephemeral data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kv_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    return {"status": "initialized", "db": str(DB_PATH)}

def add_project(name, category, description):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO projects (name, category, description) VALUES (?, ?, ?)",
                     (name, category, description))
        conn.commit()
        return {"status": "success", "message": f"Project '{name}' created."}
    except sqlite3.IntegrityError:
        return {"error": f"Project '{name}' already exists."}
    finally:
        conn.close()

def add_task(project_name, description, priority=2):
    conn = get_connection()
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
        project_id = project['id'] if project else None
        
        conn.execute("INSERT INTO tasks (project_id, description, priority) VALUES (?, ?, ?)",
                     (project_id, description, priority))
        conn.commit()
        return {"status": "success", "message": "Task added."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def query_state():
    conn = get_connection()
    try:
        projects = [dict(row) for row in conn.execute("SELECT * FROM projects WHERE status = 'active'").fetchall()]
        tasks = [dict(row) for row in conn.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority ASC").fetchall()]
        return {"projects": projects, "active_tasks": tasks}
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="State Management Tool (SQLite)")
    subparsers = parser.add_subparsers(dest="command")

    # Init
    subparsers.add_parser("init")

    # Add Project
    p_parser = subparsers.add_parser("add-project")
    p_parser.add_argument("--name", required=True)
    p_parser.add_argument("--category", choices=['Projects', 'Areas', 'Resources', 'Archive'], default='Projects')
    p_parser.add_argument("--desc")

    # Add Task
    t_parser = subparsers.add_parser("add-task")
    t_parser.add_argument("--project", help="Project name")
    t_parser.add_argument("--desc", required=True)
    t_parser.add_argument("--priority", type=int, default=2)

    # Query
    subparsers.add_parser("summary")

    args = parser.parse_args()

    if args.command == "init":
        print(json.dumps(init_db(), indent=2))
    elif args.command == "add-project":
        print(json.dumps(add_project(args.name, args.category, args.desc), indent=2))
    elif args.command == "add-task":
        print(json.dumps(add_task(args.project, args.desc, args.priority), indent=2))
    elif args.command == "summary":
        print(json.dumps(query_state(), indent=2))
    else:
        parser.print_help()
