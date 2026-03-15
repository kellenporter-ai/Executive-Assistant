# Gemini Assistant → Headless Discourse Agent

**Date:** 2026-03-15
**Type:** ARCHITECTURE

## Decision
Transform the non-shared Gemini Assistant from a full web app (FastAPI + chat UI) into a headless discourse agent integrated with the Claude Code dev-pipeline. The Shared version remains a distributable web app.

## Rationale
- The non-shared version's value is as a **peer AI system** in the pipeline, not as a standalone chat app
- Cross-model discourse (Claude + Gemini working the same task in parallel) produces stronger QA and analysis
- Gemini CLI's yolo mode with full file access complements Claude Code's permission-gated approach
- Context-agnostic learnings from the working version flow to the Shared version, improving both

## What Changed
- Removed: FastAPI server, chat UI (~8K lines), setup wizard, start scripts
- Created: `tools/gemini-bridge.py`, `agents/gemini-assistant.md`, `.claude/skills/discourse/SKILL.md`
- Modified: dev-pipeline (Step 4b discourse QA), ROUTING.md, remember/context-sync skills, CLAUDE.md
- Populated: Gemini context files with discourse agent identity
- Rewrote: GEMINI.md and PROJECT_MAP.md for headless operation
