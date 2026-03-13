# Current Priorities

<!-- Ordered by importance. Update as goals evolve. -->
<!-- The EA reads this at session start to understand what matters most right now. -->

## Priority 1: System Maturity (WAT Implementation)
**Goal:** Complete the **Deterministic Execution Layer** (Tools) to fully align with the architectural blueprint.
- **Status:** In Progress (Gmail, Calendar, Search, Logger, and **Session Isolation** implemented).
- **Key Milestones:** Add Slack integration, build a local state database (SQLite/Airtable), and refine all workflows for tool-first execution.
- **Blockers:** Missing `credentials.json` for live Gmail/Calendar testing.

## Priority 2: Efficiency & Cost Optimization
**Goal:** Maximize the system's ability while **minimizing token usage** through context compaction and model routing.
- **Status:** Strategizing.
- **Key Milestones:** Implement prompt caching for core instruction files, use "Dense Context" only for sub-agents, and dynamically toggle model effort tiers (low/med/high) based on task complexity.

## Priority 3: Autonomous Inbox-to-Project Pipeline
**Goal:** Transition the system from passive responding to active, background triaging of communications.
- **Status:** Initial `inbox-triage` workflow drafted.
- **Key Milestones:** Verify classification accuracy using the P.A.R.A. method and automate the Daily Briefing generation.

## Guiding Principles
- **Token Efficiency First:** Treat the context window as a finite resource; use compaction and caching wherever possible.
- **P.A.R.A. Order:** Meticulously categorize every action into Projects, Areas, Resources, or Archives.
- **Log Everything:** Every tool call and agent verdict must be recorded in the Operational Log for auditability.
- **Hierarchical Intelligence:** Orchestrate with Gemini 3.0 Pro (Manager); execute with specialists on Gemini 2.5 (Flash/Pro).
