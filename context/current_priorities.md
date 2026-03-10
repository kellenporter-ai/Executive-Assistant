# Current Priorities & Goals

## Primary Initiative: Automate Teaching Overhead
- **Grading classwork** — AI grading assistant implemented (`tools/grade-assistant.py`): pulls ungraded submissions from Firestore, pre-fills rubric tiers via Ollama qwen3:14b, teacher reviews before finalizing. Self-improving via teacher correction feedback loop. Desktop-only (Ollama required).
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
  - **3D avatar system** — **ON HOLD** (`ENABLE_3D_AVATAR = false`). Switched from Quaternius to KayKit Adventurers (6 models). PBR→StandardMaterial conversion, mesh-name tinting, idle animations all working. Blocked on visual quality Kellen isn't satisfied with. Students with stale `selectedCharacterModel` (old Quaternius IDs) need migration before re-enabling.
  - **Simulation development** — Babylon.js 3D activities and 2D interactive activities for physics and forensic science; 3D rendering optimizations applied (Thin Instances, GreasedLine, static mesh freezing, LOD)
  - **3D asset pipeline** — Phase 1 complete (external glTF loading via Babylon.js SceneLoader); **Phase 2 complete** (meshoptimizer compression via gltf-transform — 51% file size reduction across all character models; originals backed up to `.originals/`); roadmap in `decisions/asset-pipeline-roadmap.md`
  - **Grading UX** — side-by-side rubric grading, academic integrity analysis, AI-flagged submission handling; AI-suggested grade badges with per-skill rationale + confidence; teacher correction feedback loop for self-improvement
  - **Lesson block richness** — DrawingBlock (canvas drawing, vector precision editor, layers, snap guides, multi-vector types), MATH_RESPONSE (natural math input, Given/Find lists), BAR_CHART (full LOL chart); all added to palette, grading view, and progress counter
  - **Student UI/UX** — collapsible sidebar (icon-only mode), mobile bottom nav bar, keyboard shortcuts (j/k scroll, ? help), accessibility + breadcrumb improvements

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
