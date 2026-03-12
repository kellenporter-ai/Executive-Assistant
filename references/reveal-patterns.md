# Reveal.js Patterns & Theme Presets

Reference for the `/slide-deck` skill. All patterns extracted from production presentations.

## Reveal.js Standard Config

```javascript
Reveal.initialize({
  hash: true,
  history: true,
  transition: 'slide',          // or 'fade', 'convex', 'zoom'
  backgroundTransition: 'fade',
  transitionSpeed: 'default',   // or 'slow', 'fast'
  center: true,
  controls: true,
  controlsTutorial: true,
  progress: true,
  slideNumber: 'c/t',
  keyboard: true,
  overview: true,
  width: 1920,
  height: 1080,
  margin: 0.04,
  plugins: []
});
```

Speaker notes: `<aside class="notes">` — press 'S' to open speaker view.
Notes plugin requires explicit load: `plugin/notes/notes.min.js` + `plugins: [RevealNotes]`.

---

## Theme Presets

### 1. Deep Space
- **Palette:** `#080c1a` (bg), `#e8eaf6` (text), `#00e5ff` (cyan), `#ff4081` (pink), `#ffd600` (gold), `#7b61ff` (purple)
- **Fonts:** Outfit (display) + Inter (body)
- **Background:** Canvas particle network with colored nodes
- **Transition:** `slide` with `fade` background

### 2. Forensic Green
- **Palette:** `#040c06` (bg), `#39e07a` (lime), `#00e5ff` (cyan), `#ff5c5c` (red), `#ffd166` (yellow)
- **Fonts:** Outfit (display) + JetBrains Mono (tables)
- **Background:** Animated DNA double helix (canvas)
- **Transition:** `fade` with `slow` speed

### 3. Physics Purple-Blue
- **Palette:** `#0f0720` (bg), `#1a0a3e` (darker), `#0d1f4a` (blue-black), `#5b9cf6` (blue accent), `#22d47a` (green)
- **Fonts:** Outfit (display) + Inter (body)
- **Background:** Animated gradient (20s cycle) + 3 floating orbs
- **Transition:** `slide` with `fade` background

---

## Animation Recipes

### Gradient Shift (background)
```css
.reveal {
  background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary), var(--bg-tertiary));
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

### Floating Orbs (ambient)
```css
.ambient-overlay {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}
.orb-1 {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  width: 50vw; height: 50vh;
  background: radial-gradient(circle, var(--accent) 0%, transparent 65%);
  top: -10vh; left: -10vw;
  animation: orbFloat1 30s ease-in-out infinite;
}
@keyframes orbFloat1 {
  0%, 100% { opacity: 0.15; transform: translate(0, 0); }
  33% { opacity: 0.25; transform: translate(15vw, 10vh); }
  66% { opacity: 0.15; transform: translate(-5vw, 20vh); }
}
```

**Orb opacity guidelines:** Base 0.10-0.15, peak 0.18-0.25, never > 0.3.
**Standard placements:** Top-left, bottom-right, top-right offset. Duration 25-35s staggered.

### Blob Pulse (title glow)
```css
.glow-blob {
  position: absolute;
  width: 600px; height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0,229,255,.12) 0%, transparent 70%);
  pointer-events: none;
  animation: blobPulse 6s ease infinite;
}
@keyframes blobPulse {
  0%, 100% { transform: scale(1); opacity: .7; }
  50% { transform: scale(1.15); opacity: 1; }
}
```

### Slide Up (entry)
```css
@keyframes slideUp {
  from { opacity: 0; transform: translateY(28px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## Ambient Overlay Z-Index (Critical)

Never use `::before`/`::after` on `.reveal` — they're invisible behind Reveal.js's opaque background.

```css
.reveal { position: relative; }
.ambient-overlay { z-index: 1; }
.reveal .slides { position: relative; z-index: 2; }
```

Use child `<div>` elements inside `.reveal` with `z-index: 1`.

---

## Card & Layout Patterns

### Pattern Card (content block with colored left border)
```css
.pattern-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-left: 5px solid var(--accent);
  border-radius: 16px;
  padding: 1em 1.4em;
  backdrop-filter: blur(4px);
  font-size: 0.88em;
  line-height: 1.65;
}
```

### Scenario/Question Box
```css
.scenario-box {
  background: rgba(0,229,255,0.07);
  border: 1px solid rgba(0,229,255,0.25);
  border-left: 4px solid var(--cyan);
  border-radius: 8px;
  padding: 0.9em 1.4em;
  width: 80%;
  font-size: 0.82em;
}
```

### Result Glow Box
```css
.result-glow {
  background: linear-gradient(135deg, rgba(34,212,122,0.15), rgba(91,156,246,0.15));
  border: 2px solid var(--highlight);
  border-radius: 20px;
  padding: 1.2em 2em;
  box-shadow: 0 0 40px rgba(34,212,122,0.2);
}
```

### Data Table
```css
.data-table {
  width: 88%;
  border-collapse: collapse;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72em;
}
.data-table th {
  background: rgba(57, 224, 122, 0.15);
  padding: 0.55em 1.2em;
  border: 1px solid rgba(255,255,255,0.15);
}
.data-table tr:nth-child(even) td {
  background: rgba(255,255,255,0.03);
}
```

### Candidate Cards (with elimination states)
```css
.candidate { border: 2px solid rgba(255,255,255,0.18); border-radius: 14px; padding: 1em; transition: all 0.3s; }
.candidate.eliminated { opacity: 0.35; border-color: var(--danger); text-decoration: line-through; }
.candidate.winner { border-color: var(--highlight); background: rgba(34,212,122,0.1); box-shadow: 0 0 20px rgba(34,212,122,0.15); }
```

---

## Grid Sizing Table

| Items | Columns | Font Size | Notes |
|-------|---------|-----------|-------|
| 2-4 | 2 | 0.8-0.9em | Comfortable, readable |
| 3 | 3 | 0.7-0.75em | Good for cards |
| 4 | 2 | 0.75em | Two rows, medium density |
| 6 | 3 | 0.6-0.65em | Tight grid |
| 7+ | 3 | 0.55-0.6em | Risk of overflow — split slides instead |

**Effective viewport:** 1920x1080 with 4% margin = ~1843x1043px usable.

---

## 16:9 Widescreen Layout Rules (Critical)

The target ratio is **16:9 (1920×1080)**, NOT 4:3. Content designed for 4:3 clips vertically at 16:9. Follow these rules:

### Vertical Budget
- **Max usable height:** ~1043px (1080 minus margin). Every element competes for this space.
- **h2 margin:** `margin: 0 0 0.15em 0` — default Reveal.js heading margins are too large.
- **Fragment margins:** ≤0.4em between fragments. Never >0.5em.
- **Padding:** pattern cards 0.5em 1em (not 1em 1.4em), task boxes 0.5em 1.2em (not 1em 1.6em), eq-containers 0.4em 1.2em (not 0.8em 1.8em).

### Use the Width
- **Prefer horizontal layouts** over vertical stacks. Side-by-side cards, horizontal flowcharts, `flex-wrap: nowrap`.
- **Two-col layouts:** use `max-width: 92%` and `gap: 1.5em`.
- **Multi-item lists:** 4 items → single row with `flex-wrap: nowrap` and smaller cards, not 2×2 grid.
- **Flowcharts/derivation chains:** horizontal arrows (`→`) between compact step cards, never vertical stacks with `⬇` arrows.

### SVG Heights
- **Max SVG height:** 400px for two-col, 320px for standalone. Never >420px.
- **Force diagrams:** ~320px height is enough for point-object + two forces.
- **Bar charts:** ~310px height.

### Compact CSS Defaults (16:9-safe)
```css
.pattern-card { padding: 0.5em 1em; margin: 0.2em 0; border-radius: 12px; font-size: 0.82em; line-height: 1.5; }
.task-box { padding: 0.5em 1.2em; margin: 0.3em auto; border-radius: 12px; }
.eq-container { padding: 0.4em 1.2em; margin: 0.25em auto; border-radius: 12px; }
.result-glow { padding: 0.5em 1.5em; border-radius: 16px; }
.summary-card { padding: 0.6em 1em; border-radius: 14px; }
```

### Force Diagrams
- **Always use point-object representation** (filled circle, r=9-10) for translational motion — never rectangles/extended objects.
- Force arrows originate from the dot. Acceleration arrow offset to the side, dashed.

---

## Typography Scales

| Context | h1 | h2 | body | small |
|---------|----|----|------|-------|
| Feature-heavy | 5.5em | 1.4-1.5em | 0.85-0.95em | 0.62-0.72em |
| Content-dense | 2.6em | 1.05-1.3em | 0.72-0.85em | 0.55-0.62em |
| Equation-focused | 2.2-2.6em | 2.2em | 0.88em | n/a |

When content overflows, reduce typography scale before splitting slides.

---

## Canvas Background Patterns

### Particle Network
```javascript
const COUNT = 85, MAX_DIST = 165;
const COLORS = ['0,229,255', '123,97,255', '255,64,129', '0,230,118', '255,214,0'];
// Particles bounce within viewport, edges drawn between particles within MAX_DIST
// ctx.strokeStyle = `rgba(100,180,255,${t * t * 0.28})`
```

### DNA Helix
```javascript
// Three helix columns at x: W*0.08, W*0.5, W*0.92
// Amplitudes: 55-60px | Wavelengths: 180-200px
// Phases: 0, 1.2, 2.4 (staggered)
// offset += 0.4 per frame (continuous scroll)
```
