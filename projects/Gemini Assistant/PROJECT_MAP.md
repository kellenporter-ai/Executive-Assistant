# Project Map — Gemini Executive Assistant

Quick-reference index of the entire workspace. Read this first to orient yourself.

## How This System Works

This is a **WAT (Workflow, Agent, Tool)** architecture:
- **GEMINI.md** is the brain — the orchestrator that reads your request and decides what to do
- **Agents** (`.gemini/agents/`) are specialists that handle scoped work (frontend, backend, QA, etc.)
- **Workflows** (`workflows/`) are step-by-step procedures for common tasks (dev pipeline, research, etc.)
- **Context** (`context/`) tells the EA who you are and how you want to work
- **Memory** (`memory/`) is how the EA learns and remembers across sessions

## Directory Structure

```text
Gemini Assistant/
├── GEMINI.md                     # EA operating instructions (Gemini reads this first)
├── PROJECT_MAP.md                # This file — workspace orientation
├── SETUP.md                      # Getting started guide for new users
├── start.sh                      # Launch script (Mac/Linux)
├── start.bat                     # Launch script (Windows)
│
├── app/                          # Web chat interface (CLI proxy server)
│   ├── server.py                 #   FastAPI backend (streams CLI output via SSE)
│   ├── gemini_client.py          #   CLI subprocess spawner (no SDK)
│   ├── requirements.txt          #   Python dependencies (fastapi, uvicorn only)
│   └── static/
│       └── index.html            #   Chat UI with streaming (served on localhost:3131)
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
│       ├── email-agent.md        #     Gmail triage, drafting, inbox management
│       ├── research-agent.md     #     Multi-source synthesis, literature review
│       ├── data-analyst.md       #     Metrics, analysis (read-only)
│       ├── technical-writer.md   #     API docs, changelogs, references
│       ├── performance-engineer.md #   Profiling, optimization
│       └── deployment-monitor.md #     Post-deploy health checks (monitor-only)
│
├── workflows/                    # Step-by-step procedures (imported via @)
│   ├── sign-on.md                #   Session initialization
│   ├── sign-off.md               #   Clean session shutdown
│   ├── remember.md               #   Memory consolidation
│   ├── context-sync.md           #   Weekly priority/memory maintenance
│   ├── daily-briefing.md         #   Activity summary and next steps
│   ├── dev-pipeline.md           #   Full dev lifecycle with agent orchestration
│   ├── inbox-triage.md           #   Gmail triage and classification
│   ├── web-research.md           #   Search, extract, convert
│   ├── slide-deck.md             #   Reveal.js presentations
│   ├── 2d-activity.md            #   Interactive HTML (Canvas/SVG/JS)
│   ├── 3d-activity.md            #   Babylon.js 3D simulations
│   ├── create-assessment.md      #   Build assessments from objectives
│   ├── lesson-plan.md            #   ISLE-aligned lesson creation
│   ├── generate-questions.md     #   Bulk question bank production
│   ├── study-guide.md            #   Student review materials from existing content
│   ├── rubric-audit.md           #   Rubric neutrality and quality checks
│   ├── changelog.md              #   Generate changelogs from git history
│   ├── dependency-audit.md       #   Security and package freshness checks
│   └── agent-creator.md          #   Create/audit agent definitions
│
├── context/                      # User identity and preferences
│   ├── me.md                     #   Role, expertise, preferences
│   ├── work.md                   #   Hardware, software, deployment
│   ├── team.md                   #   Team members and norms
│   ├── current_priorities.md     #   Active goals (read at session start)
│   └── rules.md                  #   Communication style and hard rules
│
├── memory/                       # Cross-session persistent knowledge
│   └── MEMORY.md                 #   Index (max 200 lines) → topic files
│
├── decisions/                    # Major decision log (dated entries)
├── references/                   # Domain knowledge and SOPs
│   └── agent-routing.md          #   Which agent handles which task
├── templates/                    # Reusable output formats
│   └── skill-template.md         #   Workflow file template
├── projects/                     # Ongoing projects and submodules
├── assets/                       # Reusable media (images, textures)
└── temp/                         # Temporary outputs (gitignored)
```

## Key Concepts

### Agents vs Workflows
- **Agents** are *who* — specialist personas with scoped expertise and boundaries
- **Workflows** are *what* — step-by-step procedures that may invoke agents

### Memory Types
| Type | Purpose |
|------|---------|
| `user` | Your role, preferences, expertise |
| `feedback` | Corrections to EA behavior (includes *why*) |
| `project` | Ongoing work context, decisions, deadlines |
| `reference` | Pointers to external systems and resources |

### Model Tiers
| Tier | Model | Used For |
|------|-------|----------|
| Manager | gemini-3.0-pro | EA orchestration via Gemini CLI (this is the CLI's own model, not declared in agent frontmatter) |
| Specialist | gemini-2.5-pro | Engineering agents, education agents, content creation |
| Fast | gemini-2.5-flash | QA, summaries, monitoring, email, research |
