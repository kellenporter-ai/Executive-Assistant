# Current Priorities & Goals

## Priority 1: Porter's Portal Stability
- **Student work persistence (completed 2026-03-10):** Save retry + backoff, 800ms debounce, sessionStorage crash buffer, save status HUD, 2-hour draft guard, denial cache on login, grace period cleanup, submission retry, multi-tab warning
- Stability audit round 2 (completed 2026-03-10): admin auth via custom claims (4 functions fixed), chat rate limiting + HTML sanitization, unbounded query limits, bare setTimeout cleanup, console.error→reportError sweep, notification error handling, Proctor mousemove throttle, boss HP scan scoping, enrollment validation on assessments, resilientSnapshot map bounds
- Stability audit round 3 (completed 2026-03-10): paginated 10 unbounded Cloud Function queries, onSnapshot error callback (App.tsx), ArenaPanel subscription cleanup, BossEncounterPanel leaderboard memoization, AdjustXPModal bulk error handling, FortuneWheel timer cleanup, IdleMissionsPanel countdown memoization, ResourceViewer history guard + submission retry, dataService existence check, warning toast type
- Stability audit round 4 (completed 2026-03-10): ConnectionStatus setTimeout leak, Proctor handleReplayClick mountedRef guard, AdjustXPModal bulk Promise.allSettled mountedRef guard. Full 100-file audit confirmed no remaining timer/async/listener leaks.
- Chat real-time bug (completed 2026-03-10)
- Chat security hardening (completed 2026-03-09)
- Firestore rules audit (completed 2026-03-09)
- Error boundaries, edge cases, async error handling (completed 2026-03-09)

## Priority 2: Porter's Portal UI/UX & Quality of Life
- **Admin experience** — grading workflows, lesson authoring efficiency, analytics clarity
- **Student experience** — responsive design, accessibility, intuitive navigation, performance
- Recent work: collapsible sidebar, mobile bottom nav, keyboard shortcuts, breadcrumbs, post-submission review mode
- Gamification polish (Flux Shop, cosmetics, boss fights, dungeons, PvP arena)
- UI/UX round 1 (completed 2026-03-10): virtualizer measureElement on 4 components, lazy-load DrawingBlock/MathResponseBlock, lesson editor Firestore auto-save (10s debounce), drag-and-drop block reordering (@dnd-kit/sortable)
- **Uncommitted changes in Portal:** ResourceViewer.tsx (submitFailed escape hatch), functions/src/index.ts (buildDailyDigest refactor), lib/firebase.ts (callTriggerDailyDigest) — from previous session, need review before committing

## Priority 3: Executive Assistant & Agent Team Enhancement
- Improve skills, agents, and workflows to increase EA effectiveness
- 8 general agents in `agents/`, project-specific agents in `projects/<name>/.agents/`
- Skills in `.claude/skills/` — dev-pipeline is project-agnostic with Backward Design
- Agent memory in `agents/memory/` — cross-project institutional knowledge
- Teaching automation tools (grading assistant, lesson plans, parent comms, behavior referrals)

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
