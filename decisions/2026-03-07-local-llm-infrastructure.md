# Decision: Local LLM Infrastructure

**Date:** 2026-03-07
**Status:** Implemented

## Context
Claude API token costs add up for simple tasks (drafting, summarizing, reformatting). Desktop has a Radeon 7900 XTX with 24GB VRAM — enough to run capable local models.

## Decision
- Installed Ollama (ROCm) with qwen3:14b as the local model
- Built `tools/local-agent.py` — an agentic wrapper that gives the local LLM tool access (read/write/grep/bash)
- Added local LLM offloading rules to CLAUDE.md so Claude auto-delegates simple tasks on the desktop
- Created sign-on/sign-off session management skills
- Consolidated skills from legacy `skills/` to `.claude/skills/` (single source of truth)
- Created `PROJECT_MAP.md` for LLM workspace orientation

## Rationale
- Save API tokens on tasks that don't need Claude-level reasoning
- Local model runs entirely on GPU — no data leaves the machine
- Context-aware system prompt (auto-loads PROJECT_MAP.md + skill index) means zero wasted turns on orientation
- Only available on desktop; laptop sessions gracefully skip offloading

## Trade-offs
- qwen3:14b quality ceiling is lower than Claude for complex tasks
- Local model can't spawn Claude Code subagents
- Adds a dependency on Ollama service being running (mitigated by availability check)
