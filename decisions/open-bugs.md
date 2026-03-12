# Open Bug Registry

Centralized tracking of known bugs across Porter's Portal. Sourced from QA-engineer memory, SHARED.md, and session discoveries. Updated by `/remember` skill during memory sweeps.

**Last updated:** 2026-03-12

---

## MAJOR (Blocks features or causes data issues)

| # | Component | Bug | Root Cause | Fix Direction | Owner |
|---|-----------|-----|-----------|---------------|-------|
| 1 | `dataService.ts` | `equipCosmetic` silently fails — writes `gamification.activeCosmetic` which is NOT in Firestore student self-write allowlist | Client-side write to unallowed field | Move to Cloud Function (like `awardBehavior`) | backend-engineer |
| 2 | `unflagSubmissionAsAI` | Score stays 0 and status stays FLAGGED after unflagging | Function doesn't restore original score/status | Restore pre-flag score + set status to previous value | backend-engineer |
| 3 | `integrityAnalysis.ts` | `mcWrong` denominator counts union instead of intersection — produces false negatives | Logic error in set math | Fix to intersection of shared questions | backend-engineer |
| 4 | `integrityAnalysis.ts` | MC blocks with `correctAnswer: undefined` generate false positives | Missing null check | Guard against undefined correctAnswer | backend-engineer |
| 5 | `PhysicsTools.tsx` | Missing `onPointerCancel` — toolbar stuck in permanent drag on ChromeOS gesture interruptions | No cancel handler | Add pointercancel handler that snaps back + resets drag state | ui-engineer |
| 6 | `PhysicsTools.tsx` | No mount-time viewport clamp — position saved on large monitor restores off-screen on Chromebook | Position persisted without viewport bounds check | Clamp to viewport dimensions on mount | ui-engineer |
| 7 | Submission query | `existingSubmission` uses `limit(1)` without `orderBy` — may return stale flagged submission | Missing sort | Add `orderBy('submittedAt', 'desc')` before `limit(1)` | backend-engineer |

## MEDIUM (Degraded experience but has workarounds)

| # | Component | Bug | Fix Direction | Owner |
|---|-----------|-----|---------------|-------|
| 8 | `FluxShopPanel.tsx` | `handleEquipCosmetic` is fire-and-forget (no await/catch) — shows false success toast | Add await + try/catch + error toast | ui-engineer |
| 9 | `FluxShopPanel.tsx` | `purchaseFluxItem` writes `consumablePurchases` for `dailyLimit: 0` items — unbounded map growth | Skip write for unlimited items | backend-engineer |
| 10 | `FluxShopPanel.tsx` | Zero ARIA attributes on purchase buttons, no focus ring on item cards | Add aria-labels + focus-visible rings | ui-engineer |
| 11 | CSS | `scrollbar-hide` Tailwind class used but plugin not installed — no-op on non-Chrome | Install plugin or use CSS directly | ui-engineer |
| 12 | TeacherDashboard | FLAGGED status banner hidden when `showScoreOnSubmit === false` | Always show flagged banner regardless of score visibility setting | ui-engineer |
| 13 | LessonBlocks | `completedBlocks` Set not decremented on Edit — progress bar stays at 100% | Remove block from Set on edit action | ui-engineer |

## MINOR (Cosmetic or edge-case)

| # | Component | Bug | Owner |
|---|-----------|-----|-------|
| 14 | Notifications | AI_FLAGGED icon uses `text-red-400` instead of `text-purple-400` | ui-engineer |
| 15 | Stats | `avgScore` includes AI-flagged submissions (score:0), deflating average | data-analyst → backend-engineer |
| 16 | Stats cards | 4 cards in `md:grid-cols-3` — last card wraps alone | ui-engineer |
| 17 | Retake dialog | `handleRetake` confirm overstates remaining attempts by 1 | ui-engineer |
| 18 | Submission type | `needsReview` missing from submitAssessment return — "Pending Review" not shown immediately | backend-engineer |
| 19 | Status labels | `getStatusLabel` shows raw enum strings for non-flagged statuses | ui-engineer |
| 20 | NotificationBell | `expandedId` not reset on panel close | ui-engineer |
| 21 | Dead code | Results modal Exit button: `${!canRetake ? '' : ''}` — empty ternary | ui-engineer |

## Recurring Patterns (not bugs, but watch for)

- **Firestore self-write allowlist** (`firestore.rules` ~line 53-61): only 6 fields permitted under `gamification`. Any new client-side gamification write will silently fail. Always use Cloud Functions for new gamification fields.
- **Fire-and-forget async**: UI agent frequently omits `await`/`try-catch` on handlers, shows premature success toast. Check all equip/purchase/save handlers.
- **`consumablePurchases` map bloat**: Items with `dailyLimit: 0` should not write to this map.
- **`integrityAnalysis.ts` runs synchronously** on main thread — fine for <30 students, risky at 100+.

## Resolved (keep for reference, remove after 30 days)

- Multi-question room answer bleeding: fixed by adding questionId to useEffect dep array (2026-03-04)
- setTimeout cleanup: overlay + attack timers correctly guarded with refs + useEffect cleanup
- Section filter: all stats cards correctly use sectionFilteredSubs
