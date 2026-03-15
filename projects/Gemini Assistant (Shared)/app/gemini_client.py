"""
Gemini CLI proxy — spawns the gemini CLI as a subprocess and streams NDJSON events.
No SDK, no API keys, no custom tools. The CLI handles everything.
"""

import asyncio
import json
import os
import shutil

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_gemini_path() -> str:
    """Find the gemini CLI binary."""
    path = shutil.which("gemini")
    if not path:
        raise RuntimeError(
            "Gemini CLI not found.\n"
            "Install with: npm install -g @google/gemini-cli\n"
            "Then authenticate with: gemini auth login"
        )
    return path


async def stream_chat(
    message: str,
    session_id: str | None = None,
    approval_mode: str = "yolo",
    model: str | None = None,
):
    """
    Spawn gemini CLI with -p and -o stream-json, yield parsed NDJSON events.

    Event types yielded:
      - init:        {type, session_id, model, timestamp}
      - message:     {type, role, content, delta?}
      - tool_use:    {type, tool_name, tool_id, parameters}
      - tool_result: {type, tool_id, status, output}
      - result:      {type, status, stats}

    If session_id is provided, resumes that session for multi-turn conversation.
    If model is provided, passes --model to select Gemini model variant.
    """
    gemini = get_gemini_path()

    # Only 'yolo' and 'plan' modes work in subprocess mode.
    # 'default' and 'auto_edit' require stdin for interactive approval prompts,
    # which aren't available when spawning gemini as a subprocess.
    effective_mode = approval_mode if approval_mode in ("yolo", "plan") else "yolo"
    cmd = [
        gemini,
        "-p", message,
        "-o", "stream-json",
        "--approval-mode", effective_mode,
    ]
    if model:
        cmd.extend(["--model", model])
    if session_id:
        cmd.extend(["--resume", session_id])

    # Pass session_id to tools via environment
    env = os.environ.copy()
    if session_id:
        env["GEMINI_SESSION_ID"] = session_id

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=WORKSPACE,
        env=env,
    )

    async for raw_line in proc.stdout:
        line = raw_line.decode("utf-8").strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            yield event
        except json.JSONDecodeError:
            # Non-JSON output from CLI (warnings, etc.) — skip
            continue

    # Wait for process to finish
    await proc.wait()

    # If the process failed, yield an error event
    if proc.returncode and proc.returncode != 0:
        stderr_output = ""
        if proc.stderr:
            stderr_bytes = await proc.stderr.read()
            stderr_output = stderr_bytes.decode("utf-8").strip()
        yield {
            "type": "error",
            "message": stderr_output or f"Gemini CLI exited with code {proc.returncode}",
        }
