# Current Priorities & Goals

## Priority 1: Porter's Portal Stability
All stability work completed as of 2026-03-10. Full audit history archived in `decisions/completed-milestones.md`.
- Student work persistence, 4 stability audit rounds, chat security, Firestore rules audit, error boundaries — all complete
- No outstanding stability issues

## Priority 2: Porter's Portal UI/UX & Quality of Life
- **Admin experience** — grading workflows, lesson authoring efficiency, analytics clarity
- **Student experience** — responsive design, accessibility, intuitive navigation, performance
- Recent work: collapsible sidebar, mobile bottom nav, keyboard shortcuts, breadcrumbs, post-submission review mode
- Gamification polish (Flux Shop, cosmetics, boss fights, dungeons, PvP arena)
- UI/UX rounds 1-9 completed (2026-03-10 through 2026-03-11). Full round history archived in `decisions/completed-milestones.md`.
- **Remaining (round 10+):** deeper color contrast sweep (remaining `text-gray-300/400/500` on dark), InlineBlockEditor form labels (`htmlFor`/`id` pairing ~30 inputs), touch target sizing (icon buttons `p-1`/`p-1.5` → 44px min), virtualization (DungeonPanel, FluxShop, inventory grids), early warning intervention UI, seasonal rewards wiring, spectate mode, skill synergy viz

## Priority 3: Executive Assistant & Agent Team Enhancement
- **14 general agents** in `agents/`, project-specific agents in `projects/<name>/.agents/`
- **26 skills** in `.claude/skills/` — dev-pipeline is project-agnostic with Backward Design
- Agent memory in `agents/memory/` — cross-project institutional knowledge
- Teaching automation tools (grading assistant, lesson plans, parent comms, behavior referrals)
- Trigger skills for new agents: `/rubric-audit`, `/perf-audit`, `/changelog`
- Full assessment lifecycle + skill-to-agent mapping documented in `agents/ROUTING.md`
- **Two audit rounds completed (2026-03-12):** Round 1 added 6 agents, 4 skills, 3 tools, expanded ROUTING.md. Round 2 standardized all agent structures, added error handling to skills, wired orphaned tools, fixed deploy delegation (→ release-engineer), added QA-before-user in create-assessment.

## Priority 4: Gemini Executive Assistant for Teachers
- **Goal:** Distributable WAT-based EA powered by Gemini CLI for other teachers
- **Location:** `projects/Gemini Assistant/`
- **Architecture:** Web chat UI (FastAPI + vanilla HTML) that acts as a thin shell over Gemini CLI subprocess
- **Key decision:** Frontend pipes user input to `gemini` CLI process stdin, streams stdout back. CLI handles all auth (Google account OAuth or API key), tool calling, agent delegation, and file operations natively. No SDK, no custom auth code.
- **Status (2026-03-13):** WAT structure complete (GEMINI.md, 8 agents, 13 workflows, context templates, memory system). Web UI built and styled. Backend needs rewrite from SDK-based (`google-genai`) to CLI-proxy architecture (`gemini` subprocess). Current SDK approach can't use Gemini CLI's OAuth tokens.
- **Next step:** Rewrite `app/gemini_client.py` to spawn `gemini` as a PTY subprocess, pipe messages to stdin, parse/stream stdout back. Remove `tools.py` (CLI has native tools). Simplify `requirements.txt`.

## Porter's Portal Reference
- Path: `/home/kp/Desktop/Executive Assistant/projects/Porters-Portal` (git submodule)
- Core goals: ZPD-calibrated tasks, social constructivism, ISLE pedagogy, gamification, differentiation
- **On hold:** 3D avatar system (`ENABLE_3D_AVATAR = false`) — blocked on visual quality
- **Completed:** 3D asset pipeline Phase 1+2, assessment security/analytics, lesson block richness (21 types), chat feature

## Guiding Principles
- Social constructivism: students build understanding collaboratively
- ISLE framework: observe, explain, predict, test, revise
- ZPD-focused: meet students where they are
- Reduce teacher admin burden so more time goes to actual teaching
