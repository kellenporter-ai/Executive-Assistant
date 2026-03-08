---
name: local-llm
description: Delegate tasks to the local Ollama LLM (qwen3:14b) running on GPU. The local agent has tool access — it can read/write files, grep, list files, and run bash commands autonomously. Use this for tasks that don't need Claude-level reasoning — drafting, summarizing, reformatting, brainstorming, simple code gen, file lookups, or any task where "good enough" saves API cost.
model: claude-sonnet-4-6
---

## Steps

1. Determine whether the task needs tool access or is a simple text-in/text-out job.

2. **With tool access** (file reads, searches, edits, commands) — use the agent script:
```bash
cd "/home/kp/Desktop/Executive Assistant" && python3 tools/local-agent.py "YOUR PROMPT HERE"
```

   Add `-v` for verbose mode (shows tool calls on stderr):
```bash
python3 tools/local-agent.py -v "YOUR PROMPT HERE"
```

   Add `-s` for a custom system prompt:
```bash
python3 tools/local-agent.py -s "You are a code reviewer." "Review the file at context/me.md"
```

3. **Simple text-only tasks** (no file access needed) — use the raw API for speed:
```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:14b",
  "prompt": "<YOUR_PROMPT_HERE> /no_think",
  "stream": false,
  "options": { "temperature": 0.7, "num_predict": 2048 }
}' | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

4. Present the response to the user. If quality isn't sufficient, handle the task yourself instead of re-prompting.

## Agent Script Details (`tools/local-agent.py`)
- **Tools available:** read_file, write_file, edit_file, list_files, grep, bash
- **Safety:** file ops restricted to `/home/kp/`, dangerous bash commands blocked
- **Max turns:** 15 agentic loops
- **Timeout:** 30s per bash command, 120s per LLM call
- **Env vars:** `LOCAL_MODEL` (default: qwen3:14b), `LOCAL_AGENT_WORKDIR` (default: cwd)

## Tips
- Keep prompts focused — 14b works best with clear, single-task instructions
- Append `/no_think` for faster responses on simple tasks
- For creative tasks, the agent uses temperature 0.3 by default (good for accuracy)
- Max context is ~32k tokens — don't dump entire codebases
- The agent can chain multiple tool calls autonomously (up to 15 turns)
