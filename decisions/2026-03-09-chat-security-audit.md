# Chat Feature Security Audit

**Date:** 2026-03-09
**Type:** Security hardening
**Status:** Implemented and deployed

## Context

The Communications/chat feature had never received a formal QA pass. A code + visual audit surfaced 3 critical security vulnerabilities, 6 high-priority issues, and 10+ medium/low items.

## Key Decisions

### 1. Lock class_messages create to Cloud Functions only
- **Before:** Any authenticated user could write directly to Firestore, bypassing mute checks, moderation, and enrollment validation
- **After:** `allow create: if false` — all messages must go through `sendClassMessage` Cloud Function
- **Trade-off:** Slightly higher latency (function call vs direct write), but security is non-negotiable

### 2. Remove mutedUntil from student-writable fields
- Students could self-clear their mute by writing to their own user document
- Removed from the `hasOnly` list in Firestore rules

### 3. Add class enrollment validation to sendClassMessage
- Students could send messages to any class channel, even ones they're not enrolled in
- Now validates `enrolledClasses` for `class_` and `res_` channels; admin bypasses

### 4. Harden content moderation
- Added Unicode normalization (NFKD), leetspeak substitution, separator stripping, repeated character collapsing
- Still regex-based — consider external moderation API if bypasses persist

## Deferred Items
- Message pagination beyond 100 (architecture change)
- Student unread badges (feature addition, requires per-channel subscription)
- Emoji picker portal rendering (edge case clipping)

## Firestore Index Required
Composite index on `class_messages`: `channelId` ASC + `timestamp` DESC. Firestore will prompt to create this on first query if missing.
