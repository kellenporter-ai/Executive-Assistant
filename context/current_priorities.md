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
  - **Assessment security & analytics** — server-side telemetry validation, session tokens, anti-cheat; now tracking word count and words-per-second as behavioral integrity signals; 3-panel Google Classroom-style grading view
  - **Gamification expansion** — Flux Shop, cosmetics (auras, particles, frames, trails), boss fights, dungeons, PvP arena
  - **3D avatar system (active)** — replaced SVG OperativeAvatar with Babylon.js 3D character models using Quaternius GLB assets; 8 models (2 free, 3 standard/200 Flux, 3 premium/400 Flux); integrated with Flux Store economy; PBR→StandardMaterial conversion for Chromebook compatibility; **next: 3D model customization** (color tinting for skin/hair/clothing like the 2D system)
  - **Simulation development** — Babylon.js 3D activities and 2D interactive activities for physics and forensic science; 3D rendering optimizations applied (Thin Instances, GreasedLine, static mesh freezing, LOD)
  - **3D asset pipeline** — Phase 1 complete (external glTF loading via Babylon.js SceneLoader); roadmap in `decisions/asset-pipeline-roadmap.md`; Phase 2 (Meshoptimizer compression) next
  - **Grading UX** — side-by-side rubric grading, academic integrity analysis, AI-flagged submission handling

## AI Agent Team
- 9 specialized agents managed from `agents/` in the Executive Assistant repo
- Agents: portal-orchestrator, ui-accessibility-engineer, backend-integration-engineer, qa-bug-resolution, content-strategist-ux-writer, data-analyst, economy-designer, deployment-monitor, 3d-graphics-engineer
- Agent memory stored in `agents/memory/` — captures patterns, bugs, architecture decisions
- 13 skills in `.claude/skills/` — dev-pipeline, create-assessment, slide-deck, 3d-activity, 2d-activity, crime-scene-generator, context-sync, agent-creator, game-balance, generate-image, generate-questions, lesson-plan, study-guide
- Leverage cheaper/faster models for sub-agent tasks

## Guiding Principles
- Social constructivism: students build understanding collaboratively
- ISLE framework: observe, explain, predict, test, revise
- ZPD-focused: meet students where they are
- Reduce teacher admin burden so more time goes to actual teaching
