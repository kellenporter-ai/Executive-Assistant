# Team

## Orchestrator
- **Claude Code EA** (Opus 4.6) — routes tasks, makes architectural decisions, synthesizes discourse results

## Claude Code Peer Agents
These are the agents you collaborate with during discourse. You may receive their reports or work the same task in parallel:

| Agent | Domain |
|-------|--------|
| **qa-engineer** | Auditing, testing, security, a11y, spec verification |
| **backend-engineer** | APIs, databases, Cloud Functions, auth, security rules |
| **ui-engineer** | Frontend components, styling, responsive design, a11y |
| **graphics-engineer** | Babylon.js, SVG, Canvas, animations, visual effects |
| **content-writer** | UI copy, instructional text, user-facing language |
| **assessment-designer** | Rubrics, question strategy, difficulty tiering |
| **curriculum-designer** | Learning outcomes, standards alignment, unit sequencing |
| **performance-engineer** | Bundle analysis, render profiling, query optimization |
| **technical-writer** | API docs, changelogs, migration guides |
| **data-analyst** | Metrics, engagement reports, risk identification |
| **release-engineer** | Deploy planning, sequencing, execution, rollback |
| **deployment-monitor** | Post-deploy health checks, log analysis |
| **localization-coordinator** | English/Spanish translation, bilingual review |
| **local-llm-assistant** | Drafting, summarizing, boilerplate (Qwen3 14B) |

## Your Sub-Agents
You have 13 specialist agents in `.gemini/agents/` that you can delegate to:
- ui-engineer, backend-engineer, graphics-engineer, qa-engineer
- assessment-designer, curriculum-designer, content-writer, technical-writer
- data-analyst, email-agent, research-agent, performance-engineer, deployment-monitor

When the EA asks you to target a specific agent (e.g., "run QA"), delegate to your corresponding sub-agent for specialized work.
