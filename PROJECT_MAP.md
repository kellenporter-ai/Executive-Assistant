# Project Map — Executive Assistant

Quick-reference index of the entire workspace. Read this first to orient.

## Structure

```
Executive Assistant/
├── CLAUDE.md                  # Operating instructions (read first)
├── PROJECT_MAP.md             # This file — workspace index
├── .env                       # API keys (gitignored)
│
├── context/                   # Who Kellen is, rules, priorities
│   ├── me.md                  #   Personal context
│   ├── work.md                #   Work environment
│   ├── team.md                #   Team members
│   ├── current_priorities.md  #   Active goals & priorities
│   └── rules.md               #   Communication & operating rules
│
├── .claude/skills/            # Auto-discovered skills (invocable via /skill-name)
│   ├── 2d-activity/           #   Canvas/SVG interactive activities
│   ├── 3d-activity/           #   Babylon.js 3D simulations
│   ├── agent-creator/         #   Create & audit sub-agents
│   ├── context-sync/          #   Weekly context maintenance
│   ├── create-assessment/     #   Build quizzes & assessments
│   ├── crime-scene-generator/ #   Forensic crime scene scenarios
│   ├── dev-pipeline/          #   Bug fix & feature development
│   ├── game-balance/          #   RPG gamification economy tuning
│   ├── generate-image/        #   Image prompt generation
│   ├── generate-questions/    #   Question bank generation
│   ├── lesson-plan/           #   ISLE physics lesson planning
│   ├── local-llm/             #   Delegate tasks to local Ollama LLM
│   ├── slide-deck/            #   Reveal.js presentation generation
│   └── study-guide/           #   Student review material generation
│
├── agents/                    # Sub-agent definitions (Claude Code subagents)
│   ├── portal-orchestrator.md #   Coordinates multi-agent Portal work
│   ├── 3d-graphics-engineer.md
│   ├── backend-integration-engineer.md
│   ├── content-strategist-ux-writer.md
│   ├── data-analyst.md
│   ├── deployment-monitor.md
│   ├── economy-designer.md
│   ├── local-llm-assistant.md #   Local Ollama qwen3:14b sub-agent
│   ├── qa-bug-resolution.md
│   ├── ui-accessibility-engineer.md
│   └── memory/                #   Per-agent persistent memory
│
├── projects/
│   └── Porters-Portal/        #   Git submodule — the main project (gamified LMS)
│
├── assets/                    #   Reusable media library (see assets/DIRECTORY.md)
│   ├── Assessments/           #     Assessment content files
│   ├── audio/                 #     Sound effects & music (Kenney CC0)
│   ├── ImagePrompts/          #     Image generation prompts & outputs
│   ├── models/                #     3D models (Kenney, Quaternius CC0)
│   ├── Presentations/         #     Slide decks
│   ├── Questions/             #     Question banks
│   ├── Simulations/           #     Interactive HTML simulations
│   ├── textbook PDF/          #     Course textbook PDFs
│   ├── favorited html content/#     Saved interactive content
│   ├── textures/              #     Tileable textures
│   └── ui/                    #     Sprites, icons, UI elements
│
├── tools/                     #   Local tooling scripts
│   └── local-agent.py         #     Ollama agent with tool access (read/write/grep/bash)
│
├── decisions/                 #   Decision log (dated entries)
├── references/                #   SOPs, reference docs
│   └── portal-bridge.md       #     Portal data bridge reference
├── templates/                 #   Reusable formats
│   └── skill-template.md      #     Canonical skill format
└── prototypes/                #   HTML prototypes (avatar textures)
```

## Key Paths

| What | Path |
|------|------|
| Operating instructions | `CLAUDE.md` |
| Active project | `projects/Porters-Portal/` (git submodule) |
| Skills (canonical) | `.claude/skills/` |
| Agent definitions | `agents/` |
| Asset library index | `assets/DIRECTORY.md` |
| Local LLM API | `http://localhost:11434` (Ollama, qwen3:14b) |

## Local Infrastructure

- **Ollama** running as systemd service with ROCm (AMD GPU)
- **Model:** qwen3:14b on Radeon 7900 XTX (24GB VRAM)
- Invoke via `/local-llm` skill or direct API calls

## For LLMs Reading This

- Start with `CLAUDE.md` for behavioral rules, then `context/` for who you're working for
- Skills in `.claude/skills/` are auto-discovered — each has a `SKILL.md` with instructions
- Agent definitions in `agents/` describe specialized workers you can delegate to
- The `assets/DIRECTORY.md` file indexes all available media — read it before creating new assets
- `decisions/` contains past architectural decisions — check before revisiting settled questions
