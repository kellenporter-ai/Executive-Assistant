#!/usr/bin/env python3
"""
Gemini Bridge — invokes the Gemini CLI as a subprocess and returns structured output.

The Gemini CLI has full file access (read, write, edit, grep, bash) when run
in its workspace directory. This bridge just invokes it and captures output —
Gemini handles everything else autonomously in yolo mode (no permission prompts).

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
) -> dict:
    """
    Run the Gemini CLI synchronously and return structured output.

    Collects the NDJSON stream, extracts content and tool usage,
    and returns a single JSON result.
    """
    gemini = get_gemini_path()
    full_prompt = build_prompt(prompt, agent)

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
            cwd=GEMINI_WORKSPACE,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "content": f"Gemini CLI timed out after {timeout}s",
            "tools_used": [],
            "model": model,
            "session_id": session_id,
            "duration_s": round(time.time() - start, 1),
        }

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
    status = "ok"
    if result.returncode and result.returncode != 0:
        status = "error"
        if not final_content:
            stderr = result.stderr.strip() if result.stderr else ""
            final_content = stderr or f"Gemini CLI exited with code {result.returncode}"

    return {
        "status": status,
        "content": final_content,
        "tools_used": tools_used,
        "model": detected_model,
        "session_id": detected_session,
        "duration_s": round(time.time() - start, 1),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Invoke Gemini CLI and return structured JSON output"
    )
    parser.add_argument("prompt", help="Prompt to send to Gemini")
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
    args = parser.parse_args()

    if args.verbose:
        print(f"Workspace: {GEMINI_WORKSPACE}", file=sys.stderr)
        print(f"Agent: {args.agent or 'none'}", file=sys.stderr)
        print(f"Model: {args.model or 'default'}", file=sys.stderr)

    result = run_gemini(
        prompt=args.prompt,
        agent=args.agent,
        model=args.model,
        session_id=args.session_id,
        timeout=args.timeout,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
