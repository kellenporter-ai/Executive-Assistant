# Shared Agent Memory

Cross-cutting knowledge that applies to multiple agents. Any agent can read and append to this file. The `/remember` skill consolidates cross-agent learnings here.

## What Belongs Here

- **Project-wide conventions** — naming patterns, file structure rules, shared constants
- **Cross-cutting gotchas** — things that bit one agent and would bite another (e.g., Firestore field renames, API contract changes)
- **Environment facts** — hardware constraints (Chromebook 1366x768), browser targets, deployment quirks
- **Shared discoveries** — patterns confirmed across multiple agents or sessions

## What Does NOT Belong Here

- Agent-specific domain knowledge (goes in that agent's own MEMORY.md)
- Session-specific context (temporary, not durable)
- Anything already documented in `context/` files or `CLAUDE.md`

---

## Environment

- **Student hardware:** Chromebook, 1366x768 viewport, trackpad input, integrated GPU
- **Browser target:** Chrome (latest stable on ChromeOS)
- **Deploy target:** Firebase Hosting + Cloud Functions v2

## Portal Conventions

- All interactive HTML activities are single self-contained files (no external assets except approved CDNs)
- Proctor Bridge is mandatory for portal-embedded activities
- Dark theme CSS variables from `references/portal-bridge.md` are the standard
- 44px minimum touch targets on all interactive elements

## Web Research Pipeline

- **Tool:** `tools/web-research.py` — CLI with `search`, `extract`, `convert`, `research` commands
- **Skill:** `/web-research` — orchestrates the tool with WebSearch fallback
- **Extraction tiers:** Crawl4AI (local, unlimited) → Jina Reader (free proxy) → BeautifulSoup (static)
- **Discovery:** Serper API if `SERPER_API_KEY` is set in `.env`, otherwise WebSearch built-in
- **Document conversion:** MarkItDown (PDF/DOCX/PPTX → Markdown)
- **Output:** `temp/web-research/` (gitignored) — script prints file path to stdout
- **Run:** `tools/.venv/bin/python3 tools/web-research.py extract "URL"`

## Screenshot Tool

- **Tool:** `tools/screenshot/take.mjs` — headless Chromium screenshots via puppeteer-core
- **Setup:** `cd tools/screenshot && npm install` (one-time, installs puppeteer-core only)
- **Usage:** `node "/home/kp/Desktop/Executive Assistant/tools/screenshot/take.mjs" --url "http://..." --viewport 1366x768`
- **For local HTML files:** `node tools/screenshot/take.mjs --file "/path/to/file.html"`
- **Output:** `temp/screenshots/<timestamp>.png` — path printed to stdout, read with Read tool for visual analysis
- **Chromium:** Uses system Chromium at `/usr/bin/chromium` (no bundled browser)
- **Flags:** `--wait <ms>` (default 2000), `--full-page`, `--output <path>`

## LessonBlock Schema Additions (March 2026)

- `explanation?: string` — added to the `LessonBlock` type in `types.ts`. When present on an MC block, the explanation is shown in an info box after the student answers. The `lesson-plan` and `create-assessment` skills can set this field to provide post-answer context. All blocks without it are unaffected.

## Student UI Layout Patterns (March 2026)

- Sidebar: collapsible icon-only mode (`w-[76px]`), localStorage key `sidebar-collapsed`, defaults collapsed `< 1440px`
- Mobile bottom nav bar (Home/Resources/Missions/Progress) shows below `lg` breakpoint (1024px) — `pb-20 md:pb-20 lg:pb-8` on main content to avoid overlap
- Toast notifications are **top-center** (`fixed top-4 left-1/2 -translate-x-1/2`), not bottom-left
- Keyboard shortcuts active in lessons: `j`/`k` scroll blocks, `?` shows help overlay (only when no input focused)

## Content Generation Gotchas

- **AI-generated MC answer length bias** — LLMs consistently make correct answers the longest option (~86% of the time, ~99% for Tier 3). Students know this and exploit it. Mitigation: (1) post-process with `/tmp/equalize-lengths.py` to pad distractors, (2) when generating questions, explicitly prompt for equal-length options, (3) verify with length analysis before embedding in activities. The equalization script uses forensic science qualifier phrases — adapt the `PADDING_CONNECTORS` list for other subjects.

## Vite Build Config

- **Manual chunks:** `recharts` and `katex` split via `rollupOptions.output.manualChunks` in `vite.config.ts`. Add new heavy deps here when they inflate the main bundle.
- **BabylonJS is dynamically imported** in `Avatar3D.tsx` — Vite auto-splits it. No need to add to manualChunks.
- **Idle preloads use `safeImport` wrapper** — `StudentDashboard.tsx` wraps all 16 idle `import()` calls in `.catch(() => {})` to prevent stale chunk errors from crashing preload.

## Playwright MCP Plugin

- Expects Chrome at `/opt/google/chrome/chrome` specifically — system Chromium at `/usr/bin/chromium` won't work without a symlink (requires sudo: `sudo mkdir -p /opt/google/chrome && sudo ln -sf /usr/bin/chromium /opt/google/chrome/chrome`)
- Alternative: `tools/screenshot/take.mjs` uses puppeteer-core with system Chromium and works without this constraint

## Known Gotchas

- **Per-student announcement targeting** — Announcements support `targetStudentIds?: string[]`. When set, `StudentDashboard.tsx` filters so only listed students see it. Nudge buttons in TeacherDashboard use this for per-student or batch targeting. Class-wide announcements omit the field. No true DM/chat system exists — it's still the announcement pipeline.
- **Python 3.14 compat** — System Python is 3.14.3 (very new). Some packages (lxml, snowballstemmer) pin older versions that lack 3.14 wheels and fail to build from source. Workaround: install the package `--no-deps`, then install its dependencies separately — newer versions of the pinned deps usually work fine at runtime even if version specifiers don't match.
- **STARTED submissions were previously hidden** — `TeacherDashboard.tsx` used to filter `status !== 'STARTED'`. As of March 2026, they're included so admin can see in-progress work. Any new code consuming assessment submissions should expect STARTED status in the mix.
- **New block types must be added to TWO grading lists** — `submitAssessment` in `functions/src/index.ts` has separate lists: auto-graded types (MC, SHORT_ANSWER, SORTING, RANKING, LINKED) and manual-review types (DRAWING, MATH_RESPONSE, BAR_CHART, DATA_TABLE, CHECKLIST). Missing a block type means its response is silently dropped from `perBlock` and invisible to teachers.
- **Assessment session detection** — `Proctor.tsx` uses `localStorage` + `sessionStorage` token presence to distinguish fresh start (archive then wipe responses) from returning student (restore responses). Both storages must be cleared on submit and retake. `localStorage` survives tab/browser close; `sessionStorage` is same-tab only. Fresh-start wipe archives old responses to `lesson_block_responses_archive` before clearing (soft-delete for recovery).
- **Abort flags on one-shot Firestore reads** — Any `getDoc()` call inside a `useEffect` MUST use a `cancelled` flag cleared in the cleanup function. Without it, navigating away before the promise resolves causes stale state updates and phantom error toasts. Pattern: `let cancelled = false; getDoc(...).then(s => { if (!cancelled) ... }); return () => { cancelled = true; };`
- **Context hooks must not throw** — `useAppData()`, `useAdminData()`, `useChat()` all return safe empty defaults instead of throwing. This prevents ErrorBoundary crashes during Suspense/lazy route transitions. Never revert these to throwing patterns.
- **Boss loot items must include `visualId`** — The boss loot generator (`functions/src/index.ts:3845`) previously omitted `visualId`, `baseName`, `description`, and `obtainedAt`. Without `visualId`, `getItemIconPath()` crashes on `visualId.startsWith()`. Fixed March 2026. Any new loot generation code must include all `LootItem` fields — use `BASE_ITEMS[slot][0].vid` as fallback.
- **LessonBlocks `readOnly` prop** — All 10 interactive block types support `readOnly?: boolean`. When true: inputs disabled, no correct/incorrect feedback, no action buttons, `onResponseChange` is `undefined`. Used by ResourceViewer's post-submission review mode. If adding a new interactive block type, implement `readOnly` support to maintain review mode compatibility.
- **FeatureErrorBoundary is mandatory for all dashboard tabs and admin routes** — All 15 StudentDashboard tabs, 4 TeacherDashboard tabs, and 8 admin routes are wrapped in `<FeatureErrorBoundary>` as of March 2026. Missing it means any render error crashes the entire app with "System Malfunction" instead of showing an inline retry card. When adding new tabs or routes, always wrap them. `FeatureErrorBoundary.componentDidCatch` calls `reportError()` for centralized tracking.
- **Use `lazyWithRetry` for all lazy imports at route level** — `lib/lazyWithRetry.ts` wraps `React.lazy` with auto-reload on stale chunk errors (catches dynamic import failures after deploys, reloads once via sessionStorage flag). Use `lazyWithRetry(() => import(...))` for route-level splits (App.tsx, ResourceViewer.tsx, TeacherDashboard.tsx, LessonEditorPage.tsx). For non-route lazy components rendered inside a page (e.g., DrawingBlock, MathResponseBlock in LessonBlocks.tsx), plain `React.lazy()` with inline `<React.Suspense>` is fine — the parent route already handles chunk reload.
- **Virtualizer `measureElement` is required** — All `useVirtualizer` instances must include `measureElement: (el) => el.getBoundingClientRect().height` and each row must have `ref={virtualizer.measureElement}` + `data-index={virtualRow.index}`. Remove hardcoded `height` from row styles (keep only `transform: translateY`). Without `measureElement`, rows with variable height cause layout glitches. All 5 virtualized components (Leaderboard, TeacherDashboard, UserManagement, OperativesTab, Communications) follow this pattern as of March 2026.
- **`useDebounce` has no unmount cleanup** — The `useDebounce` hook in `lib/rateLimiting.ts` does not clear its `timerRef` on component unmount. Callbacks may fire after unmount. Always pair with a `mountedRef` guard when the debounced function calls `setState` or writes to a backend. This is a known pre-existing issue, not severe enough to fix (mitigated by guards).
- **Submission counts must deduplicate by assignmentId** — A student with retakes has multiple `Submission` docs per assignment. Counting `submissions.filter(s => s.status !== 'STARTED').length` inflates "completed" past the total assignment count (e.g. "20 of 16"). Always deduplicate: `new Set(submissions.filter(...).map(s => s.assignmentId)).size`. For avg scores, use best-per-assignment via a `Map<assignmentId, bestScore>`. Fixed in HomeTab + ProgressDashboard (round 8). Any new completion/score aggregation must follow this pattern.
- **Admin sidebar collapse** — `Layout.tsx` line 305: admin nav must pass `sidebarCollapsed` to `renderNavButton`. Without it, admin sidebar renders full-width buttons squeezed into 76px collapsed width instead of icon-only mode.
- **Enrollment code redemption is server-side only** — `redeemEnrollmentCode` Cloud Function (`functions/src/index.ts`) handles enrollment atomically via `runTransaction`. Client calls it through `callRedeemEnrollmentCode` callable. Firestore rules block direct student writes to `enrollment_codes`. Do NOT add client-side enrollment logic.
- **`useIsMounted` hook for async safety** — `lib/useIsMounted.ts` returns a stable `() => boolean` callback. Use it to guard `setState` calls in promise `.then()` and timer callbacks. Pattern: `const isMounted = useIsMounted(); ... .then(r => { if (!isMounted()) return; setState(r); })`. Already used in BossQuizPanel and StudentDashboard.
- **Submissions use `setDoc` with `merge: true`** — `submitAssignment` writes identity fields (`userId`, `userName`, `assignmentId`, `assignmentTitle`) on every call. On existing docs, Firestore evaluates the `update` rule, so the update allowlist in `firestore.rules` must include these identity fields alongside mutable ones. Without them, re-submissions by renamed students silently fail.
- **Firestore rules: tutoring_sessions field-level gating** — Updates scoped per role: requester can cancel (any status), non-requester can claim tutor (OPEN→MATCHED only), participants can transition status and submit feedback. New tutoring fields need adding to the appropriate `hasOnly` branch.
- **Firestore rules: class_messages update uses whitelist** — Student updates restricted to `hasOnly(['reactions', 'pinnedBy'])`. New student-writable fields must be added to this whitelist. The old blacklist pattern was replaced because new fields would have been auto-writable.
- **Explore agents report from docs, not code** — When using Explore agents to audit codebase state, they may report issues from markdown docs (e.g., CODE_REVIEW_4.md) as still pending even when the code has already been fixed. Always verify agent claims against actual source files before planning work. Read the actual component files, don't trust review doc descriptions of what's "missing".
- **sundayReset only touches evidence** — The `sundayReset` Cloud Function ONLY deletes evidence locker uploads (Storage images + Firestore `evidence` docs). It must NEVER delete submissions, assignments, or any other collection. This was a hard lesson after it wiped 1,912 submissions on 2026-03-09.
- **`mutedUntil` is NOT student-writable** — Removed from the `hasOnly` set in Firestore user profile update rules (2026-03-09). Only admin/Cloud Functions can set mute status. If you need to add a new student-writable field to user profiles, update the `hasOnly` list in `firestore.rules` line ~56, but NEVER re-add `mutedUntil`.
- **`class_messages` create is `allow create: if false`** — All chat message creation goes through the `sendClassMessage` Cloud Function (Admin SDK). This enforces mute checks, content moderation, and class enrollment validation. Direct Firestore writes are blocked. If building new message types, they MUST go through a Cloud Function.
- **Chat `channelId + timestamp` composite index** — `subscribeToChannelMessages` uses `orderBy('timestamp', 'desc'), limit(100)`. This requires a Firestore composite index on `class_messages` for `channelId` (ASC) + `timestamp` (DESC). If the index doesn't exist, Firestore logs a URL to create it.
- **`resilientSnapshot` replaces raw `onSnapshot`** — `services/resilientSnapshot.ts` wraps `onSnapshot` with error reporting via `reportError()`, permission-denied TTL cache (30s, bounded at 100 entries), and exponential backoff retry (3 retries at 2s/4s/8s). All real-time listeners in `dataService.ts` use it. When adding new subscriptions, use `resilientSnapshot(name, query, callback)` — never raw `onSnapshot`. The chat listener (`subscribeToChannelMessages`) still has its own retry logic. `clearDeniedCollections()` is exported and called on auth state changes.
- **Admin auth must use `verifyAdmin()` with custom claims** — Never check `userData.role` from Firestore for admin authorization in Cloud Functions. Always use `verifyAdmin(request.auth)` which checks `customClaims.admin` via Firebase Auth. The Firestore `role` field is display-only and not security-critical.
- **Cloud Functions must use `logger.*` not `console.*`** — `console.error/log/warn` in Cloud Functions doesn't appear in Cloud Logging. Always use `import * as logger from 'firebase-functions/logger'` and call `logger.error()`, `logger.info()`, etc.
- **Module-level throws break Cloud Functions deploy** — All function exports are loaded at module scope. A `throw` at the top level prevents the module from loading and breaks ALL functions. Use lazy getters for environment variables.
- **Chat rate limiting** — `sendClassMessage` enforces 3-second per-user cooldown via `message_cooldowns` Firestore collection (Admin SDK only). HTML tags are stripped from message content before storage.
- **Query bounds are mandatory** — All `onSnapshot` subscriptions must use `.limit()`. Defaults: submissions per assignment (500), users (500), leaderboard (200). Cloud Functions `.get()` calls must also use `.limit(499)` with pagination (`startAfter` cursor loop) — 10 unbounded queries fixed in stability round 3. Unbounded queries cause OOM/timeout at scale.
- **Batch concurrent async operations** — Never do `Promise.all(unboundedArray.map(...))` for emails, notifications, or Firestore writes. Batch in groups of 100 via `Promise.all(items.slice(i, i+100).map(...))`. Fixed in `onNewAssignment` and `checkStreaksAtRisk`.
- **`onSnapshot` needs error callback** — Always pass an error handler as the 2nd argument to `onSnapshot` or use `resilientSnapshot`. Without it, permission errors are silently swallowed.
- **Behavior awards use Cloud Function** — `awardBehavior` in `dataService.ts` now calls `callAwardBehaviorXP` (atomic batch: award doc + XP/currency increment). Do NOT write separate `addDoc` + `updateDoc` patterns for XP awards — always use a Cloud Function with `batch()` or `runTransaction()` for atomicity.
- **Whitelist enrollment uses Cloud Function** — `addToWhitelist` in `dataService.ts` now calls `callAdminAddToWhitelist` (atomic batch: whitelist doc + all matching user docs). Do NOT write multi-step client-side enrollment logic.
- **Assessment fresh-start is a Cloud Function** — `archiveAndClearResponses` atomically archives old responses and clears for fresh start via `runTransaction`. Called from `Proctor.tsx` instead of client-side archive+clear. Has local fallback if CF fails.
- **`persistentWrite` utility for retried Firestore writes** — `lib/persistentWrite.ts` provides `persistentWrite(collection, docId, data, lsKey)` with 3 retries + exponential backoff (2s/4s/8s) and localStorage mirror. Use this for any Firestore write where data loss is unacceptable (student work, completion records). Also provides `syncDirtyDraft()` for mount/online recovery, and `draftKey()`/`readDraft()`/`writeDraft()`/`clearDraft()` helpers. The `usePersistentSave` hook wraps this for React components with debounced saves. Do NOT use raw `setDoc()` for student work — always go through `persistentWrite` or the hook.
- **"Submit" is reserved for assessment submission only** — Per-block action buttons in `LessonBlocks.tsx` must use "Lock In", "Check Answer", "Check Sorting", or "Check Order" — never "Submit". Students confused per-block "Submit" with final assessment submission, causing lost work. `ResourceViewer.tsx` has a sticky bottom banner on assessments with the only "Submit Assessment" button (green, pulsing). Any new interactive block type must follow this pattern.
- **Submissions have NO `classType` field** — The `submissions` collection does not store `classType`. To determine which class a submission belongs to, look up the `assignmentId` in the `assignments` collection and read its `classType`. This affects any aggregation, filtering, or reporting that groups submissions by class. The `tools/progress-reports.py` script derives classType this way.
- **Submission `score` field = XP on classwork, percentage on assessments** — Cloud Function `submitAssignment` writes `score: xpEarned` for non-assessment submissions (`index.ts:2021`) but `score: percentage` for assessments (`index.ts:2339`). Only assessment submissions have `assessmentScore.percentage` and `isAssessment: true`. Any code using `score` must check `isAssessment` first or use `assessmentScore.percentage`. Only 2 of 39 active assignments are assessments (as of March 2026).
- **RubricGrade structure** — `submission.rubricGrade` has shape: `{ grades: { [questionId]: { [skillId]: { selectedTier: number, percentage: number } } }, overallPercentage: number, gradedAt: string, gradedBy: string }`. The tier field is `selectedTier` (0-4), NOT `tier`. AI suggestions use `aiSuggestedGrade` with `suggestedTier` instead.
- **`user.id` vs `user.name` — always use `user.id` for storage keys** — The `User` type has `id` (Firebase UID) and `name` (display name). Any localStorage keys, Firestore doc IDs, or draft keys that scope data per-user MUST use `user.id`. Using `user.name` causes key mismatches (e.g., draft stored under UID but cleared under display name). This bug was caught in QA for the persistence layer — watch for it in any new per-user storage.
