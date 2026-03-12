# Firebase Realtime Database — Multiplayer Activity Patterns

Reference for the `/multiplayer-activity` skill. All patterns are tested and production-ready.

## Quick Start

```html
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-database-compat.js"></script>
<script>
  // Config injected by the /multiplayer-activity skill at generation time.
  // Real values live in .env (FIREBASE_API_KEY) and context/work.md.
  firebase.initializeApp({
    apiKey: "YOUR_FIREBASE_API_KEY",
    databaseURL: "https://porters-portal-default-rtdb.firebaseio.com",
    projectId: "porters-portal"
  });
  const db = firebase.database();
</script>
```

## Database Schema

```
/games/{gameId}/
  config/          → { maxPlayers, mode, hostId, createdAt }
  state/           → { phase, round, timer, data... }  (host-managed)
  players/
    {playerId}/    → { name, score, connected, joinedAt, lastSeen }
  answers/         → { [playerId]: answer }  (per-round, host clears)

/join_codes/{code} → { gameId, createdAt, active }
```

## Join Code Flow

### Host Creates Game
```javascript
const gameId = db.ref('games').push().key;
const code = Math.random().toString(36).substring(2, 6).toUpperCase(); // 4-char

// Atomic: create game + register code
const updates = {};
updates[`games/${gameId}/config`] = {
  hostId: myId,
  maxPlayers: 30,
  mode: 'quiz-race',
  createdAt: firebase.database.ServerValue.TIMESTAMP
};
updates[`games/${gameId}/state`] = { phase: 'lobby' };
updates[`games/${gameId}/players/${myId}`] = {
  name: myName,
  score: 0,
  connected: true,
  joinedAt: firebase.database.ServerValue.TIMESTAMP
};
updates[`join_codes/${code}`] = { gameId, createdAt: firebase.database.ServerValue.TIMESTAMP, active: true };

await db.ref().update(updates);
```

### Player Joins
```javascript
async function joinGame(code, playerId, playerName) {
  const snap = await db.ref(`join_codes/${code.toUpperCase()}`).once('value');
  if (!snap.exists() || !snap.val().active) throw new Error('Invalid code');

  const gameId = snap.val().gameId;
  const configSnap = await db.ref(`games/${gameId}/config`).once('value');
  const config = configSnap.val();

  // Check capacity
  const playersSnap = await db.ref(`games/${gameId}/players`).once('value');
  if (playersSnap.numChildren() >= config.maxPlayers) throw new Error('Game full');

  // Check phase (no late joins during gameplay)
  const stateSnap = await db.ref(`games/${gameId}/state`).once('value');
  if (stateSnap.val().phase !== 'lobby') throw new Error('Game already started');

  await db.ref(`games/${gameId}/players/${playerId}`).set({
    name: playerName,
    score: 0,
    connected: true,
    joinedAt: firebase.database.ServerValue.TIMESTAMP
  });

  return gameId;
}
```

## State Listener Pattern

**One listener drives ALL UI.** No polling, no multiple listeners.

```javascript
function subscribeToGame(gameId, renderFn) {
  const stateRef = db.ref(`games/${gameId}/state`);
  const playersRef = db.ref(`games/${gameId}/players`);

  // State changes drive phase transitions
  stateRef.on('value', (snap) => {
    const state = snap.val();
    renderFn({ type: 'state', data: state });
  });

  // Player list changes (joins, disconnects, score updates)
  playersRef.on('value', (snap) => {
    const players = [];
    snap.forEach((child) => {
      players.push({ id: child.key, ...child.val() });
    });
    renderFn({ type: 'players', data: players });
  });

  // Return cleanup function
  return () => {
    stateRef.off();
    playersRef.off();
  };
}
```

### Phase Transitions (host only)
```javascript
// lobby → playing → results
async function startGame(gameId) {
  await db.ref(`games/${gameId}/state`).update({
    phase: 'playing',
    round: 1,
    startedAt: firebase.database.ServerValue.TIMESTAMP
  });
}

async function endGame(gameId) {
  await db.ref(`games/${gameId}/state`).update({ phase: 'results' });
  await db.ref(`join_codes/${code}`).update({ active: false });
}
```

## Presence & Disconnection

```javascript
function setupPresence(gameId, playerId) {
  const playerRef = db.ref(`games/${gameId}/players/${playerId}`);
  const connectedRef = db.ref('.info/connected');

  connectedRef.on('value', (snap) => {
    if (!snap.val()) return;

    // When I disconnect, mark me as disconnected
    playerRef.onDisconnect().update({
      connected: false,
      lastSeen: firebase.database.ServerValue.TIMESTAMP
    });

    // Mark me as connected now
    playerRef.update({ connected: true });
  });
}
```

## Critical Rules

1. **Host = source of truth.** Only the host pushes state changes. All other devices react via listeners.
2. **Use `.on('value')` not `.once()`** for live state. `.once()` is only for join validation.
3. **Always `.off()` on cleanup** — call the unsubscribe function when leaving.
4. **4-character codes** — easy to say aloud in a classroom. Uppercase alphanumeric.
5. **`ServerValue.TIMESTAMP`** for all times — never `Date.now()` (clock skew).
6. **Late joins blocked** — check `state.phase === 'lobby'` before allowing join.
7. **Turn-based validation** — only the active player's device triggers actions.
8. **No client-side scoring** — host calculates and writes scores.
9. **Batch updates** — use `db.ref().update(multiPathObj)` for atomic multi-path writes.

## Security Notes

RTDB rules needed for multiplayer activities:

```json
{
  "rules": {
    "games": {
      "$gameId": {
        ".read": true,
        ".write": true
      }
    },
    "join_codes": {
      "$code": {
        ".read": true,
        ".write": true
      }
    }
  }
}
```

For production hardening: restrict writes to authenticated users, validate data shapes, and rate-limit code creation.

## Testing Tips

- **Multi-tab:** Open 3-4 tabs to simulate a classroom. Each tab = one player.
- **Disconnect:** Chrome DevTools → Network → Offline to test presence cleanup.
- **Race conditions:** Rapidly click join on multiple tabs to test capacity enforcement.
- **Code collision:** Extremely unlikely with 4-char alphanumeric (1.6M combinations) but handle gracefully.
