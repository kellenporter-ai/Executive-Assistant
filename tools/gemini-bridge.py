#!/usr/bin/env python3
"""
Gemini Bridge — invokes the Gemini CLI as a subprocess and returns structured output.

The Gemini CLI has full file access (read, write, edit, grep, bash) when run
in its workspace directory. This bridge just invokes it and captures output —
Gemini handles everything else autonomously in yolo mode (no permission prompts).

Model fallback: Automatically scales down when a model hits capacity limits (429).
Tracks cooldown times and retries higher models when they become available.

Usage:
  ./gemini-bridge.py "Audit this code for security issues"
  ./gemini-bridge.py --agent qa-engineer "Review the auth module"
  ./gemini-bridge.py --model gemini-2.5-pro --timeout 180 "Complex task here"
  ./gemini-bridge.py --session-id abc123 "Follow-up question"
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

EA_ROOT = "/home/kp/Desktop/Executive Assistant"
GEMINI_WORKSPACE = os.path.join(EA_ROOT, "projects", "Gemini Assistant")
DEFAULT_TIMEOUT = 120
MODEL_STATUS_FILE = os.path.join(EA_ROOT, "tools", ".gemini-model-status.json")

# Model tier list — highest capability first. Bridge tries in order.
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
        print(json.dumps({
            "status": "error",
            "content": "Gemini CLI not found. Install with: npm install -g @google/gemini-cli",
            "tools_used": [],
            "model": None,
            "session_id": None,
        }))
        sys.exit(1)
    return path


def load_model_status() -> dict:
    """Load model availability status from disk."""
    if os.path.exists(MODEL_STATUS_FILE):
        try:
            with open(MODEL_STATUS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_model_status(status: dict):
    """Persist model availability status to disk."""
    try:
        with open(MODEL_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except IOError:
        pass


def mark_model_exhausted(model: str, status: dict) -> dict:
    """Mark a model as exhausted with a retry-after timestamp."""
    retry_after = time.time() + DEFAULT_COOLDOWN_S
    status[model] = {
        "exhausted_at": time.time(),
        "retry_after": retry_after,
        "retry_after_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(retry_after)),
    }
    save_model_status(status)
    return status


def get_best_available_model(status: dict) -> tuple[str, list[str]]:
    """
    Return the highest-tier model that isn't currently exhausted,
    plus a list of skipped models and their retry times.
    """
    now = time.time()
    skipped = []

    for model in MODEL_TIERS:
        info = status.get(model)
        if info and now < info.get("retry_after", 0):
            # Still in cooldown
            retry_iso = info.get("retry_after_iso", "unknown")
            skipped.append(f"{model} (available after {retry_iso})")
            continue
        # Available — clear stale exhaustion if cooldown passed
        if model in status:
            del status[model]
            save_model_status(status)
        return model, skipped

    # All models exhausted — return the one with the soonest retry
    soonest = min(MODEL_TIERS, key=lambda m: status.get(m, {}).get("retry_after", float("inf")))
    return soonest, skipped


def is_capacity_error(stderr: str, stdout: str) -> bool:
    """Detect if the error is a model capacity exhaustion (429)."""
    combined = (stderr or "") + (stdout or "")
    return (
        "MODEL_CAPACITY_EXHAUSTED" in combined
        or "No capacity available" in combined
        or ("429" in combined and "rateLimitExceeded" in combined)
    )


def build_prompt(prompt: str, agent: str | None = None) -> str:
    """Wrap the prompt with agent delegation if targeting a specific Gemini agent."""
    if agent:
        return (
            f"Delegate this task to the {agent} agent. "
            f"Use the {agent} agent's full capabilities. "
            f"Here is the task:\n\n{prompt}"
        )
    return prompt


def run_gemini(
    prompt: str,
    agent: str | None = None,
    model: str | None = None,
    session_id: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    workspace: str | None = None,
) -> dict:
    """
    Run the Gemini CLI synchronously and return structured output.

    If no model is specified, uses the highest available model from the tier list.
    On capacity errors (429), automatically retries with the next tier down.
    """
    gemini = get_gemini_path()
    full_prompt = build_prompt(prompt, agent)
    status = load_model_status()
    cwd = workspace or GEMINI_WORKSPACE

    # Determine which model to use
    explicit_model = model is not None
    if not explicit_model:
        model, skipped_models = get_best_available_model(status)
    else:
        skipped_models = []

    # Try the model, falling back on capacity errors
    attempts = []
    while True:
        attempts.append(model)

        cmd = [
            gemini,
            "-p", full_prompt,
            "-o", "stream-json",
            "--approval-mode", "yolo",
        ]
        if model:
            cmd.extend(["--model", model])
        if session_id:
            cmd.extend(["--resume", session_id])

        env = os.environ.copy()
        if session_id:
            env["GEMINI_SESSION_ID"] = session_id

        start = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )
        except subprocess.TimeoutExpired:
            if not explicit_model:
                # Timeout may indicate the model is overloaded — try next tier
                status = mark_model_exhausted(model, status)
                next_model, _ = get_best_available_model(status)
                if next_model != model:
                    print(
                        f"[gemini-bridge] {model} timed out, falling back to {next_model}",
                        file=sys.stderr,
                    )
                    attempts.append(f"{model}(timeout)")
                    model = next_model
                    continue
            return {
                "status": "error",
                "content": f"Gemini CLI timed out after {timeout}s",
                "tools_used": [],
                "model": model,
                "session_id": session_id,
                "duration_s": round(time.time() - start, 1),
                "model_fallback": attempts if len(attempts) > 1 else None,
            }

        # Check for capacity exhaustion before parsing
        if is_capacity_error(result.stderr or "", result.stdout or ""):
            status = mark_model_exhausted(model, status)
            retry_info = status[model]

            if explicit_model:
                # User specified this model — don't fallback, just report
                return {
                    "status": "error",
                    "content": f"{model} capacity exhausted. Retry after {retry_info['retry_after_iso']}.",
                    "tools_used": [],
                    "model": model,
                    "session_id": session_id,
                    "duration_s": round(time.time() - start, 1),
                    "model_exhausted": model,
                    "retry_after": retry_info["retry_after_iso"],
                }

            # Auto-fallback: try the next tier
            next_model, skipped = get_best_available_model(status)
            if next_model == model:
                # All models exhausted
                soonest_retry = min(
                    (status[m]["retry_after_iso"] for m in MODEL_TIERS if m in status),
                    default="unknown",
                )
                return {
                    "status": "error",
                    "content": f"All Gemini models exhausted. Earliest retry: {soonest_retry}",
                    "tools_used": [],
                    "model": model,
                    "session_id": session_id,
                    "duration_s": round(time.time() - start, 1),
                    "model_fallback": attempts,
                    "all_exhausted": True,
                    "retry_after": soonest_retry,
                }

            # Log the fallback and retry
            print(
                f"[gemini-bridge] {model} exhausted, falling back to {next_model}",
                file=sys.stderr,
            )
            model = next_model
            continue

        # No capacity error — parse the response
        break

    # Parse NDJSON events from stdout
    content_parts = []
    tools_used = []
    detected_model = model
    detected_session = session_id

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")

        if event_type == "init":
            detected_session = event.get("session_id", detected_session)
            detected_model = event.get("model", detected_model)

        elif event_type == "message":
            role = event.get("role", "")
            if role == "assistant" or role == "model":
                content = event.get("content", "")
                if content:
                    content_parts.append(content)

        elif event_type == "tool_use":
            tool_name = event.get("tool_name", event.get("name", "unknown"))
            tools_used.append(tool_name)

        elif event_type == "result":
            # Final event — may contain the complete response
            if "content" in event and event["content"]:
                content_parts.append(event["content"])

    final_content = "\n".join(content_parts) if content_parts else ""

    # If no content was extracted but there's raw stdout, use it as fallback
    if not final_content and result.stdout.strip():
        # Try to extract any text that isn't JSON
        non_json_lines = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("{"):
                non_json_lines.append(line)
        if non_json_lines:
            final_content = "\n".join(non_json_lines)

    # Check for errors
    response_status = "ok"
    if result.returncode and result.returncode != 0:
        response_status = "error"
        if not final_content:
            stderr = result.stderr.strip() if result.stderr else ""
            final_content = stderr or f"Gemini CLI exited with code {result.returncode}"

    response = {
        "status": response_status,
        "content": final_content,
        "tools_used": tools_used,
        "model": detected_model,
        "session_id": detected_session,
        "duration_s": round(time.time() - start, 1),
    }

    # Include fallback info if we fell back
    if len(attempts) > 1:
        response["model_fallback"] = attempts

    return response


def check_model_status() -> dict:
    """Return current model availability status for Claude to inspect."""
    status = load_model_status()
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


def main():
    parser = argparse.ArgumentParser(
        description="Invoke Gemini CLI and return structured JSON output"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to send to Gemini")
    parser.add_argument(
        "--agent", "-a",
        help="Target a specific Gemini agent (e.g., qa-engineer, backend-engineer)"
    )
    parser.add_argument(
        "--model", "-m",
        help="Gemini model to use (e.g., gemini-2.5-pro, gemini-2.5-flash)"
    )
    parser.add_argument(
        "--session-id", "-s",
        help="Resume an existing session for multi-turn conversation"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print raw NDJSON events to stderr"
    )
    parser.add_argument(
        "--workspace", "-w",
        help="Override workspace directory (default: Gemini Assistant project)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check model availability status and exit"
    )
    args = parser.parse_args()

    if args.status:
        print(json.dumps(check_model_status(), indent=2))
        return

    if not args.prompt:
        parser.error("prompt is required (unless using --status)")

    workspace = args.workspace or GEMINI_WORKSPACE
    if args.verbose:
        print(f"Workspace: {workspace}", file=sys.stderr)
        print(f"Agent: {args.agent or 'none'}", file=sys.stderr)
        print(f"Model: {args.model or 'auto (highest available)'}", file=sys.stderr)

    result = run_gemini(
        prompt=args.prompt,
        agent=args.agent,
        model=args.model,
        session_id=args.session_id,
        timeout=args.timeout,
        workspace=args.workspace,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
