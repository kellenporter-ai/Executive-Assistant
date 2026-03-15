# Shared Memory — Agent Conventions

Agent structure rules, process conventions, and cross-agent coordination patterns.

---

## Agent Conventions

- **Canonical agent structure (2026-03-12):** All 14 general agents follow: identity line → What I Do → What I Don't Do (delegate back) → Context Loading → Output Format → Cross-cutting Notes (for /remember). New agents must match this structure. The cross-cutting notes footer enables `/remember` to consolidate learnings from agent reports.
- **Create-assessment QA ordering:** QA audit (Step 6) runs BEFORE user review (Step 7). QA catches rubric neutrality, ISLE coverage, and a11y issues before Kellen sees the output. Rubric/structural issues route to assessment-designer; wording issues route to content-writer.
- **Downstream Context in task reports (2026-03-14):** All agents must populate the `**Downstream Context:**` field in their task report with interfaces, endpoints, data shapes, or file changes that peer agents need to consume. This enables parallel agent execution — agents can read each other's downstream context to coordinate without waiting for narrative reports.

## Known Gotchas — Agent Process

- **Explore agents report from docs, not code** — When using Explore agents to audit codebase state, they may report issues from markdown docs (e.g., CODE_REVIEW_4.md) as still pending even when the code has already been fixed. Always verify agent claims against actual source files before planning work. Read the actual component files, don't trust review doc descriptions of what's "missing".
