"""
Local tool implementations for the Gemini EA.
All file operations are sandboxed to the workspace directory.
"""

import os
import subprocess
import glob as glob_module
import json
from pathlib import Path


def get_workspace() -> str:
    """Return the workspace root (parent of app/)."""
    return str(Path(__file__).resolve().parent.parent)


def _safe_path(filepath: str) -> str:
    """Resolve a path and ensure it's within the workspace. Raises ValueError if not."""
    workspace = get_workspace()
    resolved = os.path.normpath(os.path.join(workspace, filepath))
    if not resolved.startswith(workspace):
        raise ValueError(f"Access denied: path '{filepath}' is outside the workspace")
    return resolved


# --- Tool Definitions (for Gemini function calling) ---

TOOL_DECLARATIONS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file in the workspace. Returns the full text content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from workspace root (e.g., 'context/me.md')"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace. Creates the file and parent directories if they don't exist. Overwrites existing content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from workspace root"
                },
                "content": {
                    "type": "string",
                    "description": "The full content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Replace a specific string in a file. The old_string must be unique within the file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from workspace root"
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact text to find and replace"
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement text"
                }
            },
            "required": ["path", "old_string", "new_string"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files and directories at a given path. Returns names with '/' suffix for directories.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from workspace root. Use '.' for the root."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files matching a glob pattern, or search file contents with a text query.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern for file names (e.g., '**/*.md') OR text to search for in file contents"
                },
                "search_content": {
                    "type": "boolean",
                    "description": "If true, search inside file contents instead of matching file names. Default false."
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "run_command",
        "description": "Execute a shell command in the workspace directory. Use for git, npm, python, or other CLI tools. Commands are restricted to the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                }
            },
            "required": ["command"]
        }
    },
]


# --- Tool Implementations ---

def read_file(path: str) -> str:
    safe = _safe_path(path)
    if not os.path.isfile(safe):
        return f"Error: File not found: {path}"
    try:
        with open(safe, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > 100_000:
            return content[:100_000] + f"\n\n[Truncated — file is {len(content)} characters]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    safe = _safe_path(path)
    try:
        os.makedirs(os.path.dirname(safe), exist_ok=True)
        with open(safe, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    safe = _safe_path(path)
    if not os.path.isfile(safe):
        return f"Error: File not found: {path}"
    try:
        with open(safe, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(old_string)
        if count == 0:
            return f"Error: old_string not found in {path}"
        if count > 1:
            return f"Error: old_string appears {count} times in {path} — must be unique"
        new_content = content.replace(old_string, new_string, 1)
        with open(safe, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error editing file: {e}"


def list_directory(path: str) -> str:
    safe = _safe_path(path)
    if not os.path.isdir(safe):
        return f"Error: Directory not found: {path}"
    try:
        entries = sorted(os.listdir(safe))
        result = []
        for entry in entries:
            if entry.startswith(".") and entry not in [".gemini", ".env"]:
                continue
            full = os.path.join(safe, entry)
            suffix = "/" if os.path.isdir(full) else ""
            result.append(f"{entry}{suffix}")
        return "\n".join(result) if result else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


def search_files(pattern: str, search_content: bool = False) -> str:
    workspace = get_workspace()
    try:
        if search_content:
            matches = []
            for root, _, files in os.walk(workspace):
                if any(skip in root for skip in ["node_modules", ".git", "__pycache__", ".venv", "temp"]):
                    continue
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read(50_000)
                        if pattern.lower() in content.lower():
                            rel = os.path.relpath(fpath, workspace)
                            # Find matching lines
                            lines = content.split("\n")
                            for i, line in enumerate(lines, 1):
                                if pattern.lower() in line.lower():
                                    matches.append(f"{rel}:{i}: {line.strip()[:120]}")
                                    if len(matches) >= 50:
                                        break
                    except (OSError, UnicodeDecodeError):
                        continue
                    if len(matches) >= 50:
                        break
            return "\n".join(matches) if matches else f"No matches found for '{pattern}'"
        else:
            found = glob_module.glob(os.path.join(workspace, pattern), recursive=True)
            results = []
            for f in sorted(found)[:50]:
                rel = os.path.relpath(f, workspace)
                if not any(skip in rel for skip in ["node_modules", ".git", "__pycache__", ".venv"]):
                    results.append(rel)
            return "\n".join(results) if results else f"No files matching '{pattern}'"
    except Exception as e:
        return f"Error searching: {e}"


def run_command(command: str) -> str:
    workspace = get_workspace()
    # Block obviously dangerous commands
    dangerous = ["rm -rf /", "rm -rf ~", "mkfs", "dd if=", "> /dev/", ":(){ :|:& };:"]
    for d in dangerous:
        if d in command:
            return f"Error: Blocked dangerous command pattern: {d}"
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "HOME": os.path.expanduser("~")}
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        if len(output) > 50_000:
            output = output[:50_000] + "\n[Truncated]"
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error running command: {e}"


# --- Dispatcher ---

TOOL_MAP = {
    "read_file": lambda args: read_file(args["path"]),
    "write_file": lambda args: write_file(args["path"], args["content"]),
    "edit_file": lambda args: edit_file(args["path"], args["old_string"], args["new_string"]),
    "list_directory": lambda args: list_directory(args["path"]),
    "search_files": lambda args: search_files(args["pattern"], args.get("search_content", False)),
    "run_command": lambda args: run_command(args["command"]),
}


def execute_tool(name: str, args: dict) -> str:
    """Execute a tool by name with the given arguments."""
    fn = TOOL_MAP.get(name)
    if not fn:
        return f"Error: Unknown tool '{name}'"
    try:
        return fn(args)
    except Exception as e:
        return f"Error executing {name}: {e}"
