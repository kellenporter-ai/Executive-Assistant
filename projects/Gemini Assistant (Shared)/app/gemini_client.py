"""
Gemini CLI proxy — spawns the gemini CLI as a subprocess and streams NDJSON events.
No SDK, no API keys, no custom tools. The CLI handles everything.

Model auto-fallback: When a model hits capacity (429) or times out, automatically
scales down to the next tier and retries. Tracks cooldowns so subsequent requests
skip exhausted models.
"""

import asyncio
import json
import os
import shutil
import time

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_STATUS_FILE = os.path.join(WORKSPACE, ".gemini-model-status.json")

# Model tier list — highest capability first
MODEL_TIERS = [
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]

# Default cooldown: 15 minutes before retrying an exhausted model
DEFAULT_COOLDOWN_S = 15 * 60


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


def _load_model_status() -> dict:
    """Load model availability status from disk."""
    if os.path.exists(MODEL_STATUS_FILE):
        try:
            with open(MODEL_STATUS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_model_status(status: dict):
    """Persist model availability status to disk."""
    try:
        with open(MODEL_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except IOError:
        pass


def _mark_model_exhausted(model: str, status: dict) -> dict:
    """Mark a model as exhausted with a retry-after timestamp."""
    retry_after = time.time() + DEFAULT_COOLDOWN_S
    status[model] = {
        "exhausted_at": time.time(),
        "retry_after": retry_after,
        "retry_after_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(retry_after)),
    }
    _save_model_status(status)
    return status


def _get_best_available_model(status: dict) -> tuple[str, list[str]]:
    """
    Return the highest-tier model that isn't currently exhausted,
    plus a list of skipped models and their retry times.
    """
    now = time.time()
    skipped = []

    for model in MODEL_TIERS:
        info = status.get(model)
        if info and now < info.get("retry_after", 0):
            retry_iso = info.get("retry_after_iso", "unknown")
            skipped.append(f"{model} (available after {retry_iso})")
            continue
        # Available — clear stale exhaustion if cooldown passed
        if model in status:
            del status[model]
            _save_model_status(status)
        return model, skipped

    # All models exhausted — return the one with the soonest retry
    soonest = min(MODEL_TIERS, key=lambda m: status.get(m, {}).get("retry_after", float("inf")))
    return soonest, skipped


def _is_capacity_error(text: str) -> bool:
    """Detect if text contains a model capacity exhaustion error."""
    return (
        "MODEL_CAPACITY_EXHAUSTED" in text
        or "No capacity available" in text
        or ("429" in text and "rateLimitExceeded" in text)
    )


def get_model_status() -> dict:
    """Return current model availability status for API consumers."""
    status = _load_model_status()
    now = time.time()
    result = {}
    for model in MODEL_TIERS:
        info = status.get(model)
        if info and now < info.get("retry_after", 0):
            result[model] = {
                "available": False,
                "retry_after": info["retry_after_iso"],
                "seconds_remaining": round(info["retry_after"] - now),
            }
        else:
            result[model] = {"available": True}
    return result


async def stream_chat(
    message: str,
    session_id: str | None = None,
    approval_mode: str = "yolo",
    model: str | None = None,
):
    """
    Spawn gemini CLI with -p and -o stream-json, yield parsed NDJSON events.

    If no model is specified, uses the highest available model from the tier list.
    On capacity errors (429) or process failures, automatically retries with the
    next tier down and yields a fallback notification event.

    Event types yielded:
      - init:        {type, session_id, model, timestamp}
      - message:     {type, role, content, delta?}
      - tool_use:    {type, tool_name, tool_id, parameters}
      - tool_result: {type, tool_id, status, output}
      - result:      {type, status, stats}
      - model_fallback: {type, from_model, to_model, reason, skipped}
      - error:       {type, message}

    If session_id is provided, resumes that session for multi-turn conversation.
    """
    gemini = get_gemini_path()
    status = _load_model_status()
    explicit_model = model is not None

    # Only 'yolo' and 'plan' modes work in subprocess mode.
    effective_mode = approval_mode if approval_mode in ("yolo", "plan") else "yolo"

    # Determine starting model
    if not explicit_model:
        model, skipped = _get_best_available_model(status)
    else:
        skipped = []

    while True:
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

        # Collect all events and check for capacity errors
        events = []
        got_content = False

        async for raw_line in proc.stdout:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
                if event.get("type") == "message" and event.get("content"):
                    got_content = True
            except json.JSONDecodeError:
                continue

        await proc.wait()

        # Read stderr for capacity errors
        stderr_output = ""
        if proc.stderr:
            stderr_bytes = await proc.stderr.read()
            stderr_output = stderr_bytes.decode("utf-8").strip()

        # Check if this was a capacity error
        all_text = stderr_output + " ".join(
            json.dumps(e) for e in events if e.get("type") == "error"
        )
        is_capacity = _is_capacity_error(all_text)
        is_failure = (proc.returncode and proc.returncode != 0) and not got_content

        if (is_capacity or is_failure) and not explicit_model:
            # Mark this model as exhausted and try the next one
            reason = "capacity_exhausted" if is_capacity else "process_failure"
            status = _mark_model_exhausted(model, status)
            next_model, next_skipped = _get_best_available_model(status)

            if next_model != model:
                # Notify the consumer about the fallback
                yield {
                    "type": "model_fallback",
                    "from_model": model,
                    "to_model": next_model,
                    "reason": reason,
                    "skipped": next_skipped,
                    "retry_after": status[model].get("retry_after_iso"),
                }
                model = next_model
                continue
            # else: all models exhausted, fall through to yield what we have

        # No capacity error (or explicit model) — yield all collected events
        for event in events:
            yield event

        # If the process failed, yield an error event
        if proc.returncode and proc.returncode != 0 and not got_content:
            error_msg = stderr_output or f"Gemini CLI exited with code {proc.returncode}"
            if is_capacity:
                retry_info = status.get(model, {})
                error_msg = (
                    f"{model} capacity exhausted. "
                    f"Retry after {retry_info.get('retry_after_iso', 'unknown')}."
                )
            yield {
                "type": "error",
                "message": error_msg,
            }

        # Done — break the retry loop
        break
