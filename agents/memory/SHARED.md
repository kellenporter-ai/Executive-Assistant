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

## Environment

- **Student hardware:** Chromebook, 1366x768 viewport, trackpad input, integrated GPU
- **Browser target:** Chrome (latest stable on ChromeOS)
- **Deploy target:** Firebase Hosting + Cloud Functions v2

## Portal Conventions

- All interactive HTML activities are single self-contained files (no external assets except approved CDNs)
- Proctor Bridge is mandatory for portal-embedded activities
- Dark theme CSS variables from `references/portal-bridge.md` are the standard
- 44px minimum touch targets on all interactive elements

## Web Research Pipeline

- **Tool:** `tools/web-research.py` — CLI with `search`, `extract`, `convert`, `research` commands
- **Skill:** `/web-research` — orchestrates the tool with WebSearch fallback
- **Extraction tiers:** Crawl4AI (local, unlimited) → Jina Reader (free proxy) → BeautifulSoup (static)
- **Discovery:** Serper API if `SERPER_API_KEY` is set in `.env`, otherwise WebSearch built-in
- **Document conversion:** MarkItDown (PDF/DOCX/PPTX → Markdown)
- **Output:** `temp/web-research/` (gitignored) — script prints file path to stdout
- **Run:** `tools/.venv/bin/python3 tools/web-research.py extract "URL"`

## Known Gotchas

- **Per-student announcement targeting** — Announcements support `targetStudentIds?: string[]`. When set, `StudentDashboard.tsx` filters so only listed students see it. Nudge buttons in TeacherDashboard use this for per-student or batch targeting. Class-wide announcements omit the field. No true DM/chat system exists — it's still the announcement pipeline.
- **Python 3.14 compat** — System Python is 3.14.3 (very new). Some packages (lxml, snowballstemmer) pin older versions that lack 3.14 wheels and fail to build from source. Workaround: install the package `--no-deps`, then install its dependencies separately — newer versions of the pinned deps usually work fine at runtime even if version specifiers don't match.
- **STARTED submissions were previously hidden** — `TeacherDashboard.tsx` used to filter `status !== 'STARTED'`. As of March 2026, they're included so admin can see in-progress work. Any new code consuming assessment submissions should expect STARTED status in the mix.
