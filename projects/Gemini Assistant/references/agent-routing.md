# Agent Routing Guide

Quick reference for the EA to decide which agent handles a task.

## Agent Roster

| Agent | Model | Domain | Does NOT Handle |
|-------|-------|--------|-----------------|
| **ui-engineer** | gemini-2.5-pro | Components, styling, responsive, a11y | Server logic, 3D/WebGL |
| **backend-engineer** | gemini-2.5-pro | APIs, database, auth, security rules, cloud functions | Frontend components, visual design |
| **qa-engineer** | gemini-2.5-flash | Testing, security audit, a11y audit, spec verification | Fixing bugs (reports only) |
| **content-writer** | gemini-2.5-flash | User-facing copy, UI text, emails, instructional content | Code changes, data analysis |
| **data-analyst** | gemini-2.5-flash | Metrics, trends, risk identification, data processing | Implementing features (read-only) |
| **technical-writer** | gemini-2.5-flash | API docs, changelogs, architecture docs, decision logs | User-facing copy, code changes |
| **performance-engineer** | gemini-2.5-flash | Profiling, bundle size, query optimization, load budgets | Feature implementation |
| **deployment-monitor** | gemini-2.5-flash | Post-deploy health checks, log analysis, smoke tests | Fixing issues (monitor-only) |

## Routing Rules

### By Task Type
| Task | Agent |
|------|-------|
| Build a UI component | ui-engineer |
| Fix a visual bug | ui-engineer |
| Create an API endpoint | backend-engineer |
| Fix a security vulnerability | backend-engineer |
| Write unit tests | qa-engineer (audit) or the relevant engineer (if building tests) |
| Draft an email or announcement | content-writer |
| Analyze usage metrics | data-analyst |
| Write API documentation | technical-writer |
| Investigate slow page loads | performance-engineer |
| Verify a deployment succeeded | deployment-monitor |

### Boundary Resolution
When a task could belong to multiple agents:
- **"Button styling"** → ui-engineer (visual)
- **"Button click handler that calls API"** → ui-engineer (frontend) + backend-engineer (API) — split the task
- **"Error message text"** → content-writer (copy) — ui-engineer only if it involves layout/display
- **"Why is the page slow?"** → performance-engineer (diagnosis) — then the relevant engineer for the fix

## Multi-Agent Coordination

Common sequences for complex tasks:

1. **New feature:** backend-engineer (API) → ui-engineer (UI) → qa-engineer (audit)
2. **Performance fix:** performance-engineer (profile) → relevant engineer (fix) → qa-engineer (regression check)
3. **Documentation update:** relevant engineer (implementation) → technical-writer (docs) → qa-engineer (accuracy check)
4. **Content creation:** content-writer (draft) → qa-engineer (review) → relevant agent (implement)

## Adding New Agents

When the agent roster grows, update this file:
1. Add the agent to the roster table
2. Define boundary ownership with existing agents
3. Add to relevant coordination sequences
4. Run the agent-creator workflow for a full audit
