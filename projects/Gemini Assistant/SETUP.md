# Getting Started with Your Gemini Executive Assistant

This guide walks you through setting up and personalizing your EA.

## Prerequisites

1. **Gemini CLI** — Install with `npm install -g @google/gemini-cli`
2. **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
3. **A Google account** — For Gemini authentication
4. **Git** — Optional, for repo sync features

## Quick Start (3 steps)

### 1. Fill in your context

These files tell the EA who you are. Open each one and fill in the sections:

| File | What to fill in |
|------|----------------|
| `context/me.md` | Your role, expertise, preferences |
| `context/work.md` | Hardware, software, deployment targets |
| `context/team.md` | People you work with, collaboration norms |
| `context/current_priorities.md` | What you're working on right now |
| `context/rules.md` | How the EA should communicate with you |

**This is the most important step.** The more context you provide, the better the EA performs.

### 2. Authenticate with Gemini

Run these two commands in your terminal:

```bash
npm install -g @google/gemini-cli
gemini auth login
```

A browser window will open — log in with your Google account. That's it. The CLI handles all authentication natively.

### 3. Launch the EA

**Mac/Linux:**
```bash
./start.sh
```

**Windows:**
Double-click `start.bat`

The first launch installs Python dependencies (takes ~30 seconds). After that, it starts instantly.

Your browser will open to `http://localhost:3131` with the chat interface.

## Using the Web Interface

### The Chat
Type messages in the text box and press Enter (or click the send button). The EA can:
- Answer questions about your work and priorities
- Read and write files in your workspace
- Run shell commands (git, npm, etc.)
- Follow multi-step workflows automatically
- Delegate to specialist agents for complex tasks

### Quick Actions
- **"sign on"** — Start-of-day dashboard with repo status and priorities
- **"sign off"** — End-of-day: commit, push, update priorities, save memories
- **"briefing"** — Quick catch-up on recent activity

### Header Buttons
- **New Chat** — Clears conversation history for a fresh start

### Tool Calls
When the EA reads files, runs commands, or makes changes, you'll see collapsible tool call indicators with live status. Click them to see details of what the EA did.

### Streaming Responses
Responses stream in real-time as the Gemini CLI generates them. You'll see text appear word-by-word and tool calls update from "running" to "done" as they complete.

## Two Ways to Use the EA

### Web Interface (recommended for most users)
Launch with `./start.sh` — get a friendly chat UI in your browser. Best for:
- People who prefer a visual interface
- Quick conversations and task management
- Seeing tool calls and file operations in context

### Gemini CLI (power users)
Run `gemini` in this directory — the CLI reads GEMINI.md automatically. Best for:
- Developers comfortable with terminals
- Advanced agent delegation features
- Maximum control and speed

Both use the same GEMINI.md, context files, memory, and agents — they're interchangeable. The web interface is a thin proxy over the same CLI.

## How It Works

### Architecture
The web UI is a thin shell over the Gemini CLI. When you send a message:
1. The server spawns `gemini -p "your message" -o stream-json`
2. The CLI loads GEMINI.md, authenticates, calls tools, and delegates to agents
3. The server streams NDJSON events back to the browser
4. The browser renders text, tool calls, and results in real-time
5. Session continuity is maintained via `--resume` on subsequent messages

### The Brain: GEMINI.md
The EA's operating instructions. Loaded automatically by the CLI at each invocation. You generally don't need to modify it.

### Agents: .gemini/agents/
Specialist sub-agents that handle scoped work (frontend, backend, QA, etc.). Auto-discovered and delegated to by the Gemini CLI natively.

### Workflows: workflows/
Step-by-step procedures for common tasks. Think of them as recipes the EA follows when you ask for specific things.

### Memory: memory/
The EA learns from each session. When you correct it or share preferences, it saves these as memory files that persist across conversations.

### Decisions: decisions/
Major decisions get logged with rationale, preventing re-litigation of settled questions.

## Customization

### Adding domain-specific agents
Say "create an agent for [domain]" — the EA will use the agent-creator workflow. Or manually create `.gemini/agents/your-agent.md`.

### Adding workflows
Create a new file in `workflows/` following `templates/skill-template.md`, then add a trigger entry to the workflow table in `GEMINI.md`.

### Per-project context
For each project: create `projects/<name>/` with a `context.md` describing the stack and conventions.

## Tips

1. **Correct the EA early and often** — Say "don't do X because Y" and it'll remember for future sessions.
2. **Keep priorities current** — The EA reads `current_priorities.md` every session.
3. **Use sign-on/sign-off** — These bookend your sessions and keep everything in sync.
4. **Let it specialize** — The more you use it, the more it adapts to your work patterns.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Gemini CLI not found" | Run `npm install -g @google/gemini-cli` |
| "Authentication failed" | Run `gemini auth login` in your terminal |
| Browser doesn't open | Go to `http://localhost:3131` manually |
| "Python not found" | Install Python 3.10+ from python.org |
| Slow first message | Normal — first message loads the model. Subsequent messages are faster |
