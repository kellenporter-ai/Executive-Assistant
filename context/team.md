# Key Team Members

| Name | Role | Notes |
|------|------|-------|
| Joyce Macaraeg Porter | ESL Teacher | Kellen's wife; colleague at PAHS |
| Moises Ramos | Mathematics Teacher | Collaborator |
| Lucas McCarthy | Physics Teacher / Intro to AI Teacher | Collaborator |
| Jinny DeJesus | Department Head | Direct supervisor |
| Karla Garcia | Principal | School administration |
| Raquel Estremera | Principal | School administration |

## AI Agent Team
General agents in `agents/` — project-specialized via `projects/<name>/.agents/`.

| Agent | Role | Notes |
|-------|------|-------|
| ui-engineer | Frontend + accessibility | WCAG compliance, responsive design |
| backend-engineer | Server-side logic | APIs, databases, security rules |
| qa-engineer | Quality gatekeeper | Reports bugs, does not fix; audits before deploy |
| content-writer | UX copy + content | User-facing text, instructional content |
| data-analyst | Analytics + reports | Engagement, metrics, risk identification |
| graphics-engineer | Visual rendering | 3D/SVG, effects, animations |
| deployment-monitor | Post-deploy QA | Health checks, log review |
| local-llm-assistant | Local LLM delegation | Ollama qwen3:14b for simple tasks |
| assessment-designer | Assessment + rubric design | ISLE-aligned assessments, rubric neutrality |
| technical-writer | Docs + changelogs | Release notes, architecture docs |
| performance-engineer | Perf audits + optimization | Bundle size, Core Web Vitals, Chromebook perf |
| curriculum-designer | Lesson + unit design | ISLE methodology, Backward Design |
| localization-coordinator | Bilingual content | English/Spanish, equity-centered |
| release-engineer | Deploy orchestration | Ordering, pre-deploy gates, rollback |
| gemini-assistant | Gemini system coordinator | Invokes Gemini CLI via bridge tool; parallel discourse QA and cross-model synthesis |

**Portal-only:** `economy-designer` lives in `projects/Porters-Portal/.agents/` (no general counterpart).
**Gemini sub-agents:** 13 specialists in `projects/Gemini Assistant/.gemini/agents/` (mirror of Claude agent roster).
**Orchestration:** EA handles directly — no separate orchestrator agent.
