# Current Priorities & Goals

## Primary Initiative: Automate Teaching Overhead
- **Grading classwork** — largely completion-based, should be automatable
- **Writing lesson plans** — AI-assisted generation aligned to ISLE pedagogy
- **Parent communication** — automated updates on student progress in the parent's language of choice
- **Behavior referrals** — streamlined writing of student misbehavior documentation

## Porter's Portal (`/home/kp/Desktop/Executive Assistant/projects/Porters-Portal`)
- Interactive student-facing platform managed under Executive Assistant (git submodule)
- Goals:
  - Students engage with materials and receive feedback
  - Tasks calibrated to each student's zone of proximal development (ZPD)
  - Every student experiences success
  - Students construct knowledge first, then name concepts once understood
  - Gamification to drive participation and motivation
  - Differentiated learning for varied learning styles and abilities
- Recent focus areas (as of March 2026):
  - **Assessment security** — server-side telemetry validation, session tokens, anti-cheat measures
  - **Gamification expansion** — Flux Shop, cosmetics (auras, particles, frames, trails), boss fights, dungeons, PvP arena
  - **Simulation development** — Babylon.js 3D activities and 2D interactive activities for physics and forensic science
  - **Grading UX** — side-by-side rubric grading, academic integrity analysis, AI-flagged submission handling

## AI Agent Team
- 9 specialized agents managed from `agents/` in the Executive Assistant repo
- Agents: portal-orchestrator, ui-accessibility-engineer, backend-integration-engineer, qa-bug-resolution, content-strategist-ux-writer, data-analyst, economy-designer, deployment-monitor, 3d-graphics-engineer
- Agent memory stored in `agents/memory/` — captures patterns, bugs, architecture decisions
- 14 skills in `skills/` — dev-pipeline, create-assessment, slide-deck, 3d-activity, 2d-activity, crime-scene-generator, and more
- Leverage cheaper/faster models for sub-agent tasks

## Guiding Principles
- Social constructivism: students build understanding collaboratively
- ISLE framework: observe, explain, predict, test, revise
- ZPD-focused: meet students where they are
- Reduce teacher admin burden so more time goes to actual teaching
