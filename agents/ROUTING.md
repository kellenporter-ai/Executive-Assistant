# Agent Routing Guide

Quick reference for the EA to decide which agent handles a task.

## General Agents

| Agent | Model | Triggers On | Does NOT Handle |
|-------|-------|------------|-----------------|
| **ui-engineer** | Sonnet | Components, styling, responsive layout, a11y, Tailwind, React hooks | Server logic, 3D/SVG rendering, economy design |
| **backend-engineer** | Sonnet | Cloud Functions, Firestore rules, auth, APIs, database ops | Frontend components, visual effects, copy |
| **graphics-engineer** | Sonnet | Babylon.js, SVG avatars, animations, visual effects, 3D scenes | UI layout, a11y, economy tuning, form fields |
| **qa-engineer** | Sonnet | Auditing, testing, security, a11y compliance, spec verification | Fixing bugs (reports only), writing features |
| **content-writer** | Haiku | UI copy, tooltips, error messages, instructional text | Code changes, visual design, data analysis |
| **data-analyst** | Haiku | Metrics, engagement reports, risk identification, data queries | Implementing features, writing code |
| **deployment-monitor** | Haiku | Post-deploy health checks, log analysis, uptime verification | Fixing issues (reports only), pre-deploy work |
| **local-llm-assistant** | Qwen3 14B | Drafting, summarizing, reformatting, brainstorming, boilerplate | Complex reasoning, multi-step code, student-facing content |

## Project-Only Agents

| Agent | Project | Triggers On |
|-------|---------|------------|
| **economy-designer** | Porters-Portal | XP rates, loot tables, currency sinks, boss stats, ability effects, progression curves |

## Common Routing Decisions

| Task | Route To | NOT |
|------|----------|-----|
| "Add a button to the dashboard" | ui-engineer | graphics-engineer |
| "Boss fight animation" | graphics-engineer | ui-engineer |
| "New cosmetic item stats" | economy-designer → backend-engineer | ui-engineer |
| "Fix grading Cloud Function" | backend-engineer | data-analyst |
| "Check if deploy broke anything" | deployment-monitor | qa-engineer |
| "Audit for a11y violations" | qa-engineer | ui-engineer |
| "Write tooltip text for XP bar" | content-writer | ui-engineer |
| "Student engagement by class" | data-analyst | backend-engineer |
| "Draft an email to parents" | local-llm-assistant | content-writer |
| "New SVG hair style" | graphics-engineer | ui-engineer |
| "Equip cosmetic silently fails" | backend-engineer (Firestore rules) | ui-engineer |

## Multi-Agent Coordination

Some tasks require multiple agents. Launch them in sequence:

1. **New game feature:** economy-designer (design) → backend-engineer (CF) → ui-engineer (UI) → qa-engineer (audit)
2. **New interactive block type:** ui-engineer (component) → backend-engineer (grading lists) → qa-engineer (4-place checklist)
3. **Visual upgrade:** graphics-engineer (effects) → ui-engineer (integration) → qa-engineer (perf audit)
4. **Content pipeline:** content-writer (copy) → ui-engineer (placement) → qa-engineer (a11y check)

## Boundary Ownership

### Cosmetic Features (Common Confusion)
- **graphics-engineer**: Item icon rendering, color swatch visuals, preview animations, SVG/3D effects
- **ui-engineer**: Button layout, form fields, label placement, accessibility, responsive grid
- **economy-designer**: Cosmetic stats, rarity distribution, Flux costs, balance tuning
- **backend-engineer**: Server-side validation, Firestore rules, Cloud Functions, write allowlist

### Copy Quality
- **content-writer**: Tone, voice, word choice, instructional accuracy, ISLE alignment
- **qa-engineer**: Missing labels entirely (a11y defect), broken label text, spec violations
- **ui-engineer**: Label placement, font sizing, truncation, responsive text

### Data & Analytics
- **data-analyst**: Querying, aggregation, visualization recommendations, risk scoring
- **backend-engineer**: Cloud Function implementation of analytics pipelines
- **ui-engineer**: Chart components, dashboard layout, interactive filters
