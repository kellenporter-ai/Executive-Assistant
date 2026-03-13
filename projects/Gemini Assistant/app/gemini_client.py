"""
Gemini API client with function calling support.
Supports both API key auth and Google OAuth login.
"""

import os
import json
import subprocess
from pathlib import Path
from google import genai
from google.genai import types
from tools import TOOL_DECLARATIONS, execute_tool, get_workspace


def _find_api_key() -> str | None:
    """Check multiple sources for a Gemini API key."""
    for var in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"]:
        key = os.environ.get(var)
        if key:
            return key
    # Check .env file in workspace
    env_file = os.path.join(get_workspace(), ".env")
    if os.path.isfile(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
                        return v.strip().strip('"').strip("'")
    return None


def _get_gemini_cli_api_key() -> str | None:
    """Try to get an API key from Gemini CLI config."""
    # Gemini CLI may store config in ~/.gemini/
    config_paths = [
        os.path.expanduser("~/.gemini/.env"),
        os.path.expanduser("~/.config/gemini/.env"),
    ]
    for path in config_paths:
        if os.path.isfile(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _load_system_prompt() -> str:
    """Build the system prompt from GEMINI.md and context files."""
    workspace = get_workspace()
    parts = []

    # Load GEMINI.md
    gemini_md = os.path.join(workspace, "GEMINI.md")
    if os.path.isfile(gemini_md):
        with open(gemini_md, "r") as f:
            parts.append(f.read())

    # Load context files
    context_dir = os.path.join(workspace, "context")
    if os.path.isdir(context_dir):
        for fname in sorted(os.listdir(context_dir)):
            fpath = os.path.join(context_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".md"):
                with open(fpath, "r") as f:
                    content = f.read().strip()
                    # Skip empty template files
                    if content and not all(line.strip().startswith("<!--") or line.strip().endswith("-->") or line.strip().startswith("#") or line.strip() == "" for line in content.split("\n")):
                        parts.append(f"--- {fname} ---\n{content}")

    # Load memory index
    memory_md = os.path.join(workspace, "memory", "MEMORY.md")
    if os.path.isfile(memory_md):
        with open(memory_md, "r") as f:
            parts.append(f"--- Memory Index ---\n{f.read()}")

    return "\n\n".join(parts)


def _build_tool_declarations() -> list[types.Tool]:
    """Convert our tool declarations to Gemini API format."""
    function_declarations = []
    for tool in TOOL_DECLARATIONS:
        function_declarations.append(types.FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
        ))
    return [types.Tool(function_declarations=function_declarations)]


class GeminiChat:
    """Manages a Gemini chat session with function calling."""

    def __init__(self, api_key: str | None = None):
        # Try multiple auth sources in order
        resolved_key = api_key or _find_api_key() or _get_gemini_cli_api_key()

        if resolved_key:
            self.client = genai.Client(api_key=resolved_key)
            self._auth_method = "API key"
        else:
            # Last resort: try ADC (works if user ran `gcloud auth application-default login`)
            try:
                import google.auth
                credentials, project = google.auth.default()
                self.client = genai.Client(
                    vertexai=True,
                    project=project or os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
                    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
                    credentials=credentials,
                )
                self._auth_method = "Google Cloud ADC"
            except Exception:
                raise RuntimeError(
                    "No Gemini API credentials found.\n"
                    "Option 1: Add GEMINI_API_KEY=your-key to .env\n"
                    "Option 2: Run 'gemini auth login' in your terminal\n"
                    "Option 3: Run 'gcloud auth application-default login'"
                )

        self.model = "gemini-2.5-flash"
        self.system_prompt = _load_system_prompt()
        self.tools = _build_tool_declarations()
        self.history: list[types.Content] = []

    def _make_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            tools=self.tools,
            temperature=0.7,
        )

    async def send_message(self, user_message: str) -> dict:
        """
        Send a message and handle function calling loops.
        Returns {"response": str, "tool_calls": [{"name": str, "args": dict, "result": str}]}
        """
        # Add user message to history
        self.history.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        ))

        tool_calls_log = []
        max_rounds = 10  # Prevent infinite tool-calling loops

        for _ in range(max_rounds):
            # Call Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.history,
                config=self._make_config(),
            )

            # Check if the model wants to call functions
            function_calls = []
            text_parts = []

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                    if part.text:
                        text_parts.append(part.text)

            if not function_calls:
                # No function calls — we have the final response
                final_text = "\n".join(text_parts) if text_parts else ""
                # Add assistant response to history
                if response.candidates and response.candidates[0].content:
                    self.history.append(response.candidates[0].content)
                return {
                    "response": final_text,
                    "tool_calls": tool_calls_log
                }

            # Add the model's response (with function calls) to history
            if response.candidates and response.candidates[0].content:
                self.history.append(response.candidates[0].content)

            # Execute function calls and build results
            function_response_parts = []
            for fc in function_calls:
                args = dict(fc.args) if fc.args else {}
                result = execute_tool(fc.name, args)

                tool_calls_log.append({
                    "name": fc.name,
                    "args": args,
                    "result": result[:2000]  # Truncate for log display
                })

                function_response_parts.append(types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result}
                ))

            # Add function results to history
            self.history.append(types.Content(
                role="user",
                parts=function_response_parts
            ))

        # If we exhausted rounds, return what we have
        return {
            "response": "[Max tool-calling rounds reached. The assistant may need to continue in the next message.]",
            "tool_calls": tool_calls_log
        }

    def reload_system_prompt(self):
        """Reload GEMINI.md and context files (useful after edits)."""
        self.system_prompt = _load_system_prompt()

    def clear_history(self):
        """Clear conversation history for a fresh start."""
        self.history = []

    def get_history_summary(self) -> list[dict]:
        """Return a simplified view of the conversation history."""
        summary = []
        for content in self.history:
            entry = {"role": content.role, "parts": []}
            for part in content.parts:
                if part.text:
                    entry["parts"].append({"type": "text", "content": part.text[:200]})
                elif part.function_call:
                    entry["parts"].append({"type": "function_call", "name": part.function_call.name})
                elif part.function_response:
                    entry["parts"].append({"type": "function_response", "name": part.function_response.name})
            summary.append(entry)
        return summary
