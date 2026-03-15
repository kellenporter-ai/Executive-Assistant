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
    
    # Areas table (Long-term responsibilities)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Resources table (Knowledge, links, notes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT,
            notes TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            area_id INTEGER,
            description TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'completed', 'blocked')) DEFAULT 'pending',
            priority INTEGER DEFAULT 2, -- 1: High, 2: Med, 3: Low
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (area_id) REFERENCES areas(id)
        )
    ''')

    # Sessions table to track archived state
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT CHECK(status IN ('active', 'archived')) DEFAULT 'active',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def add_area(name, description):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO areas (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return {"status": "success", "message": f"Area '{name}' created."}
    except sqlite3.IntegrityError:
        return {"error": f"Area '{name}' already exists."}
    finally:
        conn.close()

def add_resource(title, link=None, notes=None, tags=None):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO resources (title, link, notes, tags) VALUES (?, ?, ?, ?)",
                     (title, link, notes, tags))
        conn.commit()
        return {"status": "success", "message": f"Resource '{title}' added."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def add_task(description, project_name=None, area_name=None, priority=2):
    conn = get_connection()
    try:
        project_id = None
        if project_name:
            project = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
            if project: project_id = project['id']
            
        area_id = None
        if area_name:
            area = conn.execute("SELECT id FROM areas WHERE name = ?", (area_name,)).fetchone()
            if area: area_id = area['id']
        
        conn.execute("INSERT INTO tasks (project_id, area_id, description, priority) VALUES (?, ?, ?, ?)",
                     (project_id, area_id, description, priority))
        conn.commit()
        return {"status": "success", "message": "Task added."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def archive_session(session_id):
    conn = get_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO sessions (session_id, status, updated_at) VALUES (?, 'archived', CURRENT_TIMESTAMP)", (session_id,))
        conn.commit()
        return {"status": "success", "message": f"Session '{session_id}' archived."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_archived_sessions():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT session_id FROM sessions WHERE status = 'archived'").fetchall()
        return [row['session_id'] for row in rows]
    finally:
        conn.close()

def query_state():
    conn = get_connection()
    try:
        projects = [dict(row) for row in conn.execute("SELECT * FROM projects WHERE status = 'active'").fetchall()]
        areas = [dict(row) for row in conn.execute("SELECT * FROM areas").fetchall()]
        resources = [dict(row) for row in conn.execute("SELECT * FROM resources ORDER BY created_at DESC LIMIT 10").fetchall()]
        tasks = [dict(row) for row in conn.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority ASC").fetchall()]
        return {
            "projects": projects,
            "areas": areas,
            "resources": resources,
            "active_tasks": tasks
        }
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

    # Add Area
    a_parser = subparsers.add_parser("add-area")
    a_parser.add_argument("--name", required=True)
    a_parser.add_argument("--desc")

    # Add Resource
    r_parser = subparsers.add_parser("add-resource")
    r_parser.add_argument("--title", required=True)
    r_parser.add_argument("--link")
    r_parser.add_argument("--notes")
    r_parser.add_argument("--tags")

    # Add Task
    t_parser = subparsers.add_parser("add-task")
    t_parser.add_argument("--desc", required=True)
    t_parser.add_argument("--project", help="Project name")
    t_parser.add_argument("--area", help="Area name")
    t_parser.add_argument("--priority", type=int, default=2)

    # Archive Session
    as_parser = subparsers.add_parser("archive-session")
    as_parser.add_argument("--id", required=True, help="Session ID to archive")

    # Query
    subparsers.add_parser("summary")


    args = parser.parse_args()

    if args.command == "init":
        print(json.dumps(init_db(), indent=2))
    elif args.command == "add-project":
        print(json.dumps(add_project(args.name, args.category, args.desc), indent=2))
    elif args.command == "add-area":
        print(json.dumps(add_area(args.name, args.desc), indent=2))
    elif args.command == "add-resource":
        print(json.dumps(add_resource(args.title, args.link, args.notes, args.tags), indent=2))
    elif args.command == "add-task":
        print(json.dumps(add_task(args.desc, args.project, args.area, args.priority), indent=2))
    elif args.command == "archive-session":
        print(json.dumps(archive_session(args.id), indent=2))
    elif args.command == "summary":
        print(json.dumps(query_state(), indent=2))
    else:
        parser.print_help()

