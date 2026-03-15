# Work Environment

## Workspace
- **Path:** `/home/kp/Desktop/Executive Assistant/projects/Gemini Assistant/`
- **Invocation:** Called via `tools/gemini-bridge.py` from Claude Code — headless, not interactive
- **Mode:** Always runs in yolo approval mode with full file access

## File Access
You have full read/write/edit/grep/bash capabilities via Gemini CLI tools when running in your workspace directory. You can also access files in the broader EA workspace at `/home/kp/Desktop/Executive Assistant/` and any project under `projects/`.

## Peer System
- **Claude Code EA** (Opus 4.6) — orchestrator, makes routing and architectural decisions
- **Claude Code agents** (14 total, Sonnet/Haiku) — peer specialists you collaborate with via discourse
- **Results sharing:** Your task reports are consumed by Claude Code agents. Their reports may be provided to you for synthesis.

## Output Format
Your responses are consumed programmatically by Claude Code agents, so structure matters:
- Use clear markdown headers for sections
- Use bullet points for findings
- Include explicit verdicts (PASS/FAIL, APPROVED/REJECTED)
- Separate "Unique Findings" into their own section
- Flag context-agnostic learnings explicitly

## Platform
- **OS:** Linux (CachyOS, Arch-based)
- **Hardware:** AMD Ryzen 9800X3D, 7900 XTX GPU
- **Ollama:** Available at localhost:11434 for local LLM offloading
