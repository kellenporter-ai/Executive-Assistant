# Project Map — Gemini Discourse Agent

Quick-reference index of the workspace. Read this first to orient yourself.

## How This System Works

This is a **headless discourse agent** in the Claude Code Executive Assistant's dev-pipeline. It runs Google's Gemini models alongside Claude Code agents to provide independent analysis through cross-model discourse.

**Architecture:**
- **GEMINI.md** is the brain — orchestrator instructions for headless operation
- **Agents** (`.gemini/agents/`) are 13 specialists that handle scoped work
- **Workflows** (`workflows/`) are step-by-step procedures for common tasks
- **Context** (`context/`) defines this agent's identity, environment, and priorities
- **Memory** (`memory/`) persists learnings across invocations

**Invocation:** Called via `tools/gemini-bridge.py` from Claude Code — not interactive, not browser-based.

**Key advantage:** Gemini CLI runs in yolo mode with full file access (read, write, edit, bash) and zero permission prompts.

## Directory Structure

```text
Gemini Assistant/
├── GEMINI.md                     # Discourse agent operating instructions
├── PROJECT_MAP.md                # This file — workspace orientation
│
├── app/                          # CLI integration
│   └── gemini_client.py          #   CLI subprocess spawner (reference library)
│
├── .gemini/                      # Gemini CLI configuration
│   ├── settings.json             #   Experimental agents enabled
│   └── agents/                   #   Sub-agent definitions (auto-discovered)
│       ├── ui-engineer.md        #     Frontend, components, accessibility
│       ├── backend-engineer.md   #     APIs, database, auth, security
│       ├── graphics-engineer.md  #     Canvas, SVG, Babylon.js, animations
│       ├── assessment-designer.md #    Rubric architecture, standards alignment
│       ├── curriculum-designer.md #    Learning objectives, unit sequencing
│       ├── qa-engineer.md        #     Testing, auditing (reports only)
│       ├── content-writer.md     #     User-facing copy and text
│       ├── email-agent.md        #     Gmail triage, drafting
│       ├── research-agent.md     #     Multi-source synthesis
│       ├── data-analyst.md       #     Metrics, analysis (read-only)
│       ├── technical-writer.md   #     API docs, changelogs
│       ├── performance-engineer.md #   Profiling, optimization
│       └── deployment-monitor.md #     Post-deploy health checks
│
├── workflows/                    # Step-by-step procedures (imported via @)
│   ├── remember.md               #   Memory consolidation
│   ├── context-sync.md           #   Priority/memory maintenance
│   ├── dev-pipeline.md           #   Full dev lifecycle with agent orchestration
│   ├── web-research.md           #   Search, extract, convert
│   ├── create-assessment.md      #   Build assessments from objectives
│   ├── lesson-plan.md            #   ISLE-aligned lesson creation
│   ├── generate-questions.md     #   Bulk question bank production
│   ├── study-guide.md            #   Student review materials
│   ├── rubric-audit.md           #   Rubric neutrality and quality checks
│   ├── changelog.md              #   Generate changelogs from git history
│   ├── dependency-audit.md       #   Security and package freshness checks
│   ├── agent-creator.md          #   Create/audit agent definitions
│   └── ...                       #   Additional workflows
│
├── context/                      # Agent identity and operating context
│   ├── me.md                     #   Discourse agent identity and strengths
│   ├── work.md                   #   Operating environment and output format
│   ├── team.md                   #   Peer agents (Claude Code + Gemini sub-agents)
│   ├── current_priorities.md     #   Discourse QA, synthesis, memory goals
│   └── rules.md                  #   Output rules and memory propagation
│
├── memory/                       # Cross-session persistent knowledge
│   └── MEMORY.md                 #   Index (max 200 lines) → topic files
│
├── decisions/                    # Major decision log (dated entries)
├── references/                   # Domain knowledge and SOPs
│   └── agent-routing.md          #   Which agent handles which task
├── templates/                    # Reusable output formats
├── assets/                       # Reusable media (images, textures)
└── temp/                         # Temporary outputs (gitignored)
```

## Key Concepts

### Discourse
Parallel analysis by Claude Code agents and this Gemini system on the same task. Each works independently, then the Claude Code EA synthesizes findings — agreements (high confidence), disagreements (resolved by EA), and unique findings (included from both).

### Agents vs Workflows
- **Agents** are *who* — specialist personas with scoped expertise and boundaries
- **Workflows** are *what* — step-by-step procedures that may invoke agents

### Memory Propagation
Context-agnostic learnings (useful to any user) are marked with `<!-- propagate-to-shared -->` and synced to the distributable Shared version via Claude Code's `/remember` and `/context-sync` skills.

### Memory Types
| Type | Purpose |
|------|---------|
| `user` | Role, preferences, expertise |
| `feedback` | Corrections to behavior (includes *why*) |
| `project` | Ongoing work context, decisions |
| `reference` | Pointers to external systems |

### Model Tiers
| Tier | Model | Used For |
|------|-------|----------|
| Manager | gemini-3.1-pro-preview | Orchestration, architectural decisions |
| Specialist | gemini-2.5-pro | Engineering agents, content creation |
| Fast | gemini-2.5-flash | QA, summaries, monitoring, research |
