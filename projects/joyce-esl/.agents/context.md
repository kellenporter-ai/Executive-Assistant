# Joyce ESL — Project Context

## Overview
Standalone HTML practice activities for 6th-8th grade ESL students (Level 1, varying abilities and prior education). Long, continued adaptive practice — not one-time activities.

## Audience
- **Teacher:** Joyce Porter — ESL, South River middle school
- **Students:** 6th-8th graders, Level 1 ESL, widely varying backgrounds
- **Devices:** School-issued laptops/tablets (assume limited connectivity)

## Tech Stack
- **Frontend:** Single self-contained HTML files (all CSS, JS, content inline)
- **JavaScript:** Vanilla ES6+ only — no frameworks, no CDN dependencies
- **Persistence:** localStorage with unique key prefixes per activity
- **Audio:** Browser speech synthesis API (for listening activities)
- **Backend:** None — no server, no build step, no deploy

## Build Commands
- None — files are standalone HTML

## Deploy Commands
- None — files are distributed directly to students/teachers

## Output Location
- Save activities to: `projects/joyce-esl/activities/`

## Key Architecture Patterns
- **Adaptive engine** in every activity (copy from `shared/adaptive-engine.js`)
- 5 difficulty tiers with promote (4 correct) / demote (2 incorrect) logic
- Each tier needs 20+ unique items (deep question banks, no quick repeats)
- Progress persists in localStorage across sessions

## Visual Theme
- Dark charcoal (#1a1a2e) to deep navy (#16213e) backgrounds
- Electric blue (#00d4ff) accent, neon green (#00ff88) success, hot red (#ff3366) error
- Bold, competitive, game-feel — geared toward middle school boys
- 48px minimum touch targets for tablet use

## Project-Specific QA Criteria
- English only — no L1 translations at any tier
- All grammar, vocabulary, and definitions must be correct
- Age-appropriate and culturally neutral content
- Keyboard accessible with visible focus indicators
- `prefers-reduced-motion` respected
- Each activity must include the adaptive engine
