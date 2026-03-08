# Firebase Multiplayer Reference

Complete implementation patterns for real-time multiplayer HTML activities using Firebase Realtime Database.

---

## Table of Contents

1. [Firebase Setup](#firebase-setup)
2. [Player Identity](#player-identity)
3. [Connection Status](#connection-status)
4. [Database Schema](#database-schema)
5. [Game Creation (Host)](#game-creation-host)
6. [Joining a Game](#joining-a-game)
7. [State Listener Pattern](#state-listener-pattern)
8. [Lobby Player List](#lobby-player-list)
9. [State Updates](#state-updates)
10. [Presence & Disconnect](#presence--disconnect)
11. [Game Cleanup](#game-cleanup)
12. [Security Notes](#security-notes)

---

## Firebase Setup

Include these CDN scripts (Firebase 11.x compat build — no bundler needed):

```html
<script src="https://www.gstatic.com/firebasejs/11.7.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/11.7.1/firebase-database-compat.js"></script>
```

Initialize with the project's config:

```javascript
firebase.initializeApp(firebaseConfig);
const db = firebase.database();
```

The `firebaseConfig` object is provided by the skill's main instructions — it comes from the project context, not this file.

**Do NOT include `firebase-auth-compat.js`** — auth is not used for multiplayer games. The RTDB rules on `/games/` and `/join_codes/` paths are open.

---

## Player Identity

No Firebase Auth needed. Generate a stable player ID per browser tab using sessionStorage:

```javascript
let myUid = sessionStorage.getItem('game_player_uid');
if (!myUid) {
    myUid = 'player_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 8);
    sessionStorage.setItem('game_player_uid', myUid);
}
```

This means:
- Each tab gets its own identity (good for testing on one device)
- Refreshing the same tab keeps the same ID (good for reconnection)
- No login flow needed — students just enter a display name

---

## Connection Status

Show a live online/offline indicator so students know if Firebase is reachable:

```javascript
db.ref('.info/connected').on('value', snap => {
    const el = document.getElementById('fb-status');
    if (el) {
        const online = snap.val() === true;
        el.textContent = online ? '● ONLINE' : '● OFFLINE';
        el.style.color = online ? '#4ade80' : '#ef4444';
    }
});
```

Place the status indicator in the header or corner of the UI.

---

## Database Schema

All game data lives under `/games/{gameId}/`:

```json
{
    "meta": {
        "createdBy": "uid",
        "status": "waiting|setup|playing|finished",
        "createdAt": 1234567890,
        "joinCode": "ABCD",
        "numTeams": 2,
        "timerSecs": 20
    },
    "players": {
        "uid1": { "name": "Team Alpha", "teamId": 0, "ready": false, "connected": true, "lastSeen": 1234567890 },
        "uid2": { "name": "Team Bravo", "teamId": 1, "ready": true,  "connected": true, "lastSeen": 1234567890 }
    },
    "state": {
        // Shared game state — ALL game logic goes here
        // Examples: phase, teams[], currentTeamIndex, scores, round, board, etc.
        // Any player can read; the host typically drives updates
    },
    "answers": {
        "uid1": { "teamId": 0, "answer": "A", "correct": true, "ts": 1234567890 }
        // Per-player answer submissions — useful for quiz/review games
    }
}
```

Join code index: `/join_codes/{CODE}` → `gameId`

The `meta` fields shown above are the baseline. Add game-specific fields as needed (e.g., `maxPlayers`, `currentRound`, `difficulty`). The schema is a guide, not enforced by rules.

---

## Game Creation (Host)

```javascript
const gameId = db.ref('games').push().key;
const joinCode = Math.random().toString(36).substring(2, 6).toUpperCase();
await db.ref('games/' + gameId).set({
    meta: { createdBy: myUid, status: 'waiting', createdAt: Date.now(), joinCode, numTeams: N },
    players: { [myUid]: { name: hostName, teamId: -1, ready: true, connected: true } }
});
await db.ref('join_codes/' + joinCode).set(gameId);

// Clean up if host disconnects:
db.ref('games/' + gameId).onDisconnect().remove();
db.ref('join_codes/' + joinCode).onDisconnect().remove();
```

The host's `teamId` is `-1` because the host may or may not play — that depends on the game design.

---

## Joining a Game

```javascript
const snapshot = await db.ref('join_codes/' + code).get();
if (!snapshot.exists()) { /* room not found */ return; }
const gameId = snapshot.val();
const gameSnap = await db.ref('games/' + gameId).get();
const gameData = gameSnap.val();
if (gameData.meta.status !== 'waiting') { /* game already started */ return; }

// Find lowest unoccupied team slot
const players = gameData.players || {};
const takenIds = Object.values(players).map(p => p.teamId).filter(id => id >= 0);
let slot = 0;
while (takenIds.includes(slot)) slot++;
if (slot >= gameData.meta.numTeams) { /* room full */ return; }

await db.ref('games/' + gameId + '/players/' + myUid).set({
    name: playerName, teamId: slot, ready: false, connected: true,
    lastSeen: firebase.database.ServerValue.TIMESTAMP
});
db.ref('games/' + gameId + '/players/' + myUid + '/connected').onDisconnect().set(false);
```

---

## State Listener Pattern

This is the core pattern — a single listener on `/games/{gameId}/state` drives ALL screen transitions. The host pushes state; every device (including the host) reacts:

```javascript
db.ref('games/' + gameId + '/state').on('value', snap => {
    const gs = snap.val();
    if (!gs) return;
    switch (gs.phase) {
        case 'setup':    handleSetup(gs);    break;
        case 'turn':     handleTurn(gs);     break;
        case 'playing':  handlePlaying(gs);  break;
        case 'gameover': handleGameOver(gs);  break;
    }
});
```

The phase names above are examples — use whatever phases your game needs. The point is: one listener, one switch, all UI driven by the state object.

---

## Lobby Player List

Live-updating player roster in the lobby:

```javascript
db.ref('games/' + gameId + '/players').on('value', snap => {
    const players = snap.val() || {};
    // Render connected players, show count vs numTeams
    // Update ready indicators
    // Enable/disable "Start Game" button for host
});
```

---

## State Updates

The host pushes state changes; all devices react via the state listener:

```javascript
await db.ref('games/' + gameId + '/state').update({
    phase: 'playing', currentTeamIndex: 0, scores: [0, 0], round: 1
});
```

Use `update()` for partial changes, `set()` for replacing the entire state.

---

## Presence & Disconnect

```javascript
// Mark player as disconnected when tab closes
db.ref('games/' + gameId + '/players/' + myUid + '/connected').onDisconnect().set(false);
```

For the host, use `onDisconnect().remove()` on the entire game path to clean up abandoned games.

---

## Game Cleanup

When the game ends naturally:

```javascript
await db.ref('games/' + gameId + '/meta/status').set('finished');
await db.ref('join_codes/' + joinCode).remove();
```

Also clean up listeners:

```javascript
db.ref('games/' + gameId + '/state').off();
db.ref('games/' + gameId + '/players').off();
```

---

## Security Notes

- `/games/` and `/join_codes/` paths are fully open — no auth, no validation
- Any device can read and write any game path
- Use `myUid` from sessionStorage as the player identifier for all writes
- Use `firebase.database.ServerValue.TIMESTAMP` for server-side timestamps
- The host device is the "source of truth" — it resolves conflicts and advances phases
