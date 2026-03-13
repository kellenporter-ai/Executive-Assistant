"""
Gemini Executive Assistant — CLI Proxy Server

Thin web server that pipes messages to the Gemini CLI and streams responses back.
No SDK, no API management — the CLI handles auth, tools, and agents natively.
"""

import os
import re
import json
import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from gemini_client import stream_chat, get_gemini_path, WORKSPACE

load_dotenv(os.path.join(WORKSPACE, ".env"))

# Attachments directory
ATTACHMENTS_DIR = os.path.join(WORKSPACE, "temp", "attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


app = FastAPI(title="Gemini Executive Assistant")


# --- Request Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# --- API Routes ---

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream a chat response from the Gemini CLI."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id

    async def event_stream():
        async for event in stream_chat(request.message, session_id):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
    }


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
            r"\s*\d+\.\s+(.+?)\s+\((.+?)\)\s+\[([a-f0-9-]+)\]",
            line,
        )
        if match:
            sessions.append({
                "preview": match.group(1).strip(),
                "time_ago": match.group(2).strip(),
                "session_id": match.group(3).strip(),
            })
    return {"sessions": sessions}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    gemini = get_gemini_path()
    # Find the session index by listing sessions first
    proc = await asyncio.create_subprocess_exec(
        gemini, "--list-sessions",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8")

    session_index = None
    for line in output.split("\n"):
        match = re.match(
            r"\s*(\d+)\.\s+.+?\[([a-f0-9-]+)\]",
            line,
        )
        if match and match.group(2) == session_id:
            session_index = match.group(1)
            break

    if not session_index:
        raise HTTPException(status_code=404, detail="Session not found")

    proc = await asyncio.create_subprocess_exec(
        gemini, "--delete-session", session_index,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE,
    )
    await proc.communicate()
    return {"status": "ok"}


# --- File Browser ---

@app.get("/api/files")
async def list_files(path: str = ""):
    """List files and directories in the workspace."""
    target = os.path.normpath(os.path.join(WORKSPACE, path))
    # Security: ensure within workspace
    if not target.startswith(WORKSPACE):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Directory not found")

    SKIP = {".git", ".venv", "__pycache__", "node_modules", ".gemini"}
    entries = []
    try:
        for name in sorted(os.listdir(target)):
            if name in SKIP or name.startswith("."):
                continue
            full = os.path.join(target, name)
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


@app.get("/api/files/read")
async def read_file(path: str):
    """Read a file from the workspace (text preview, max 50KB)."""
    target = os.path.normpath(os.path.join(WORKSPACE, path))
    if not target.startswith(WORKSPACE):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.getsize(target) > 50_000:
        return {"content": "(File too large to preview — over 50KB)", "truncated": True}

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return {"content": f.read(), "truncated": False}
    except Exception as e:
        return {"content": f"(Cannot read file: {e})", "truncated": True}


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

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    """Serve the chat UI."""
    return FileResponse(os.path.join(static_dir, "index.html"))


# --- Entry Point ---

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("EA_PORT", "3131"))
    print(f"\n  Starting Gemini Executive Assistant on http://localhost:{port}")
    print(f"  Workspace: {WORKSPACE}")
    print(f"  Press Ctrl+C to stop\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
