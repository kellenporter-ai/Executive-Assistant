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

class ContextSaveRequest(BaseModel):
    file: str  # e.g. "me.md"
    content: str

class ResetRequest(BaseModel):
    scope: str  # "interview", "history", "preferences", "factory", "complete"

class FolderClearRequest(BaseModel):
    folder: str  # "temp", "assets", or "projects"

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
    """Check server and CLI status."""
    try:
        get_gemini_path()
        cli_available = True
    except RuntimeError:
        cli_available = False
    return {
        "ready": True,  # Server is always ready (it's running!)
        "cli_available": cli_available,
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

async def _delete_from_cli(session_id: str, index: str | None = None) -> bool:
    """Remove a session from the Gemini CLI's index.
    If index is not provided, looks it up via --list-sessions."""
    gemini = get_gemini_path()

    if not index:
        # Look up the index by listing sessions and matching the session_id
        proc = await asyncio.create_subprocess_exec(
            gemini, "--list-sessions",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE,
        )
        stdout, _ = await proc.communicate()
        for line in stdout.decode("utf-8").split("\n"):
            match = re.match(
                r"\s*(\d+)\.\s+.+?\s+\(.+?\)\s+\[([a-f0-9-]+)\]",
                line,
            )
            if match and match.group(2).strip() == session_id:
                index = match.group(1).strip()
                break

    if not index:
        return False

    proc = await asyncio.create_subprocess_exec(
        gemini, "--delete-session", index,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE,
    )
    await proc.communicate()
    return proc.returncode == 0


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
    """Archive a chat session by moving it to the 24h archive directory
    and removing it from the Gemini CLI's session index."""
    # Always remove from CLI index (looks up index if not provided)
    await _delete_from_cli(session_id, index)

    gemini_dir = os.path.expanduser("~/.gemini/tmp")
    short_id = session_id.split("-")[0]
    pattern = os.path.join(gemini_dir, "**", "chats", f"session-*{short_id}*.json")
    matches = glob.glob(pattern, recursive=True)

    if not matches:
        # CLI delete may have already removed the file
        return {"status": "ok", "archived": True, "cli_deleted": True}

    for match in matches:
        dest = os.path.join(ARCHIVE_DIR, os.path.basename(match))
        shutil.move(match, dest)

    return {"status": "ok", "archived": True}


@app.post("/api/sessions/{session_id}/archive")
async def permanent_archive_session(session_id: str):
    """Permanently archive a session (not auto-deleted after 24h).
    Also removes it from the Gemini CLI's session index."""
    # Remove from CLI index before moving files
    await _delete_from_cli(session_id)

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




# --- Setup / Onboarding ---

@app.get("/api/setup/status")
async def setup_status():
    """Check all dependencies and setup completion."""
    checks = {}

    # Check each dependency
    for name, cmds in [("node", ["node"]), ("npm", ["npm"]), ("git", ["git"]), ("python", ["python3", "python"]), ("gemini", ["gemini"])]:
        checks[name] = any(shutil.which(c) is not None for c in cmds)

    # Check Gemini auth - look for auth tokens or settings
    gemini_auth = False
    auth_dir = os.path.expanduser("~/.gemini")
    if os.path.isdir(auth_dir):
        # Check settings.json for account info
        settings_file = os.path.join(auth_dir, "settings.json")
        if os.path.isfile(settings_file):
            try:
                with open(settings_file, "r") as f:
                    s = json.load(f)
                    gemini_auth = bool(s.get("account") or s.get("selectedAuthType"))
            except Exception:
                pass
        # Fallback: check for any session files (indicates CLI has been used successfully)
        if not gemini_auth:
            tmp_dir = os.path.join(auth_dir, "tmp")
            if os.path.isdir(tmp_dir):
                for d in os.listdir(tmp_dir):
                    chats = os.path.join(tmp_dir, d, "chats")
                    if os.path.isdir(chats) and os.listdir(chats):
                        gemini_auth = True
                        break

    # Check context files - are they filled in or still templates?
    context_dir = os.path.join(WORKSPACE, "context")
    context_files = {}
    for fname in ["me.md", "work.md", "team.md", "current_priorities.md", "rules.md"]:
        fpath = os.path.join(context_dir, fname)
        filled = False
        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                content = f.read()
                # Consider it "filled" if it has content beyond just template comments
                lines = [l.strip() for l in content.split("\n")
                         if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("<!--")]
                filled = len(lines) > 3
        context_files[fname] = filled

    # Overall setup phase
    deps_ok = all(checks.values())
    auth_ok = gemini_auth
    context_ok = any(context_files.values())

    if not deps_ok:
        phase = "dependencies"
    elif not auth_ok:
        phase = "auth"
    elif not context_ok:
        phase = "interview"
    else:
        phase = "ready"

    return {
        "phase": phase,
        "dependencies": checks,
        "auth": auth_ok,
        "context": context_files,
    }


@app.post("/api/setup/save-context")
async def save_context(request: ContextSaveRequest):
    """Save content to a context file from the setup interview."""
    allowed = {"me.md", "work.md", "team.md", "current_priorities.md", "rules.md"}
    if request.file not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid context file: {request.file}")

    context_dir = os.path.join(WORKSPACE, "context")
    fpath = os.path.join(context_dir, request.file)

    # Security: ensure path stays within context dir
    resolved = Path(fpath).resolve()
    if not resolved.is_relative_to(Path(context_dir).resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    with open(str(resolved), "w", encoding="utf-8") as f:
        f.write(request.content)

    return {"status": "ok", "file": request.file}


@app.post("/api/setup/verify-auth")
async def verify_auth():
    """Verify Gemini CLI authentication by running a simple test command."""
    try:
        gemini = get_gemini_path()
    except RuntimeError:
        return {"authenticated": False, "error": "Gemini CLI not installed"}

    proc = await asyncio.create_subprocess_exec(
        gemini, "-p", "Say hello", "-o", "stream-json",
        "--approval-mode", "yolo",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8")
        # If we got any valid JSON events, auth works
        for line in output.split("\n"):
            try:
                event = json.loads(line.strip())
                if event.get("type") in ("init", "message", "result"):
                    return {"authenticated": True}
            except Exception:
                continue

        stderr_text = stderr.decode("utf-8")
        return {"authenticated": False, "error": stderr_text or "No valid response from CLI"}
    except asyncio.TimeoutError:
        proc.kill()
        return {"authenticated": False, "error": "Authentication check timed out"}


@app.get("/api/setup/context/{filename}")
async def get_context(filename: str):
    """Read a context file for the profile editor."""
    allowed = {"me.md", "work.md", "team.md", "current_priorities.md", "rules.md"}
    if filename not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid context file: {filename}")

    context_dir = os.path.join(WORKSPACE, "context")
    fpath = os.path.join(context_dir, filename)

    resolved = Path(fpath).resolve()
    if not resolved.is_relative_to(Path(context_dir).resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(str(resolved)):
        return {"content": "", "exists": False}

    with open(str(resolved), "r", encoding="utf-8") as f:
        return {"content": f.read(), "exists": True}


@app.post("/api/setup/reset")
async def reset(request: ResetRequest):
    """Reset various aspects of the assistant."""
    results = {}

    if request.scope in ("history", "factory", "complete"):
        # Archive all active sessions
        gemini = None
        try:
            gemini = get_gemini_path()
        except RuntimeError:
            pass

        if gemini:
            proc = await asyncio.create_subprocess_exec(
                gemini, "--list-sessions",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=WORKSPACE,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8")

            archived_count = 0
            for line in output.split("\n"):
                match = re.match(
                    r"\s*(\d+)\.\s+.+?\s+\(.+?\)\s+\[([a-f0-9-]+)\]",
                    line,
                )
                if match:
                    session_id = match.group(2).strip()
                    await _delete_from_cli(session_id, match.group(1).strip())
                    # Move session files to archive
                    gemini_dir = os.path.expanduser("~/.gemini/tmp")
                    short_id = session_id.split("-")[0]
                    pattern = os.path.join(gemini_dir, "**", "chats", f"session-*{short_id}*.json")
                    matches = glob.glob(pattern, recursive=True)
                    for m in matches:
                        dest = os.path.join(ARCHIVE_DIR, os.path.basename(m))
                        shutil.move(m, dest)
                    archived_count += 1

            results["history"] = {"archived": archived_count}
        else:
            results["history"] = {"archived": 0, "note": "Gemini CLI not available"}

    if request.scope in ("interview", "factory", "complete"):
        # Reset context files to templates
        context_dir = os.path.join(WORKSPACE, "context")
        templates = {
            "me.md": "# About Me\n\n## Role\n<!-- What is your primary role? -->\n\n## Name\n\n\n## Tech Comfort Level\n\n\n## Goals\n\n\n## Preferences\n<!-- Add personal workflow preferences as you discover them -->\n",
            "work.md": "# Work Environment\n\n## Student Devices\n<!-- What devices do your students use? -->\n\n## Teaching Tools\n<!-- Key tools and platforms you use -->\n\n## Constraints\n<!-- Any limitations? -->\n\n## Deployment\n<!-- Updated as you configure integrations -->\n",
            "team.md": "# Team\n\n## Collaborators\n<!-- People you work with -->\n\n## Other Users\n<!-- Who else might use this assistant? -->\n",
            "current_priorities.md": "# Current Priorities & Goals\n\n## Priority 1\n<!-- What are you working on right now? -->\n\n## Automation Goals\n<!-- What takes up the most time that you'd like to automate? -->\n",
            "rules.md": "# Communication & Operating Rules\n\n## Communication Style\n- **Tone:** Casual\n- **Format:** Concise\n- **Decision-making:** Present options for me to choose from\n\n## Hard Rules\n- Never modify files outside the user's home directory\n- Once a task has been agreed upon, execute without asking for further permissions\n- Never commit secrets, API keys, or credentials to version control\n",
        }
        for fname, template in templates.items():
            fpath = os.path.join(context_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(template)
        results["context"] = {"reset": True, "files": list(templates.keys())}

    if request.scope in ("factory", "complete"):
        # Also reset token usage
        _save_token_usage({"sessions": {}, "total": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}})
        results["tokens"] = {"reset": True}

        # Clear memory files
        memory_dir = os.path.join(WORKSPACE, "memory")
        if os.path.isdir(memory_dir):
            for f in os.listdir(memory_dir):
                if f.endswith(".md") and f != "MEMORY.md":
                    os.remove(os.path.join(memory_dir, f))
            # Reset MEMORY.md to empty index
            memfile = os.path.join(memory_dir, "MEMORY.md")
            if os.path.isfile(memfile):
                with open(memfile, "w") as f:
                    f.write("# Memory\n\n<!-- Memories will be stored here as you use the assistant -->\n")
        results["memory"] = {"reset": True}

    if request.scope == "complete":
        # Clear non-essential workspace folders
        for folder in ["temp", "assets", "projects"]:
            folder_path = os.path.join(WORKSPACE, folder)
            if os.path.isdir(folder_path):
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    except OSError:
                        pass

        # Recreate essential directories and re-save token usage (cleared by folder wipe)
        os.makedirs(os.path.join(WORKSPACE, "temp", "archived_sessions"), exist_ok=True)
        os.makedirs(os.path.join(WORKSPACE, "temp", "permanent_archives"), exist_ok=True)
        os.makedirs(os.path.join(WORKSPACE, "temp", "attachments"), exist_ok=True)
        _save_token_usage({"sessions": {}, "total": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}})

        results["folders"] = {"cleared": ["temp", "assets", "projects"]}

    return {"status": "ok", "scope": request.scope, "results": results}


# --- Folder Management ---

@app.get("/api/folders/stats")
async def folder_stats():
    """Get file counts and sizes for cleanable folders."""
    folders = {
        "temp": os.path.join(WORKSPACE, "temp"),
        "assets": os.path.join(WORKSPACE, "assets"),
        "projects": os.path.join(WORKSPACE, "projects"),
    }
    stats = {}
    for name, path in folders.items():
        file_count = 0
        total_size = 0
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total_size += os.path.getsize(fp)
                        file_count += 1
                    except OSError:
                        pass
        stats[name] = {"files": file_count, "size": total_size, "path": path}
    return stats


@app.post("/api/folders/clear")
async def clear_folder(request: FolderClearRequest):
    """Clear contents of a workspace folder."""
    allowed = {"temp", "assets", "projects"}
    if request.folder not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid folder: {request.folder}")

    target = os.path.join(WORKSPACE, request.folder)
    if not os.path.isdir(target):
        return {"status": "ok", "deleted": 0}

    # Security: ensure path stays within workspace
    resolved = Path(target).resolve()
    if not resolved.is_relative_to(Path(WORKSPACE).resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    deleted = 0
    for item in os.listdir(target):
        item_path = os.path.join(target, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
            deleted += 1
        except OSError:
            pass

    return {"status": "ok", "folder": request.folder, "deleted": deleted}


@app.post("/api/shutdown")
async def shutdown():
    """Gracefully shut down the server."""
    import signal

    async def _delayed_shutdown():
        await asyncio.sleep(1.5)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(_delayed_shutdown())
    return {"status": "ok", "message": "Server shutting down..."}


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
