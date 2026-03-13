"""
Gemini Executive Assistant — CLI Proxy Server

Thin web server that pipes messages to the Gemini CLI and streams responses back.
No SDK, no API management — the CLI handles auth, tools, and agents natively.
"""

import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from gemini_client import stream_chat, get_gemini_path, WORKSPACE

load_dotenv(os.path.join(WORKSPACE, ".env"))


# --- State ---
current_session_id: str | None = None


app = FastAPI(title="Gemini Executive Assistant")


# --- Request Models ---

class ChatRequest(BaseModel):
    message: str


# --- API Routes ---

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream a chat response from the Gemini CLI."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def event_stream():
        global current_session_id
        async for event in stream_chat(request.message, current_session_id):
            # Capture session_id from init event for conversation continuity
            if event.get("type") == "init" and "session_id" in event:
                current_session_id = event["session_id"]
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/clear")
async def clear_chat():
    """Clear the current session (next message starts fresh)."""
    global current_session_id
    current_session_id = None
    return {"status": "ok"}


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
        "session_id": current_session_id,
        "workspace": WORKSPACE,
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
