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
  - **3D avatar system** — replaced SVG OperativeAvatar with Babylon.js 3D character models using Quaternius GLB assets; 8 models (2 free, 3 standard/200 Flux, 3 premium/400 Flux); integrated with Flux Store economy; PBR→StandardMaterial conversion for Chromebook compatibility; **color customization complete** (skin tone, hair color, suit hue via gradient sliders; in-place material tinting; 16-tone palettes); **next: 3D hair styles** (requires Blender-created swappable hair mesh assets)
  - **Simulation development** — Babylon.js 3D activities and 2D interactive activities for physics and forensic science; 3D rendering optimizations applied (Thin Instances, GreasedLine, static mesh freezing, LOD)
  - **3D asset pipeline** — Phase 1 complete (external glTF loading via Babylon.js SceneLoader); **Phase 2 complete** (meshoptimizer compression via gltf-transform — 51% file size reduction across all character models; originals backed up to `.originals/`); roadmap in `decisions/asset-pipeline-roadmap.md`
  - **Grading UX** — side-by-side rubric grading, academic integrity analysis, AI-flagged submission handling

## AI Agent Team
- 8 general agents in `agents/`: ui-engineer, backend-engineer, qa-engineer, content-writer, data-analyst, graphics-engineer, deployment-monitor, local-llm-assistant
- Project-specific specializations in `projects/<name>/.agents/` (context.md + per-agent overrides)
- Portal-only agents: economy-designer (in `projects/Porters-Portal/.agents/`)
- EA handles orchestration directly — no separate orchestrator
- Agent memory in `agents/memory/` — cross-project institutional knowledge
- Skills in `.claude/skills/` — dev-pipeline is now project-agnostic with Backward Design

## Guiding Principles
- Social constructivism: students build understanding collaboratively
- ISLE framework: observe, explain, predict, test, revise
- ZPD-focused: meet students where they are
- Reduce teacher admin burden so more time goes to actual teaching
