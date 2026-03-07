# Joyce ESL Practice Activities

Standalone HTML practice activities for 6th-8th grade ESL students (Level 1, varying abilities).

## Project Overview

- **Teacher:** Joyce Porter — ESL, South River middle school
- **Students:** 6th-8th graders, Level 1 ESL, widely varying prior education
- **Goal:** Long, continued adaptive practice — not one-time activities
- **Output:** Single self-contained HTML files (no server, no build step)
- **Style:** Middle school energy geared towards boys — bold colors, strong contrasts, competitive/game feel

## Building Activities

### Output Location

Save all activities to: `projects/joyce-esl/activities/`

### Technical Rules

1. **Single HTML file** — all CSS, JS, and content inline. No external dependencies except browser speech synthesis API (for listening activities).
2. **Vanilla JS only** — no frameworks, no jQuery, no CDNs.
3. **localStorage for persistence** — each activity uses a unique key prefix (e.g., `esl-vocab-match`) to store progress across sessions.
4. **No L1 translations** — English only at all difficulty tiers.

### Adaptive Engine

Every activity MUST include the adaptive engine. Copy the pattern from `shared/adaptive-engine.js` into each HTML file's `<script>` block.

**How it works:**

- Questions are organized into difficulty tiers (1-5):
  - **Tier 1:** High-frequency sight words, simple present, basic nouns/verbs
  - **Tier 2:** Common phrases, subject-verb agreement, everyday vocabulary
  - **Tier 3:** Compound sentences, irregular verbs, academic vocabulary
  - **Tier 4:** Complex grammar, idiomatic expressions, multi-step tasks
  - **Tier 5:** Near-fluent challenges, nuance, inference
- Student starts at Tier 1
- **Promote:** 4 correct in a row → move up one tier
- **Demote:** 2 incorrect in a row → move down one tier (floor: Tier 1)
- Tier, streak, and lifetime stats persist in localStorage
- Each tier has a deep question bank (20+ items minimum) so students don't see repeats quickly
- Questions within a tier are shuffled; once all are seen, reshuffle

### Visual Theme

- **Background:** Dark charcoal (#1a1a2e) to deep navy (#16213e)
- **Cards/panels:** Semi-transparent with subtle glow — `rgba(255,255,255,0.05)` bg, `1px solid rgba(255,255,255,0.1)` border
- **Primary accent:** Electric blue (#00d4ff)
- **Success:** Neon green (#00ff88)
- **Error:** Hot red (#ff3366)
- **Text:** White (#ffffff) with muted hints in (#8899aa)
- **Font:** System sans-serif stack, bold headings
- **Correct feedback:** Brief flash animation + score increment + encouraging short phrase
- **Wrong feedback:** Shake animation + show correct answer briefly
- **Progress bar:** XP-style bar showing progress within current tier
- **Tier badge:** Visible indicator of current level (Tier 1-5 with labels like "Rookie", "Pro", "Legend", etc.)
- **Streak counter:** Visible fire/streak counter for consecutive correct answers
- **Minimum touch targets:** 48px for mobile/tablet use

### Tier Labels

| Tier | Label |
|------|-------|
| 1 | Rookie |
| 2 | Starter |
| 3 | Pro |
| 4 | All-Star |
| 5 | Legend |

### Activity Types

1. **Vocabulary Match** — Match words to images/definitions. Tap-to-select matching pairs.
2. **Sentence Builder** — Drag words into correct sentence order. Sentences grow longer/complex at higher tiers.
3. **Fill-in-the-Blank** — Cloze exercises with multiple choice options. Grammar and vocabulary.
4. **Listening Comprehension** — Browser speech synthesis reads a word/sentence, student picks the correct written form or answers a question.

### Content Requirements

- **Accuracy:** All grammar, vocabulary, and definitions must be correct.
- **Age-appropriate:** Content should be relevant and interesting for middle school boys.
- **Volume:** Each tier needs 20+ unique items minimum. More is better — students will use these repeatedly.
- **No cultural assumptions:** Students come from diverse backgrounds with gaps in prior education.

### Accessibility

- All interactive elements keyboard-accessible
- Visible focus indicators
- `aria-label` on interactive elements
- Color is never the only indicator (pair with icons/text)
- `prefers-reduced-motion` respected

### File Naming

Use descriptive kebab-case: `vocabulary-match.html`, `sentence-builder.html`, `fill-in-the-blank.html`, `listening-comprehension.html`
