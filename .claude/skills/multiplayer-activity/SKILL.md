---
name: multiplayer-activity
description: >
  Build real-time multiplayer HTML activities using Firebase Realtime Database — lobby system, join codes,
  live state sync, and presence tracking in a single self-contained HTML file. Use this skill whenever the
  user asks to create a multiplayer game, build a real-time collaborative activity, make a classroom
  competition, create a team-based review game, build a multiplayer quiz, or wants any HTML activity where
  multiple students interact in real time. Also trigger when someone says "make a multiplayer version of X",
  "build a game students can play together", "real-time classroom game", "team competition activity",
  "collaborative activity with join codes", or anything involving multiple players connecting via codes
  and playing together. If the request is single-player and doesn't need real-time sync, use 2d-activity
  or 3d-activity instead.
model: claude-sonnet-4-6
effort: high
tools: [Read, Write, Glob, Bash]
---

## What This Skill Does

Generates a standalone, self-contained HTML file with a real-time multiplayer activity powered by Firebase Realtime Database. The activity includes a lobby system with join codes, live player synchronization, presence tracking, and a game flow from lobby → gameplay → results.

**Output:** Single HTML file saved to the appropriate project asset directory.

For the complete Firebase implementation patterns (database schema, join flow, state listener, presence), see [firebase-multiplayer.md](references/firebase-multiplayer.md).

---

## Step 1: Determine the Firebase Project

The multiplayer system needs a Firebase Realtime Database. Determine which project's config to use based on context:

**Porter's Portal** (default if working in that project or for Kellen's classroom):
```javascript
const firebaseConfig = {
    apiKey: "AIzaSyAGUwSeJVCLLz_UTIFj4H3qvJnlFnvNjSw",
    authDomain: "porters-portal.firebaseapp.com",
    databaseURL: "https://porters-portal-default-rtdb.firebaseio.com",
    projectId: "porters-portal",
    storageBucket: "porters-portal.firebasestorage.app",
    messagingSenderId: "822085463019",
    appId: "1:822085463019:web:d55fa7e5b4516429d4aa52"
};
```

**Other projects:** Check the project's `.env.local`, `firebaseConfig.ts`, or CLAUDE.md for credentials. If no Firebase config is found, ask the user to provide one or add it to the project's `.env`.

**RTDB rules requirement:** The Firebase project must have open read/write rules on `/games/` and `/join_codes/` paths. If using a new project, remind the user to configure this.

---

## Step 2: Parse the Request

Extract from the user's prompt:

- **Game concept** — what kind of multiplayer activity (quiz battle, team trivia, collaborative puzzle, real-time competition, review game, etc.)
- **Player count** — how many players/teams (default: 2-4 teams)
- **Subject/topic** — what content the game covers (if educational)
- **Special mechanics** — timers, buzzer systems, board game elements, scoring rules

If the request is vague, ask: "What kind of multiplayer activity? For example: team trivia, head-to-head quiz, collaborative puzzle, real-time race, board game..."

---

## Step 3: Determine Theme and Output Location

**If Porter's Portal project:**
- Use the portal dark theme from [portal-bridge.md](../../../references/portal-bridge.md)
- Include the Proctor Bridge for LMS integration
- Save to `/home/kp/Desktop/Executive Assistant/assets/Simulations/<class>/`
- Ask which class: AP Physics 1, Honors Physics, or Forensic Science

**If another project:**
- Use whatever theme matches the project (ask if unclear)
- Skip the Proctor Bridge unless the project has its own LMS integration
- Save to wherever makes sense for that project's structure

---

## Step 4: Design the Game

Plan before coding. Decide:

1. **Game flow** — what phases the game goes through (lobby → setup → rounds → game over)
2. **Turn structure** — simultaneous play, turn-based, timed rounds, or buzzer-style
3. **Scoring** — how points are earned, displayed, and tallied
4. **State model** — what fields go in the `/games/{gameId}/state` object
5. **Player interactions** — what each player can do and when (answer questions, make moves, vote, etc.)
6. **Win condition** — how the game ends and who wins

The host device is always the source of truth — it resolves conflicts, advances phases, and manages timers.

---

## Step 5: Generate the HTML File

Write a single self-contained HTML file. Read [firebase-multiplayer.md](references/firebase-multiplayer.md) for all the Firebase patterns — use them exactly as documented.

### File Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>[Game Title]</title>
    <style>
        /* All CSS inline */
        /* Use project theme (portal dark theme or project-specific) */
    </style>
</head>
<body>
    <!-- Firebase SDKs -->
    <script src="https://www.gstatic.com/firebasejs/11.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/11.7.1/firebase-database-compat.js"></script>

    <!-- Proctor Bridge (Porter's Portal only) -->
    <script>/* PortalBridge snippet if applicable */</script>

    <!-- Game UI -->
    <div id="app">
        <div id="screen-start"><!-- Name entry + Create/Join --></div>
        <div id="screen-lobby"><!-- Player roster + join code display --></div>
        <div id="screen-game"><!-- Main gameplay area --></div>
        <div id="screen-results"><!-- Leaderboard / final scores --></div>
    </div>

    <script>
        // Firebase init + config
        // Player identity (sessionStorage)
        // Connection status indicator
        // Game logic — screen management driven by state listener
    </script>
</body>
</html>
```

### UI Flow (every multiplayer activity follows this)

1. **Start screen** — Enter display name, choose "Create Game" or "Join Game"
2. **Create path** — Host sets player count (if variable), sees a 4-character join code to share verbally
3. **Join path** — Enter the join code, get assigned to the next open slot
4. **Lobby** — Shows all connected players, ready status, slots remaining. Host can start when all players are ready (or auto-start when full + all ready)
5. **Gameplay** — Live updates via Firebase state listener. Show whose turn it is (if turn-based), scores, timer (if timed)
6. **Results** — Leaderboard showing final scores for all players

### Critical Rules

- Use `.on('value')` for real-time listeners, NOT `.once()` — the whole point is live sync
- Use a SINGLE state listener on `/games/{gameId}/state` that drives ALL UI transitions
- The host pushes state changes; all devices (including host) react via the listener
- Always use `onDisconnect()` to handle players closing the tab
- Use `firebase.database.ServerValue.TIMESTAMP` for server-side timestamps
- Clean up listeners with `.off()` when leaving the game
- Join codes should be 4 characters — short enough to share verbally in a classroom
- Never cache stale state client-side — all truth comes from the database
- For turn-based games, only allow the active player/team's device to trigger actions
- Handle edge cases: late joins blocked during play, disconnected players shown as offline, host disconnect cleans up the game

### Technical Requirements

- **Vanilla ES6+ only** — no frameworks, no jQuery, no bundler
- **All CSS inline** in a `<style>` block
- **Mobile-responsive** — must work on Chromebook screens (1366x768) and phones
- **Minimum 44px touch targets** for all interactive elements
- **Glassmorphism panels** (if using portal theme): `backdrop-filter: blur(14px); background: rgba(18, 10, 38, 0.88); border: 1px solid rgba(160, 100, 255, 0.18); border-radius: 14px;`
- **Connection status indicator** visible at all times
- **No external assets** — everything inline. KaTeX CDN allowed if math rendering needed.

---

## Step 6: Save and Summarize

Save the HTML file to the appropriate location (see Step 3).

Provide a brief summary:
- File path
- Game concept and mechanics
- Number of players/teams supported
- Turn structure (simultaneous, turn-based, timed)
- Which Firebase project it's configured for
- Any limitations or things to tweak

---

## Notes

- **Output ONLY the HTML file.** Write it with the Write tool — no conversational filler around the content.
- **The host is always the source of truth.** In any conflict, the host's state wins.
- **Test with multiple tabs.** Each tab gets a unique player ID via sessionStorage, so you can simulate multiplayer on one device.
- **Questions/content can be embedded or dynamic.** For review games, questions can be hardcoded in the HTML or fetched from the game state. Hardcoded is simpler; dynamic lets the host configure content.
- **Agent delegation (Porter's Portal).** After generating the file, delegate to:
  - **qa-engineer** — validate multiplayer sync, edge cases (disconnect/reconnect, late join), accessibility
  - **content-writer** — review game instructions, UI labels, educational content accuracy
