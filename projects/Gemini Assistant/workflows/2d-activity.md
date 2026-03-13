# Workflow: 2D Activity

Generate lightweight, interactive HTML activities using Canvas, SVG, or vanilla JavaScript. No heavy frameworks — these must run well on low-end devices.

## Step 1: Define the Activity

1. **Subject/Topic** — What is the activity teaching or practicing?
2. **Interaction type** — Drag-and-drop, sorting, matching, labeling, simulation, quiz, graph, timeline?
3. **Target device** — Desktop, tablet, Chromebook? (default: Chromebook — assume 1366x768, limited GPU)
4. **Complexity** — Simple exercise or multi-step investigation?

## Step 2: Design

Plan the activity structure:
- **Layout** — How elements are arranged on screen
- **Interactions** — What the user clicks, drags, types, or selects
- **Feedback** — How the activity responds (correct/incorrect, scoring, visual changes)
- **Completion** — How the user knows they're done

Present the design for user approval.

## Step 3: Build

Generate a single, self-contained HTML file:

### Technical Requirements
- **Single file** — All HTML, CSS, and JS in one file
- **No external dependencies** — No CDN links, no npm packages
- **Responsive** — Must work at 1366x768 minimum
- **Touch-friendly** — Support both mouse and touch events
- **Performant** — No heavy animations on low-end devices

### Code Standards
- Clean, readable JavaScript (no minification)
- CSS custom properties for theming
- Semantic HTML where possible
- Clear comments for complex logic
- `prefers-reduced-motion` media query for animations

### Accessibility
- Keyboard navigable where applicable
- ARIA labels on interactive elements
- Sufficient color contrast (4.5:1)
- Don't rely on color alone for meaning

## Step 4: Test

1. Verify the activity works as designed
2. Check responsive behavior at target viewport
3. Verify all interactions function (click, drag, keyboard)
4. Check accessibility basics

## Step 5: Deliver

Save to the user's requested location or `assets/Activities/`.

Report: activity type, estimated engagement time, and any customization options built in.
