#!/usr/bin/env python3
"""
Local LLM Agent — gives Ollama tool access (read, write, grep, bash).
Runs an agentic loop: prompt -> model -> tool calls -> results -> repeat.

Usage:
  ./local-agent.py "summarize the file context/me.md"
  ./local-agent.py --system "You are a code reviewer." "review this function..."
  echo "explain this" | ./local-agent.py --stdin
  ./local-agent.py  # interactive mode
"""

import json
import os
import re
import subprocess
import sys
import glob as glob_mod
import requests
import argparse

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("LOCAL_MODEL", "qwen3:14b")
MAX_TURNS = 15
WORKDIR = os.environ.get("LOCAL_AGENT_WORKDIR", os.getcwd())
EA_ROOT = "/home/kp/Desktop/Executive Assistant"


def _build_default_system_prompt() -> str:
    """Build a context-aware system prompt from PROJECT_MAP.md and skill index."""
    parts = [
        "You are a local AI assistant for Kellen Porter's Executive Assistant workspace.",
        "You have tool access: read_file, write_file, edit_file, list_files, grep, bash.",
        "Be concise and direct. Complete tasks autonomously using your tools.",
        ""
    ]

    # Load PROJECT_MAP.md
    map_path = os.path.join(EA_ROOT, "PROJECT_MAP.md")
    if os.path.exists(map_path):
        with open(map_path, "r") as f:
            parts.append(f.read())
        parts.append("")

    # Build skill index from .claude/skills/*/SKILL.md frontmatter
    skills_dir = os.path.join(EA_ROOT, ".claude", "skills")
    if os.path.isdir(skills_dir):
        skill_entries = []
        for name in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.exists(skill_md):
                with open(skill_md, "r") as f:
                    content = f.read()
                # Extract description from YAML frontmatter
                desc = ""
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end != -1:
                        for line in content[3:end].split("\n"):
                            if line.strip().startswith("description:"):
                                desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                                if len(desc) > 120:
                                    desc = desc[:120] + "..."
                                break
                skill_entries.append(f"  - /{name}: {desc}")

        if skill_entries:
            parts.append("## Available Skills")
            parts.append("These skills exist in .claude/skills/ — read the SKILL.md for full instructions before executing one:")
            parts.extend(skill_entries)
            parts.append("")

    return "\n".join(parts)

# Safety: restrict file ops to these roots
ALLOWED_ROOTS = [
    os.path.expanduser("~"),
]

# --- Tool Definitions (Ollama/OpenAI format) ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Returns the text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"},
                    "limit": {"type": "integer", "description": "Max lines to read (default: all)"},
                    "offset": {"type": "integer", "description": "Line number to start from (0-indexed, default: 0)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed. Overwrites existing content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a specific string in a file with new content. The old_string must appear exactly once in the file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"},
                    "old_string": {"type": "string", "description": "Exact text to find and replace"},
                    "new_string": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files matching a glob pattern. Returns file paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.md', 'src/*.py')"},
                    "path": {"type": "string", "description": "Base directory (default: working directory)"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search file contents for a regex pattern. Returns matching lines with file paths and line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "path": {"type": "string", "description": "File or directory to search in (default: working directory)"},
                    "glob": {"type": "string", "description": "Filter files by glob pattern (e.g. '*.py')"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command and return stdout + stderr. Use for git, npm, system commands, etc. Timeout: 30s.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
]

# --- Tool Implementations ---

def _resolve_path(path: str) -> str:
    """Resolve a path relative to WORKDIR, with safety checks."""
    if not os.path.isabs(path):
        path = os.path.join(WORKDIR, path)
    path = os.path.realpath(path)
    if not any(path.startswith(root) for root in ALLOWED_ROOTS):
        raise PermissionError(f"Access denied: {path} is outside allowed roots")
    return path


def tool_read_file(path: str, limit: int = None, offset: int = 0) -> str:
    path = _resolve_path(path)
    with open(path, "r") as f:
        lines = f.readlines()
    if offset:
        lines = lines[offset:]
    if limit:
        lines = lines[:limit]
    content = "".join(lines)
    if len(content) > 50000:
        content = content[:50000] + "\n... (truncated at 50k chars)"
    return content


def tool_write_file(path: str, content: str) -> str:
    path = _resolve_path(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} chars to {path}"


def tool_edit_file(path: str, old_string: str, new_string: str) -> str:
    path = _resolve_path(path)
    with open(path, "r") as f:
        content = f.read()
    count = content.count(old_string)
    if count == 0:
        return f"Error: old_string not found in {path}"
    if count > 1:
        return f"Error: old_string appears {count} times in {path} — must be unique"
    content = content.replace(old_string, new_string, 1)
    with open(path, "w") as f:
        f.write(content)
    return f"Edited {path} — replaced 1 occurrence"


def tool_list_files(pattern: str, path: str = None) -> str:
    base = _resolve_path(path) if path else WORKDIR
    matches = sorted(glob_mod.glob(os.path.join(base, pattern), recursive=True))
    if not matches:
        return "No files matched."
    # Show relative paths for readability
    results = []
    for m in matches[:100]:
        try:
            results.append(os.path.relpath(m, WORKDIR))
        except ValueError:
            results.append(m)
    output = "\n".join(results)
    if len(matches) > 100:
        output += f"\n... ({len(matches) - 100} more)"
    return output


def tool_grep(pattern: str, path: str = None, glob_filter: str = None) -> str:
    base = _resolve_path(path) if path else WORKDIR
    cmd = ["grep", "-rn", "--color=never"]
    if glob_filter:
        cmd.extend(["--include", glob_filter])
    cmd.extend([pattern, base])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout
        if not output:
            return "No matches found."
        lines = output.strip().split("\n")
        if len(lines) > 50:
            return "\n".join(lines[:50]) + f"\n... ({len(lines) - 50} more matches)"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: grep timed out after 15s"


DANGEROUS_PATTERNS = [
    r'\brm\s+(-rf?|--recursive)\s+[/~]',  # rm -rf /
    r'\bmkfs\b', r'\bdd\s+if=', r'\b:(){ :\|:& };:',  # fork bomb
    r'\bshutdown\b', r'\breboot\b', r'\bpoweroff\b',
    r'\bsystemctl\s+(stop|disable|mask)\s+(sshd|NetworkManager|systemd)',
    r'>\s*/dev/sd', r'\bfdisk\b', r'\bparted\b',
]


def tool_bash(command: str) -> str:
    # Block obviously dangerous commands
    for pat in DANGEROUS_PATTERNS:
        if re.search(pat, command):
            return f"Error: blocked dangerous command matching pattern: {pat}"

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=30, cwd=WORKDIR
        )
        output = result.stdout + result.stderr
        if not output:
            return "(no output)"
        if len(output) > 30000:
            output = output[:30000] + "\n... (truncated at 30k chars)"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30s"


TOOL_DISPATCH = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "list_files": tool_list_files,
    "grep": tool_grep,
    "bash": tool_bash,
}

# --- Agent Loop ---

def call_ollama(messages: list, use_tools: bool = True) -> dict:
    """Send a chat request to Ollama."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 4096,
        }
    }
    if use_tools:
        payload["tools"] = TOOLS

    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with given arguments."""
    fn = TOOL_DISPATCH.get(name)
    if not fn:
        return f"Error: unknown tool '{name}'"
    try:
        return fn(**arguments)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def run_agent(prompt: str, system_prompt: str = None, verbose: bool = False) -> str:
    """Run the agent loop: prompt -> model -> tool calls -> results -> repeat."""
    messages = []

    # Use context-aware default if no system prompt provided
    if system_prompt is None:
        system_prompt = _build_default_system_prompt()

    messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    for turn in range(MAX_TURNS):
        if verbose:
            print(f"\n--- Turn {turn + 1} ---", file=sys.stderr)

        result = call_ollama(messages)
        msg = result.get("message", {})
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        # Add assistant message to history
        messages.append(msg)

        if not tool_calls:
            # Model is done — return its final response
            # Strip <think> blocks from output
            if content:
                content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)
            return content.strip()

        # Execute each tool call
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args = tc["function"]["arguments"]

            if verbose:
                print(f"  Tool: {fn_name}({json.dumps(fn_args, indent=2)[:200]})", file=sys.stderr)

            result_text = execute_tool(fn_name, fn_args)

            if verbose:
                preview = result_text[:200] + "..." if len(result_text) > 200 else result_text
                print(f"  Result: {preview}", file=sys.stderr)

            messages.append({
                "role": "tool",
                "content": result_text,
            })

    return "Error: agent exceeded maximum turns"


def interactive_mode(system_prompt: str = None, verbose: bool = False):
    """Run in interactive REPL mode."""
    print(f"Local Agent ({MODEL}) — type 'exit' to quit")
    print(f"Working directory: {WORKDIR}")
    print()

    while True:
        try:
            prompt = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            break

        response = run_agent(prompt, system_prompt=system_prompt, verbose=verbose)
        print()
        print(response)
        print()


# --- CLI ---

def main():
    global MODEL, WORKDIR

    parser = argparse.ArgumentParser(description="Local LLM Agent with tool access")
    parser.add_argument("prompt", nargs="?", help="Prompt to send (omit for interactive mode)")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show tool calls on stderr")
    parser.add_argument("--model", "-m", help=f"Model name (default: {MODEL})")
    parser.add_argument("--workdir", "-w", help=f"Working directory (default: cwd)")
    args = parser.parse_args()

    if args.model:
        MODEL = args.model
    if args.workdir:
        WORKDIR = os.path.realpath(args.workdir)

    if args.stdin:
        prompt = sys.stdin.read().strip()
        if not prompt:
            print("Error: no input on stdin", file=sys.stderr)
            sys.exit(1)
        print(run_agent(prompt, system_prompt=args.system, verbose=args.verbose))
    elif args.prompt:
        print(run_agent(args.prompt, system_prompt=args.system, verbose=args.verbose))
    else:
        interactive_mode(system_prompt=args.system, verbose=args.verbose)


if __name__ == "__main__":
    main()
