# Agent Routing Guide

Quick reference for the EA to decide which agent handles a task.

## Agent Roster

| Agent | Model | Domain | Does NOT Handle |
|-------|-------|--------|-----------------|
| **ui-engineer** | gemini-2.5-pro | Components, styling, responsive, a11y | Server logic, 3D/WebGL, assessment design |
| **backend-engineer** | gemini-2.5-pro | APIs, database, auth, security rules, cloud functions | Frontend components, visual design, copy |
| **graphics-engineer** | gemini-2.5-pro | Canvas, SVG, Babylon.js, animations, visual effects, 3D scenes | UI layout, a11y, forms, data analysis |
| **assessment-designer** | gemini-2.5-pro | Rubric architecture, question strategy, difficulty tiering, answer neutrality, standards alignment | Question text writing, code generation, grading, curriculum planning |
| **qa-engineer** | gemini-2.5-flash | Testing, security audit, a11y audit, spec verification | Fixing bugs (reports only), writing tests |
| **content-writer** | gemini-2.5-flash | UI copy, tooltips, error messages, instructional content | Code changes, data analysis, email triage |
| **email-agent** | gemini-2.5-flash | Gmail triage, email drafting/sending, inbox management | Non-email copy, code, data analysis |
| **research-agent** | gemini-2.5-flash | Deep multi-source synthesis, competitive analysis, literature review | URL extraction (use web-research workflow), code implementation |
| **data-analyst** | gemini-2.5-flash | Metrics, trends, risk identification, data processing | Implementing features (read-only) |
| **technical-writer** | gemini-2.5-flash | API docs, changelogs, architecture docs, decision logs | User-facing copy, code changes |
| **performance-engineer** | gemini-2.5-flash | Profiling, bundle size, query optimization, load budgets | Feature implementation |
| **deployment-monitor** | gemini-2.5-flash | Post-deploy health checks, log analysis, smoke tests | Fixing issues (monitor-only) |
| **curriculum-designer** | gemini-2.5-pro | Learning objectives, standards alignment (NGSS/AP/CC), unit scope & sequence, prerequisite mapping, pacing | Lesson content, assessment items, code, grading |

## Routing Rules

### By Task Type

| Task | Route To | NOT |
|------|----------|-----|
| Build a UI component | ui-engineer | graphics-engineer |
| Fix a visual/layout bug | ui-engineer | graphics-engineer |
| Create an API endpoint | backend-engineer | ui-engineer |
| Fix a security vulnerability | backend-engineer | qa-engineer |
| Canvas/SVG rendering | graphics-engineer | ui-engineer |
| 3D simulation or Babylon.js scene | graphics-engineer | ui-engineer |
| Animation or visual effect | graphics-engineer | ui-engineer |
| Design a rubric | assessment-designer | content-writer |
| Audit rubric for neutrality | assessment-designer | qa-engineer |
| Calibrate assessment difficulty | assessment-designer | data-analyst |
| Align questions to standards | assessment-designer | content-writer |
| Write/refine question text | content-writer | assessment-designer |
| Write UI copy or tooltips | content-writer | email-agent |
| Draft an email | email-agent | content-writer |
| Triage inbox | email-agent | content-writer |
| Research a topic (synthesis) | research-agent | web-research workflow |
| Scrape a URL or convert a file | web-research workflow | research-agent |
| Audit code for bugs/security | qa-engineer | the engineer who wrote it |
| Analyze usage metrics | data-analyst | backend-engineer |
| Write API documentation | technical-writer | content-writer |
| Write a changelog | technical-writer | data-analyst |
| Investigate slow page loads | performance-engineer | qa-engineer |
| Verify a deployment succeeded | deployment-monitor | qa-engineer |
| Plan a unit scope and sequence | curriculum-designer | assessment-designer |
| Align objectives to standards (NGSS, AP, CC) | curriculum-designer | content-writer |
| Map prerequisites across units | curriculum-designer | data-analyst |
| Write learning objectives | curriculum-designer | content-writer |

### Boundary Resolution

When a task could belong to multiple agents:
- **"Button styling"** → ui-engineer (visual)
- **"Button click handler that calls API"** → ui-engineer (frontend) + backend-engineer (API) — split the task
- **"Error message text"** → content-writer (copy) — ui-engineer only if it involves layout/display
- **"Why is the page slow?"** → performance-engineer (diagnosis) — then the relevant engineer for the fix
- **"Interactive diagram for a lesson"** → graphics-engineer (rendering) — ui-engineer only if it needs form controls or layout integration
- **"Is this rubric fair?"** → assessment-designer (tier quality, neutrality, bias) — qa-engineer only if checking against a spec
- **"Draft a parent email about grades"** → email-agent (drafting + sending) — content-writer only if it's a template others will reuse

## Boundary Ownership

### Graphics + UI (Common Confusion)
- **graphics-engineer**: Canvas rendering, SVG drawing, Babylon.js scenes, animations, visual effects, data visualization rendering
- **ui-engineer**: Component layout, forms, responsive sizing, CSS, accessibility, keyboard navigation
- **Handoff pattern**: graphics-engineer produces the visual output. ui-engineer embeds it with responsive sizing and a11y attributes.

### Content + Email (Common Confusion)
- **content-writer**: User-facing copy that isn't email — tooltips, instructional text, error messages, UI labels
- **email-agent**: Everything Gmail — drafting, sending, triaging, summarizing email threads
- **Handoff pattern**: If email-agent needs polished copy for a template, content-writer drafts it. email-agent handles delivery.

### Assessment + Content (Common Confusion)
- **assessment-designer**: Rubric architecture, tier structure, question types, difficulty calibration, alignment audits, **answer neutrality**. Owns "what, how hard, and whether the rubric leaks answers."
- **content-writer**: Question wording, instructional tone, readability, ELL accessibility. Owns "how it reads."
- **qa-engineer**: Spec compliance and general quality — may flag neutrality issues during broad audits, but assessment-designer is the authority on neutrality.
- **Handoff pattern**: assessment-designer produces the structural design (objectives, tiers, question types) → content-writer reviews question stems for clarity → assessment-designer audits neutrality on final product.

### Curriculum + Assessment (Common Confusion)
- **curriculum-designer**: Learning outcomes, unit sequencing, standards alignment, prerequisite chains. Owns "what students learn and in what order."
- **assessment-designer**: Rubric design, question strategy, difficulty tiering, answer neutrality. Owns "how we measure what they learned."
- **Handoff pattern**: curriculum-designer produces learning objectives + sequence → assessment-designer selects which objectives need formal assessment and designs rubrics → content-writer reviews wording.

### Research Agent + Web Research Workflow (Common Confusion)
- **research-agent**: Multi-source synthesis requiring reasoning — "research the latest on formative assessment strategies"
- **web-research workflow**: Single-action extraction — "scrape this URL", "convert this PDF to Markdown", "find resources on topic X"

### Performance vs Quality (Common Confusion)
- **performance-engineer**: Measurable perf metrics (bundle size, LCP, query latency, memory), targeted optimizations
- **qa-engineer**: Broad quality audits (security, a11y, spec compliance) — reports perf issues but doesn't profile or fix

## Multi-Agent Coordination

Common sequences for complex tasks:

1. **New feature:** backend-engineer (API) → ui-engineer (UI) → qa-engineer (audit)
2. **Performance fix:** performance-engineer (profile) → relevant engineer (fix) → qa-engineer (regression check)
3. **Documentation update:** relevant engineer (implementation) → technical-writer (docs) → qa-engineer (accuracy check)
4. **Content creation:** content-writer (draft) → qa-engineer (review) → relevant agent (implement)
5. **Interactive activity:** graphics-engineer (rendering) → ui-engineer (controls/layout) → qa-engineer (accessibility check)
6. **Assessment pipeline:** assessment-designer (structure) → content-writer (question wording) → assessment-designer (neutrality audit)
7. **Email campaign:** content-writer (template copy) → email-agent (delivery) → data-analyst (open/response metrics)
8. **New curriculum unit:** curriculum-designer (objectives + sequence) → assessment-designer (rubrics for key objectives) → content-writer (student materials)

## Adding New Agents

When the agent roster grows, update this file:
1. Add the agent to the roster table
2. Define boundary ownership with existing agents
3. Add routing rules with NOT column
4. Add to relevant coordination sequences
5. Run the agent-creator workflow for a full audit
