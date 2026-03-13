"""
Gemini Executive Assistant — Local Web Server

Serves a chat UI on localhost and proxies messages to the Gemini API
with function calling for local file/shell operations.
"""

import os
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env from workspace root
workspace = str(Path(__file__).resolve().parent.parent)
load_dotenv(os.path.join(workspace, ".env"))

from gemini_client import GeminiChat


# --- State ---
chat_session: GeminiChat | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup."""
    global chat_session
    try:
        chat_session = GeminiChat()
        print(f"\n  Gemini EA ready — authenticated via {chat_session._auth_method}")
        print(f"  Model: {chat_session.model}")
        print(f"  Workspace: {workspace}\n")
    except Exception as e:
        print(f"\n  ⚠ Failed to initialize Gemini client: {e}")
        print(f"  Make sure you've run 'gemini auth login' or set GEMINI_API_KEY in .env\n")
    yield


app = FastAPI(title="Gemini Executive Assistant", lifespan=lifespan)


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] = []

class ConfigRequest(BaseModel):
    api_key: str | None = None
    model: str | None = None


# --- API Routes ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the EA and get a response."""
    if not chat_session:
        raise HTTPException(status_code=503, detail="Gemini client not initialized. Check authentication.")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await chat_session.send_message(request.message)
        return ChatResponse(
            response=result["response"],
            tool_calls=result["tool_calls"]
        )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg or "UNAUTHENTICATED" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed. Run 'gemini auth login' or check your API key."
            )
        raise HTTPException(status_code=500, detail=f"Gemini API error: {error_msg}")


@app.post("/api/clear")
async def clear_history():
    """Clear conversation history."""
    if chat_session:
        chat_session.clear_history()
    return {"status": "ok"}


@app.post("/api/reload")
async def reload_context():
    """Reload system prompt from GEMINI.md and context files."""
    if chat_session:
        chat_session.reload_system_prompt()
    return {"status": "ok", "message": "System prompt reloaded"}


@app.post("/api/configure")
async def configure(request: ConfigRequest):
    """Update configuration (API key, model)."""
    global chat_session
    try:
        api_key = request.api_key
        chat_session = GeminiChat(api_key=api_key)
        if request.model:
            chat_session.model = request.model
        return {"status": "ok", "model": chat_session.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")


@app.get("/api/status")
async def status():
    """Check if the EA is ready."""
    return {
        "ready": chat_session is not None,
        "model": chat_session.model if chat_session else None,
        "workspace": workspace,
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
    print(f"  Press Ctrl+C to stop\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
