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
- Mobile bottom nav bar (Home/Resources/Missions/Progress) shows below `lg` breakpoint (1024px) — `pb-16` added to main content to avoid overlap
- Toast notifications are **top-center** (`fixed top-4 left-1/2 -translate-x-1/2`), not bottom-left
- Keyboard shortcuts active in lessons: `j`/`k` scroll blocks, `?` shows help overlay (only when no input focused)

## Known Gotchas

- **Per-student announcement targeting** — Announcements support `targetStudentIds?: string[]`. When set, `StudentDashboard.tsx` filters so only listed students see it. Nudge buttons in TeacherDashboard use this for per-student or batch targeting. Class-wide announcements omit the field. No true DM/chat system exists — it's still the announcement pipeline.
- **Python 3.14 compat** — System Python is 3.14.3 (very new). Some packages (lxml, snowballstemmer) pin older versions that lack 3.14 wheels and fail to build from source. Workaround: install the package `--no-deps`, then install its dependencies separately — newer versions of the pinned deps usually work fine at runtime even if version specifiers don't match.
- **STARTED submissions were previously hidden** — `TeacherDashboard.tsx` used to filter `status !== 'STARTED'`. As of March 2026, they're included so admin can see in-progress work. Any new code consuming assessment submissions should expect STARTED status in the mix.
- **New block types must be added to TWO grading lists** — `submitAssessment` in `functions/src/index.ts` has separate lists: auto-graded types (MC, SHORT_ANSWER, SORTING, RANKING, LINKED) and manual-review types (DRAWING, MATH_RESPONSE, BAR_CHART, DATA_TABLE, CHECKLIST). Missing a block type means its response is silently dropped from `perBlock` and invisible to teachers.
- **Assessment refresh detection** — `Proctor.tsx` uses `sessionStorage` token presence to distinguish fresh start (wipe responses) from mid-assessment refresh (restore responses). Don't clear `sessionStorage` tokens except on successful submit or explicit retake.
- **Abort flags on one-shot Firestore reads** — Any `getDoc()` call inside a `useEffect` MUST use a `cancelled` flag cleared in the cleanup function. Without it, navigating away before the promise resolves causes stale state updates and phantom error toasts. Pattern: `let cancelled = false; getDoc(...).then(s => { if (!cancelled) ... }); return () => { cancelled = true; };`
- **Context hooks must not throw** — `useAppData()`, `useAdminData()`, `useChat()` all return safe empty defaults instead of throwing. This prevents ErrorBoundary crashes during Suspense/lazy route transitions. Never revert these to throwing patterns.
- **Boss loot items must include `visualId`** — The boss loot generator (`functions/src/index.ts:3845`) previously omitted `visualId`, `baseName`, `description`, and `obtainedAt`. Without `visualId`, `getItemIconPath()` crashes on `visualId.startsWith()`. Fixed March 2026. Any new loot generation code must include all `LootItem` fields — use `BASE_ITEMS[slot][0].vid` as fallback.
- **LessonBlocks `readOnly` prop** — All 10 interactive block types support `readOnly?: boolean`. When true: inputs disabled, no correct/incorrect feedback, no action buttons, `onResponseChange` is `undefined`. Used by ResourceViewer's post-submission review mode. If adding a new interactive block type, implement `readOnly` support to maintain review mode compatibility.
- **FeatureErrorBoundary is mandatory for dashboard tabs** — All tabs in `StudentDashboard.tsx` must be wrapped in `<FeatureErrorBoundary>`. Missing it means any render error in the tab crashes the entire app with "System Malfunction" instead of showing an inline retry card.
- **sundayReset only touches evidence** — The `sundayReset` Cloud Function ONLY deletes evidence locker uploads (Storage images + Firestore `evidence` docs). It must NEVER delete submissions, assignments, or any other collection. This was a hard lesson after it wiped 1,912 submissions on 2026-03-09.
- **`mutedUntil` is NOT student-writable** — Removed from the `hasOnly` set in Firestore user profile update rules (2026-03-09). Only admin/Cloud Functions can set mute status. If you need to add a new student-writable field to user profiles, update the `hasOnly` list in `firestore.rules` line ~56, but NEVER re-add `mutedUntil`.
- **`class_messages` create is `allow create: if false`** — All chat message creation goes through the `sendClassMessage` Cloud Function (Admin SDK). This enforces mute checks, content moderation, and class enrollment validation. Direct Firestore writes are blocked. If building new message types, they MUST go through a Cloud Function.
- **Chat `channelId + timestamp` composite index** — `subscribeToChannelMessages` uses `orderBy('timestamp', 'desc'), limit(100)`. This requires a Firestore composite index on `class_messages` for `channelId` (ASC) + `timestamp` (DESC). If the index doesn't exist, Firestore logs a URL to create it.
