# Backend Integration Engineer Memory

## See Also
- `agents/memory/SHARED.md` — cross-cutting gotchas (read first)
- `projects/Porters-Portal/.agents/backend-engineer.md` — portal-specific context
- `references/economy-reference.md` — all economy constants and formulas

## Cloud Function Canonical Pattern

```typescript
export const functionName = onCall(
  { region: "us-east1", enforceAppCheck: false },
  async (request) => {
    if (!request.auth) throw new HttpsError("unauthenticated", "...");
    const { field } = request.data;
    if (!field) throw new HttpsError("invalid-argument", "...");
    await db.runTransaction(async (t) => { /* read, validate, write */ });
    return { success: true };
  }
);
```

- Always `HttpsError`, never generic throws
- Auth check first, input validation second
- Transactions for multi-document ops
- Return structured objects

## Admin Auth Pattern

**Use custom claims, NOT Firestore role field:**
```typescript
function verifyAdmin(auth: AuthData) {
  if (!auth?.token?.admin) throw new HttpsError("permission-denied", "Admin only");
}
```

All 4 admin functions (`sendClassMessage`, `scaleBossHp`, `awardBehaviorXP`, `adminAddToWhitelist`) migrated to this pattern March 2026.

## Transaction Rules

- `runTransaction()` for read-then-write on same/cross collection (XP + inventory + currency)
- Never read-then-write without transaction when concurrent access possible
- Server timestamps: `admin.firestore.FieldValue.serverTimestamp()` in CF, `serverTimestamp()` in client
- Batch 100+ writes with `batch()`

## Firestore Schema Quick Reference

| Collection | Key Fields | Notes |
|-----------|------------|-------|
| `users/{uid}` | `gamification` (XP, inventory, cosmetics), `appearance`, `classProfiles` | RPG profile |
| `assignments/{id}` | `lessonBlocks[]`, `classType`, `rubric`, `isAssessment`, `status` | Lessons/assessments |
| `submissions/{id}` | `userId`, `assignmentId`, `score`, `status`, `rubricGrade`, `blockResponses` | NO `classType` — derive via assignment |
| `classConfigs/{classType}` | Per-class feature toggles | |
| `enrollment_codes/{code}` | CF-write only, student reads blocked | |
| `message_cooldowns/{userId}` | Admin SDK only, 3-sec cooldown enforcement | |

## Critical Anti-Patterns

### Module-Level Throws
Module-level `throw` crashes ALL Functions deploy. Use lazy getters:
```typescript
function getAdminEmail() {
  if (!process.env.ADMIN_EMAIL) throw new Error("ADMIN_EMAIL not set");
  return process.env.ADMIN_EMAIL;
}
```

### Score Semantics
- Non-assessment: `score = XP earned`
- Assessment: `score = percentage` + `assessmentScore.percentage` + `isAssessment: true`
- AI-flagged submissions: score forced to 0

### Client Firestore Write Allowlist
Only these gamification fields are writable client-side:
`codename`, `privacyMode`, `lastLevelSeen`, `appearance`, `classProfiles`, `activeQuests`

Any other field silently fails in prod. **Example bug (March 2026):** `equipCosmetic()` writes `gamification.activeCosmetic` — NOT in allowlist — must be moved to CF.

### Query Bounds (Mandatory)
All subscriptions/CF queries must `.limit()`:
- Submissions per assignment: 500
- Users: 500
- Leaderboard: 200
- CF `get()` calls: `.limit(499)` with pagination

### Submission Data Gotchas
- `submissions` have NO `classType` field — derive via assignment lookup
- `rubricGrade.grades[qId][skillId].selectedTier` (0-4), NOT `.tier`
- AI suggestions use `suggestedTier` not `selectedTier`
- STARTED submissions included in all queries (March 2026)
- Completion counts: deduplicate by assignmentId (retakes inflate)

## Use Cloud Functions Instead Of Client-Side

- Enrollment code logic → `redeemEnrollmentCode` CF (atomic)
- XP awards → `callAwardBehaviorXP` CF (atomic batch)
- Whitelist adds → `callAdminAddToWhitelist` CF (atomic)
- Chat messages → `sendClassMessage` CF (rate limiting + HTML strip)
- Student work writes → `persistentWrite()` utility (retry + localStorage)
- Snapshot listeners → `resilientSnapshot()` wrapper (auto-retry, backoff)

## Deployment Gotchas

- `firebase deploy --only hosting` ships `dist/` — must `npm run build` first
- Linter auto-removes unused imports — re-add after linter runs
- `npx tsc --noEmit` checks types but doesn't produce `dist/`
- Logging: `logger.error()` / `logger.info()`, not `console.*`

## Loot Generation (Server-Side)

Key formulas in `functions/src/index.ts`:
- Rarity roll: UNIQUE >0.98, RARE 0.85-0.98, UNCOMMON 0.60-0.85, COMMON <=0.60
- Tier scaling: `maxTierAvailable = min(10, floor(level / 50) + 1)`
- Affix value: `max(1, tier * 5 + random(-2 to 2))`
- Must include ALL fields especially `visualId` (missing causes crashes)
- See `references/economy-reference.md` for complete tables

## Chat Rate Limiting

`sendClassMessage` enforces 3-second cooldown per user via `message_cooldowns` collection.
HTML tags stripped from content. Never rely on client-side rate limiting.
