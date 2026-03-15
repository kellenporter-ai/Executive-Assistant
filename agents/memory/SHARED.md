# Shared Agent Memory

Cross-cutting knowledge that applies to multiple agents. Any agent can read and append to this file. The `/remember` skill consolidates cross-agent learnings here.

## What Belongs Here

- **Project-wide conventions** — naming patterns, file structure rules, shared constants
- **Cross-cutting gotchas** — things that bit one agent and would bite another (e.g., Firestore field renames, API contract changes)
- **Environment facts** — hardware constraints (Chromebook 1366x768), browser targets, deployment quirks
- **Shared discoveries** — patterns confirmed across multiple agents or sessions

## What Does NOT Belong Here

- Agent-specific domain knowledge (goes in that agent's own MEMORY.md)
- Session-specific context (temporary, not durable)
- Anything already documented in `context/` files or `CLAUDE.md`

---

## Domain File Index

Read only the domain files relevant to your current task. Portal work → SHARED-portal.md. Environment/tool questions → SHARED-env.md. Agent process questions → SHARED-conventions.md.

| Domain | File | Contents |
|--------|------|----------|
| Portal | `SHARED-portal.md` | Portal conventions, LessonBlock schema, student UI layout, content generation gotchas, Vite build config, all Portal/Firestore/assessment/enrollment/chat gotchas |
| Environment | `SHARED-env.md` | Student hardware, browser target, deploy target, Python 3.14 compat, tool/infrastructure gotchas |
| Agent Conventions | `SHARED-conventions.md` | Canonical agent structure, create-assessment QA ordering, downstream context in task reports, Explore agents doc-vs-code warning |
