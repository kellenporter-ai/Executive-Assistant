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
| **assessment-designer** | Sonnet | Rubric architecture, question strategy, difficulty tiering, alignment audits, answer neutrality | JSON generation, UI, grading code |
| **technical-writer** | Sonnet | API docs, reference docs, migration guides, changelogs, decision logs | Student-facing copy, code changes, skill/agent defs |
| **performance-engineer** | Sonnet | Bundle analysis, render profiling, query optimization, load budgets, Core Web Vitals | Feature implementation, visual design, general QA |
| **curriculum-designer** | Sonnet | Learning outcomes, standards alignment (NGSS/AP), unit scope & sequence, prerequisite chains, ISLE cycle mapping | Assessment design, lesson JSON, student-facing content, code |
| **localization-coordinator** | Haiku | English↔Spanish translation, bilingual content review, terminology consistency, localization coverage audits | Original English content, i18n code, lesson block JSON, assessment design |
| **release-engineer** | Sonnet | Deploy planning, multi-target Firebase sequencing (indexes→rules→functions→hosting), rollback, pre-deploy gates | Post-deploy monitoring, writing features, QA, security rule authoring |
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
| "Design a rubric for the unit test" | assessment-designer | create-assessment skill |
| "Are these questions properly tiered?" | assessment-designer | qa-engineer |
| "Document the new API endpoints" | technical-writer | content-writer |
| "Write a migration guide for the schema change" | technical-writer | backend-engineer |
| "The dashboard is slow on Chromebooks" | performance-engineer | qa-engineer |
| "Analyze our bundle size" | performance-engineer | backend-engineer |
| "Audit this rubric for neutrality" | /rubric-audit → assessment-designer | qa-engineer |
| "Run a perf audit" | /perf-audit → performance-engineer | qa-engineer |
| "Generate a changelog" | /changelog → technical-writer | data-analyst |
| "What shipped this week?" | /changelog → technical-writer | deployment-monitor |
| "Map learning objectives to NGSS" | curriculum-designer | assessment-designer |
| "Build a unit scope and sequence" | curriculum-designer | lesson-plan skill |
| "What prerequisites do students need?" | curriculum-designer | content-writer |
| "Translate this parent letter to Spanish" | localization-coordinator | content-writer |
| "Check bilingual terminology consistency" | localization-coordinator | qa-engineer |
| "Deploy the latest changes" | release-engineer | deployment-monitor |
| "What order should we deploy?" | release-engineer | backend-engineer |
| "Roll back the last deploy" | release-engineer | deployment-monitor |

## Multi-Agent Coordination

Some tasks require multiple agents. Launch them in sequence:

1. **New game feature:** economy-designer (design) → backend-engineer (CF) → ui-engineer (UI) → qa-engineer (audit)
2. **New interactive block type:** ui-engineer (component) → backend-engineer (grading lists) → qa-engineer (4-place checklist)
3. **Visual upgrade:** graphics-engineer (effects) → ui-engineer (integration) → qa-engineer (perf audit)
4. **Content pipeline:** content-writer (copy) → ui-engineer (placement) → qa-engineer (a11y check)
5. **New assessment (full lifecycle):**
   - Design: assessment-designer (rubrics + question strategy) → content-writer (question wording review)
   - Build: /create-assessment (JSON generation) → qa-engineer (neutrality + ISLE audit)
   - Post-deploy: data-analyst (student performance analysis) → assessment-designer (calibration adjustments if needed)
6. **Assessment QA feedback loop:** If qa-engineer finds neutrality violations → route back to assessment-designer (not content-writer). Assessment-designer refines → content-writer adjusts wording if needed → re-submit to qa-engineer.
7. **Major feature ship:** engineering agents (build) → performance-engineer (perf audit) → technical-writer (docs) → qa-engineer (final gate)
8. **Performance fix:** performance-engineer (profile + fix) → qa-engineer (regression check)
9. **Documentation update:** technical-writer (draft) → qa-engineer (accuracy check)
10. **New curriculum unit:** curriculum-designer (objectives + sequence) → assessment-designer (rubrics for key objectives) → lesson-plan skill (lesson blocks) → content-writer (student materials) → localization-coordinator (Spanish versions)
11. **Production release:** release-engineer (plan + sequence + deploy) → deployment-monitor (health check) → technical-writer (changelog if major)
12. **Bilingual content pipeline:** content-writer (English original) → localization-coordinator (Spanish translation) → qa-engineer (verify pedagogical framing preserved)

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

### Assessment Content (Common Confusion)
- **assessment-designer**: Rubric design, question strategy, tier calibration, alignment audits. Owns the "what" and "how hard"
- **content-writer**: Question wording, instructional tone, student-facing language. Owns the "how it reads"
- **qa-engineer**: Rubric neutrality violations (if spotted during audit), spec compliance
- **/create-assessment skill**: JSON block generation from a design doc
- **/generate-questions skill**: Bulk question bank production
- **Handoff pattern**: assessment-designer produces design doc (objectives, tiers, question types) → content-writer reviews question stems for clarity and ELL accessibility → /create-assessment generates JSON → qa-engineer audits neutrality. If wording issues found, route to content-writer. If structural/tier issues found, route back to assessment-designer.

### Performance vs Quality (Common Confusion)
- **performance-engineer**: Measurable perf metrics (bundle size, LCP, query latency, memory), targeted optimizations
- **qa-engineer**: Broad code quality audits (security, a11y, spec compliance, dead code) — reports perf issues but doesn't profile or fix them
- **backend-engineer**: Query/index implementation when perf-engineer recommends schema changes

### Graphics + UI Integration (Common Confusion)
- **graphics-engineer**: SVG/3D rendering, animation, visual effects, material/shader tuning, avatar rendering, cosmetic item icon creation
- **ui-engineer**: Component placement, responsive sizing, dark theme integration, accessibility (alt text for meaningful graphics)
- **Handoff pattern**: graphics-engineer produces the visual asset (SVG, 3D model, animation). UI-engineer embeds it in the component with responsive sizing and a11y. Graphics-engineer validates responsive scaling before handoff — no back-and-forth needed for placement.

### Documentation (Common Confusion)
- **technical-writer**: Developer docs, API references, migration guides, changelogs, decision logs
- **content-writer**: Student/user-facing copy, tooltips, error messages, onboarding text
- **assessment-designer**: Rubric tier descriptions (pedagogical, not technical docs)

### Curriculum vs Assessment (Common Confusion)
- **curriculum-designer**: Learning outcomes, unit sequencing, standards alignment, prerequisite chains. Owns "what students learn and in what order"
- **assessment-designer**: Rubric design, question strategy, difficulty tiering, answer neutrality. Owns "how we measure what they learned"
- **Handoff pattern**: curriculum-designer produces learning objectives + sequence → assessment-designer selects which objectives need formal assessment and designs rubrics → content-writer reviews wording → /create-assessment generates JSON

### Deploy Pipeline (Common Confusion)
- **release-engineer**: Pre-deploy gates, deploy sequencing, execution, rollback. Owns everything from "ready to ship" through "deployed"
- **deployment-monitor**: Post-deploy health, log analysis, uptime verification. Takes over after release-engineer hands off
- **Handoff pattern**: release-engineer deploys → deployment-monitor watches. If health critical → release-engineer rolls back

### Localization (Common Confusion)
- **localization-coordinator**: Translation, bilingual review, terminology consistency, cultural adaptation
- **content-writer**: Original English content authoring. Writes first, localization-coordinator translates second
- **ui-engineer**: i18n code implementation (locale switching, string extraction) if ever needed

## Skill-to-Agent Mapping

Which skills delegate to which agents. Helps trace the full workflow when debugging.

| Skill | Primary Agent(s) | When |
|-------|-----------------|------|
| /dev-pipeline | All engineering agents, release-engineer, qa-engineer | Any feature/bug work |
| /create-assessment | assessment-designer, content-writer, qa-engineer | Building assessments |
| /rubric-audit | assessment-designer | Rubric quality checks |
| /perf-audit | performance-engineer | Performance measurement |
| /changelog | technical-writer | Release documentation |
| /generate-questions | assessment-designer (design), EA inline (generation) | Bulk question banks |
| /game-balance | economy-designer, data-analyst | Economy tuning |
| /lesson-plan | curriculum-designer (upstream objectives), content-writer (review) | ISLE lesson creation |
| /progress-report | data-analyst (data pull), EA inline (comments) | Parent reports |
| /sign-on | deployment-monitor (service checks) | Session start |
| /sign-off | EA inline (commit, push, memory) | Session end |
| /dependency-audit | EA inline (npm audit/outdated) | Pre-release dependency checks |
| /progress-report | localization-coordinator (Spanish comments if needed) | Bilingual parent reports |
