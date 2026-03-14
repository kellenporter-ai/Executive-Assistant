"""
Gemini Executive Assistant — CLI Proxy Server

Thin web server that pipes messages to the Gemini CLI and streams responses back.
No SDK, no API management — the CLI handles auth, tools, and agents natively.
"""

import os
import re
import json
import glob
import asyncio
import shutil
import uuid
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware
from gemini_client import stream_chat, get_gemini_path, WORKSPACE

# Lock to prevent race conditions on token usage file read-modify-write
token_lock = asyncio.Lock()

load_dotenv(os.path.join(WORKSPACE, ".env"))

# Attachments directory
ATTACHMENTS_DIR = os.path.join(WORKSPACE, "temp", "attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Archive directories
ARCHIVE_DIR = os.path.join(WORKSPACE, "temp", "archived_sessions")
PERMANENT_ARCHIVE_DIR = os.path.join(WORKSPACE, "temp", "permanent_archives")
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(PERMANENT_ARCHIVE_DIR, exist_ok=True)

# Active chat tasks tracking: { session_id: asyncio.Task }
active_tasks = {}

@asynccontextmanager
async def lifespan(app):
    cleanup_old_archives()
    yield

app = FastAPI(title="Gemini Executive Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    approval_mode: str | None = "yolo"
    model: str | None = None

class CancelRequest(BaseModel):
    session_id: str

# Token usage file (persisted across server restarts)
TOKEN_USAGE_FILE = os.path.join(WORKSPACE, "temp", "token_usage.json")

def _load_token_usage() -> dict:
    try:
        with open(TOKEN_USAGE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sessions": {}, "total": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}}

def _save_token_usage(data: dict):
    os.makedirs(os.path.dirname(TOKEN_USAGE_FILE), exist_ok=True)
    with open(TOKEN_USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- API Routes ---

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream a chat response from the Gemini CLI."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id

    async def event_stream():
        nonlocal session_id
        task = asyncio.current_task()

        # We'll use a temporary ID if one isn't provided yet
        track_id = session_id or f"temp-{uuid.uuid4().hex[:8]}"
        active_tasks[track_id] = task

        try:
            async for event in stream_chat(
                request.message,
                session_id,
                approval_mode=request.approval_mode or "yolo",
                model=request.model,
            ):
                # Update track_id if session_id is returned in the first event
                if event.get("type") == "init" and event.get("session_id"):
                    new_session_id = event["session_id"]
                    if track_id != new_session_id:
                        active_tasks[new_session_id] = task
                        active_tasks.pop(track_id, None)
                        track_id = new_session_id

                # Track token usage from result events
                if event.get("type") == "result" and event.get("stats"):
                    stats = event["stats"]
                    expected_fields = ("input_tokens", "output_tokens", "total_tokens")
                    if all(k in stats for k in expected_fields):
                        async with token_lock:
                            usage = _load_token_usage()
                            sid = track_id
                            if sid not in usage["sessions"]:
                                usage["sessions"][sid] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}
                            for key in expected_fields:
                                val = stats.get(key, 0)
                                usage["sessions"][sid][key] = usage["sessions"][sid].get(key, 0) + val
                                usage["total"][key] = usage["total"].get(key, 0) + val
                            usage["sessions"][sid]["requests"] = usage["sessions"][sid].get("requests", 0) + 1
                            usage["total"]["requests"] = usage["total"].get("requests", 0) + 1
                            _save_token_usage(usage)
                    else:
                        import sys
                        print(f"WARNING: stats present but missing expected fields {expected_fields}. Got: {list(stats.keys())}", file=sys.stderr)

                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Request cancelled by user'})}\n\n"
        finally:
            active_tasks.pop(track_id, None)

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/cancel")
async def cancel_chat(request: CancelRequest):
    """Cancel an active chat task."""
    task = active_tasks.get(request.session_id)
    if not task:
        return {"status": "not_found", "message": "No active task for this session"}
    
    task.cancel()
    return {"status": "cancelled"}


@app.get("/api/status")
async def status():
    """Check if the Gemini CLI is available."""
    try:
        get_gemini_path()
        cli_available = True
    except RuntimeError:
        cli_available = False
    return {
        "ready": cli_available,
        "workspace": WORKSPACE,
        "workspace_name": os.path.basename(WORKSPACE),
    }


# --- Token Usage ---

@app.get("/api/token-usage")
async def get_token_usage():
    """Return accumulated token usage stats."""
    return _load_token_usage()


@app.delete("/api/token-usage")
async def reset_token_usage():
    """Reset token usage tracking."""
    _save_token_usage({"sessions": {}, "total": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}})
    return {"status": "ok"}


# --- Session Management ---

@app.get("/api/sessions")
async def list_sessions():
    """List available chat sessions from the Gemini CLI."""
    gemini = get_gemini_path()
    proc = await asyncio.create_subprocess_exec(
        gemini, "--list-sessions",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8")

    sessions = []
    # Parse lines like:  1. prompt preview... (time ago) [session_id]
    for line in output.split("\n"):
        match = re.match(
            r"\s*(\d+)\.\s+(.+?)\s+\((.+?)\)\s+\[([a-f0-9-]+)\]",
            line,
        )
        if match:
            sessions.append({
                "index": match.group(1).strip(),
                "preview": match.group(2).strip(),
                "time_ago": match.group(3).strip(),
                "session_id": match.group(4).strip(),
            })
    return {"sessions": sessions}


@app.delete("/api/sessions/{session_id}")
async def archive_session(session_id: str, index: str | None = None):
    """Archive a chat session by moving it to the 24h archive directory.
    If an index is provided, also use the Gemini CLI to delete it from the active session list."""
    if index:
        gemini = get_gemini_path()
        await asyncio.create_subprocess_exec(
            gemini, "--delete-session", index,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE,
        )

    gemini_dir = os.path.expanduser("~/.gemini/tmp")
    short_id = session_id.split("-")[0]
    pattern = os.path.join(gemini_dir, "**", "chats", f"session-*{short_id}*.json")
    matches = glob.glob(pattern, recursive=True)

    if not matches:
        if index: # If CLI delete succeeded, we might not find the file anymore
             return {"status": "ok", "archived": True, "cli_deleted": True}
        raise HTTPException(status_code=404, detail="Session not found")

    for match in matches:
        dest = os.path.join(ARCHIVE_DIR, os.path.basename(match))
        shutil.move(match, dest)

    return {"status": "ok", "archived": True}


@app.post("/api/sessions/{session_id}/archive")
async def permanent_archive_session(session_id: str):
    """Permanently archive a session (not auto-deleted after 24h)."""
    gemini_dir = os.path.expanduser("~/.gemini/tmp")
    short_id = session_id.split("-")[0]
    pattern = os.path.join(gemini_dir, "**", "chats", f"session-*{short_id}*.json")
    matches = glob.glob(pattern, recursive=True)

    # Also check the 24h archive in case it was already archived
    archive_pattern = os.path.join(ARCHIVE_DIR, f"session-*{short_id}*.json")
    matches += glob.glob(archive_pattern)

    if not matches:
        raise HTTPException(status_code=404, detail="Session not found")

    for match in matches:
        dest = os.path.join(PERMANENT_ARCHIVE_DIR, os.path.basename(match))
        shutil.move(match, dest)

    return {"status": "ok", "permanent": True}


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Load message history from a saved Gemini CLI session."""
    # Session files are stored in ~/.gemini/tmp/<project>/chats/
    gemini_dir = os.path.expanduser("~/.gemini/tmp")
    short_id = session_id.split("-")[0]
    pattern = os.path.join(gemini_dir, "**", "chats", f"session-*{short_id}*.json")
    matches = glob.glob(pattern, recursive=True)

    if not matches:
        return {"messages": []}

    try:
        with open(matches[0], "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"messages": []}

    messages = []
    for m in data.get("messages", []):
        msg_type = m.get("type", "")
        content = m.get("content", "")

        # User messages have content as a list of parts
        if msg_type == "user":
            if isinstance(content, list):
                texts = [p.get("text", "") for p in content if isinstance(p, dict) and "text" in p]
                content = " ".join(texts)
            messages.append({"role": "user", "content": content})

        # Gemini (assistant) messages have content as a string
        elif msg_type == "gemini" and content:
            messages.append({"role": "assistant", "content": content})

    return {"messages": messages}


# --- File Browser ---

@app.get("/api/files")
async def list_files(path: str = ""):
    """List files and directories in the workspace."""
    target = Path(WORKSPACE).joinpath(path).resolve()
    # Security: ensure within workspace
    if not target.is_relative_to(Path(WORKSPACE).resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isdir(str(target)):
        raise HTTPException(status_code=404, detail="Directory not found")

    SKIP = {".git", ".venv", "__pycache__", "node_modules", ".gemini"}
    entries = []
    try:
        for name in sorted(os.listdir(str(target))):
            if name in SKIP or name.startswith("."):
                continue
            full = os.path.join(str(target), name)
            rel = os.path.relpath(full, WORKSPACE)
            is_dir = os.path.isdir(full)
            entries.append({
                "name": name,
                "path": rel,
                "is_dir": is_dir,
                "size": os.path.getsize(full) if not is_dir else None,
            })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"entries": entries, "path": os.path.relpath(target, WORKSPACE)}


@app.get("/api/files/search")
async def search_files(query: str):
    """Search for files in the workspace by name."""
    if not query.strip():
        return {"results": []}
    
    results = []
    # Search recursively, ignoring common noise directories
    SKIP = {".git", ".venv", "__pycache__", "node_modules", ".gemini"}
    
    for root, dirs, files in os.walk(WORKSPACE):
        # Filter directories in-place to avoid walking into skipped ones
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        
        for file in files:
            if query.lower() in file.lower():
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, WORKSPACE)
                results.append({
                    "name": file,
                    "path": rel_path,
                    "is_dir": False,
                    "size": os.path.getsize(full_path)
                })
                if len(results) >= 50: # Limit results for UI stability
                    break
        if len(results) >= 50:
            break
            
    return {"results": results}


@app.get("/api/files/read")
async def read_file(path: str):
    """Read a file from the workspace (text preview, max 50KB)."""
    target = Path(WORKSPACE).joinpath(path).resolve()
    if not target.is_relative_to(Path(WORKSPACE).resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(str(target)):
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.getsize(str(target)) > 50_000:
        return {"content": "(File too large to preview — over 50KB)", "truncated": True}

    try:
        with open(str(target), "r", encoding="utf-8", errors="replace") as f:
            return {"content": f.read(), "truncated": False}
    except Exception as e:
        return {"content": f"(Cannot read file: {e})", "truncated": True}


@app.get("/api/files/git-status")
async def git_status():
    """Get list of files with uncommitted changes in the workspace."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", "-u",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8")

        modified = []  # M, MM
        added = []     # A, ??
        deleted = []   # D

        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            status = line[:2].strip()
            filepath = line[3:].strip().strip('"')
            if status in ('M', 'MM', 'AM'):
                modified.append(filepath)
            elif status in ('??', 'A'):
                added.append(filepath)
            elif status == 'D':
                deleted.append(filepath)

        return {"modified": modified, "added": added, "deleted": deleted}
    except Exception:
        return {"modified": [], "added": [], "deleted": []}


# --- File Upload ---

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to temp/attachments/ for referencing in chat."""
    # Generate unique filename to avoid collisions
    ext = Path(file.filename).suffix if file.filename else ""
    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename or 'upload' + ext}"
    dest = os.path.join(ATTACHMENTS_DIR, unique_name)

    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    rel_path = os.path.relpath(dest, WORKSPACE)
    return {
        "filename": unique_name,
        "path": rel_path,
        "size": len(content),
    }


# --- Static Files ---

def cleanup_old_archives():
    """Delete archived sessions older than 24 hours."""
    if not os.path.isdir(ARCHIVE_DIR):
        return
    cutoff = time.time() - (24 * 60 * 60)
    for f in os.listdir(ARCHIVE_DIR):
        filepath = os.path.join(ARCHIVE_DIR, f)
        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)




static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    """Serve the chat UI."""
    return FileResponse(
        os.path.join(static_dir, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


# --- Entry Point ---

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("EA_PORT", "3131"))
    print(f"\n  Starting Gemini Executive Assistant on http://localhost:{port}")
    print(f"  Workspace: {WORKSPACE}")
    print(f"  Press Ctrl+C to stop\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
