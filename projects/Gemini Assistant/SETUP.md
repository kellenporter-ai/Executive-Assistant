# Getting Started with Your Gemini Executive Assistant

This guide walks you through setting up and personalizing your EA.

## Prerequisites

1. **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
2. **A Google account** — For Gemini API access (free tier or API key)
3. **Git** — Optional, for repo sync features

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

### 2. Set up authentication

You have two options:

**Option A: Google account login (recommended)**
1. Install Gemini CLI: follow instructions at [geminicli.com](https://geminicli.com)
2. Run `gemini auth login` in your terminal
3. Log in with your Google account in the browser that opens
4. Done — the EA will use your Google account automatically

**Option B: API key**
1. Get an API key from [aistudio.google.com](https://aistudio.google.com)
2. Create a file called `.env` in this folder
3. Add: `GEMINI_API_KEY=your-key-here`

### 3. Launch the EA

**Mac/Linux:**
```bash
./start.sh
```

**Windows:**
Double-click `start.bat`

The first launch installs dependencies (takes ~30 seconds). After that, it starts instantly.

Your browser will open to `http://localhost:3131` with the chat interface.

## Using the Web Interface

### The Chat
Type messages in the text box and press Enter (or click the send button). The EA can:
- Answer questions about your work and priorities
- Read and write files in your workspace
- Run shell commands (git, npm, etc.)
- Follow multi-step workflows automatically

### Quick Actions
- **"sign on"** — Start-of-day dashboard with repo status and priorities
- **"sign off"** — End-of-day: commit, push, update priorities, save memories
- **"briefing"** — Quick catch-up on recent activity

### Header Buttons
- **Reload Context** — Re-reads GEMINI.md and context files (useful after you edit them)
- **New Chat** — Clears conversation history for a fresh start
- **Settings** — Change API key or model

### Tool Calls
When the EA reads files, runs commands, or makes changes, you'll see collapsible tool call indicators. Click them to see details of what the EA did.

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

Both use the same GEMINI.md, context files, memory, and agents — they're interchangeable.

## How It Works

### The Brain: GEMINI.md
The EA's operating instructions. Loaded automatically at session start. You generally don't need to modify it.

### Agents: .gemini/agents/
Specialist sub-agents that handle scoped work (frontend, backend, QA, etc.). Auto-discovered by Gemini CLI; called via function calling in the web interface.

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
| "Authentication failed" | Run `gemini auth login` or add API key to `.env` |
| Browser doesn't open | Go to `http://localhost:3131` manually |
| "Python not found" | Install Python 3.10+ from python.org |
| Slow first message | Normal — first message loads the model. Subsequent messages are faster |
| Tool calls failing | Check that the EA has file permissions in this directory |
