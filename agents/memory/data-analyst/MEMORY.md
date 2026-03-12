# Data Analyst Memory

## See Also
- `agents/memory/SHARED.md` — cross-cutting gotchas
- `projects/Porters-Portal/.agents/data-analyst.md` — portal-specific context
- `references/economy-reference.md` — economy constants

## Key Firestore Collections

### Users
- `gamification.xp` — global XP | `gamification.level` — 1-500
- `gamification.classXp` — per-class: `{ [classType]: number }`
- `gamification.currency` — Cyber-Flux (global)
- `gamification.streak` — engagement streak counter
- `enrolledClasses` — ClassType[] | `classSections` — `{ [classType]: section }`
- `stats.problemsCompleted`, `avgScore`, `rawAccuracy`, `totalTime`

### Submissions
- `metrics.engagementTime` — seconds (may be inflated by idle tabs)
- `metrics.pasteCount`, `keystrokes`, `clickCount`, `tabSwitchCount`
- `metrics.typingCadence` — `{ avgIntervalMs, burstCount }`
- `status` — FLAGGED | SUCCESS | SUPPORT_NEEDED | NORMAL | STARTED
- `score` — XP (classwork) or percentage (assessments)
- `isAssessment` — determines score semantics

### StudentBucketProfile (Daily at 6 AM EST)
- `bucket` — THRIVING | ON_TRACK | COASTING | SPRINTING | STRUGGLING | DISENGAGING | INACTIVE | COPYING
- `engagementScore` — z-score normalized to class mean
- `metrics.totalTime`, `submissionCount`, `totalClicks`, `totalPastes`, `totalKeystrokes`, `avgPasteRatio`, `activityDays`

### StudentAlert (6:30 AM EST)
- `alertType` — LOW_ENGAGEMENT | DECLINING_TREND | HIGH_PASTE_RATE | STRUGGLING
- `riskLevel` — CRITICAL | HIGH | MEDIUM | LOW

## Engagement Bucket Classification

Decision tree in `lib/telemetry.ts`:
1. **INACTIVE:** submissions=0 && totalTime < 60s
2. **COPYING:** pasteRatio > 0.4 && submissions >= 2 && pastes > 8
3. **STRUGGLING:** totalTime > 1800s && submissions >= 2 && totalXP < 50
4. **DISENGAGING:** zScore < -0.5 && activityDays <= 2 && submissions 1-3
5. **SPRINTING:** totalTime > 1800s && activityDays <= 2 && submissions >= 3
6. **COASTING:** zScore -0.5 to -1.5
7. **THRIVING:** zScore > 0.75 && submissions >= 4 && pasteRatio < 0.15 && activityDays >= 3
8. **ON_TRACK:** default

z-score: `(engagementScore - classMean) / classStdDev`
Window: 7 days rolling

## Auto-Classification Thresholds

| Status | Criteria |
|--------|----------|
| FLAGGED | pasteCount > 5 AND engagementTime < 300s |
| SUPPORT_NEEDED | keystrokes > 500 AND engagementTime > 1800s |
| SUCCESS | pasteCount === 0 AND keystrokes > 100 |
| NORMAL | default |

Thresholds overridable per class via ClassConfig.

## Data Quality Quirks

1. **AI-flagged scores = 0** — always exclude from avgScore calculations
2. **Inflated engagement time** — idle tabs inflate; cross-reference with keystrokes/clicks for real effort
3. **Missing fields** — old submissions may lack `isAssessment`
4. **No classType on submissions** — derive via assignment lookup
5. **Completion inflation** — retakes create multiple submissions; deduplicate by assignmentId
6. **Average score** — use best-per-assignment via `Map<assignmentId, maxScore>`
7. **STARTED included** — as of March 2026, shown in teacher dashboard
8. **RubricGrade** — uses `selectedTier` (0-4), AI uses `suggestedTier`
9. **`unflagSubmissionAsAI` bug** — does NOT restore score (stays 0)

## Query Bounds

- Submissions per assignment: 500
- Users: 500
- Leaderboard: 200
- All listeners use `resilientSnapshot` with auto-retry

## Analytics Components (Portal)

- **AnalyticsTab** — engagement trends, completion rates, XP distribution, engagement buckets
- **GamificationAnalyticsTab** — 8+ charts covering economy health
- **EndgameStatsModal** — per-question analytics, CSV export
- **StudentReports** — 6 sections, print-optimized
- Early warning bucket classification works but no intervention UI yet

## Parent Communication Rules

When generating reports for parents:
- NO portal jargon (XP, engagement buckets, gamification)
- THRIVING -> "consistently engaged" | ON_TRACK -> "meeting expectations"
- COASTING -> "doing the minimum" | SPRINTING -> "making a strong recent push"
- STRUGGLING -> "having difficulty keeping up" | DISENGAGING -> "losing engagement"
- INACTIVE -> "not participating"
