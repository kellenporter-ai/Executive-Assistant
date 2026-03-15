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
- **A11y sweeps completed (2026-03-15):** LessonBlocks (15 fixes), StudentDashboard+HomeTab (23 fixes), TeacherDashboard (13 fix categories). Landmarks, focus management, tab ARIA, form labels, target sizes, contrast, reduced motion all addressed on key pages.
- **Remaining (round 10+):** InlineBlockEditor form labels (`htmlFor`/`id` pairing ~30 inputs), virtualization (DungeonPanel, FluxShop, inventory grids), early warning intervention UI, seasonal rewards wiring, spectate mode, skill synergy viz

## Priority 3: Executive Assistant & Agent Team Enhancement
- **15 general agents** in `agents/`, project-specific agents in `projects/<name>/.agents/`
- **28 skills** in `.claude/skills/` — dev-pipeline is project-agnostic with Backward Design
- Agent memory in `agents/memory/` — cross-project institutional knowledge
- Teaching automation tools (grading assistant, lesson plans, parent comms, behavior referrals)
- Trigger skills for new agents: `/rubric-audit`, `/perf-audit`, `/changelog`
- Full assessment lifecycle + skill-to-agent mapping documented in `agents/ROUTING.md`
- **Two audit rounds completed (2026-03-12):** Round 1 added 6 agents, 4 skills, 3 tools, expanded ROUTING.md. Round 2 standardized all agent structures, added error handling to skills, wired orphaned tools, fixed deploy delegation (→ release-engineer), added QA-before-user in create-assessment.
- **Architecture discourse audit (2026-03-15):** 10 action items executed — SHARED.md split, trigger sharpening, `/student-lookup` skill, Gemini routing entries, forensic science support, context-sync vs daily-briefing differentiation.

## Priority 4: Gemini Integration (Discourse Agent + Shared Distribution)

**Two versions (as of 2026-03-15):**

- **Non-shared** (`projects/Gemini Assistant/`): Headless discourse agent in the Claude Code dev-pipeline. No web UI. Invoked via `tools/gemini-bridge.py`. Works as a peer to Claude Code agents — parallel QA audits, second-opinion analysis, cross-model synthesis via `/discourse` skill. Context files populated with discourse agent identity.
- **Shared** (`projects/Gemini Assistant (Shared)/`): Full web app (FastAPI + chat UI) for distribution to other teachers. Context files are empty templates — context-agnostic, ready for any teacher to set up.
- **Learning flow:** Non-shared accumulates learnings → context-agnostic entries propagate to Shared version via `/remember` and `/context-sync`.
- **Auto-fallback (2026-03-15):** Both versions now auto-scale down models (3.1→2.5 Pro→2.5 Flash) on exhaustion or timeout. 15-min cooldowns, `--status` to check. Shared version also has `/api/model-status` endpoint.
- **Discourse tested and proven:** 4 practical tests completed — code review, architecture audit, 2 a11y sweeps. All produced stronger outcomes than either model alone.
- **Next step:** User testing of the Shared version with a colleague (full setup flow from scratch).

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
