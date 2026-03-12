---
name: local-llm
description: Offload simple tasks to the local Ollama LLM (qwen3:14b) to save API tokens. Use for drafting text, summarizing, reformatting data, brainstorming, simple code generation, boilerplate, and quick Q&A. Do NOT use for multi-step planning, complex code, safety-critical content, or student-facing work.
model: claude-sonnet-4-6
effort: low
tools: [Bash, Read]
---

# Local LLM Offloading

## Purpose
Delegate simple tasks to the local Ollama instance (qwen3:14b on Radeon 7900 XTX) to conserve Claude API tokens.

## When to Use
- Drafting text (emails, messages, descriptions)
- Summarizing files or content
- Reformatting data (JSON <-> CSV <-> Markdown tables)
- Brainstorming / generating ideas
- Simple code generation or boilerplate
- Quick Q&A that doesn't need deep reasoning

## When NOT to Use
- Multi-step planning or architectural decisions
- Complex code that needs to be correct the first time
- Tasks requiring multiple coordinated tool calls
- Safety-critical or student-facing content needing high quality
- When Ollama is unavailable (check first)

## Steps

1. **Check Ollama availability:**
   ```bash
   curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo "available" || echo "unavailable"
   ```
   If unavailable, handle the task yourself. Do not ask Kellen to start the service.

2. **Run the local agent.** Pass the task as a quoted prompt:
   ```bash
   cd "/home/kp/Desktop/Executive Assistant" && python3 tools/local-agent.py "YOUR PROMPT"
   ```

   Options:
   - Custom system prompt: `--system "You are a code reviewer."`
   - Pipe input: `echo "content" | python3 tools/local-agent.py --stdin`
   - Different model: `--model "qwen2:7b"`

   For simple, fast responses, append `/no_think` to the prompt.

3. **Review the output.** The local LLM may produce lower-quality results. Sanity-check before presenting to Kellen. Fix obvious errors yourself rather than re-running.

## Output
- Text output printed to stdout
- The agent has file tools (read, write, edit, grep, bash) so it can modify files directly if instructed

## Error Handling
- **Ollama unavailable:** Handle the task yourself silently. No escalation needed.
- **Model not loaded:** Run `ollama pull qwen3:14b` and retry once.
- **Timeout or hang:** Kill with Ctrl+C (timeout after 120s default). Retry once, then handle yourself.
- **Low quality output:** Discard and handle yourself. Do not present garbage to Kellen.
