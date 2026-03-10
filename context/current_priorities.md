# Current Priorities & Goals

## Priority 1: Porter's Portal Stability
- Bug fixes, error handling, data integrity
- Chat security hardening (completed 2026-03-09: Cloud Function message creation, server-side mute/moderation/enrollment validation)
- Firestore rules auditing
- Edge case handling (network failures, stale state, race conditions)
- `FeatureErrorBoundary` coverage on all dashboard tabs

## Priority 2: Porter's Portal UI/UX & Quality of Life
- **Admin experience** — grading workflows, lesson authoring efficiency, analytics clarity
- **Student experience** — responsive design, accessibility, intuitive navigation, performance
- Recent work: collapsible sidebar, mobile bottom nav, keyboard shortcuts, breadcrumbs, post-submission review mode
- Gamification polish (Flux Shop, cosmetics, boss fights, dungeons, PvP arena)

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
