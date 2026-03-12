---
name: 3d-activity
description: Use when someone asks to create a 3D simulation, build a Babylon.js activity, make a 3D interactive scene, generate a physics sim, or create a forensic science simulation.
model: claude-sonnet-4-6
effort: high
tools: [Read, Write, Glob, Bash]
---

## What This Skill Does

Generates a standalone, self-contained HTML file with an interactive 3D simulation using Babylon.js. The simulation integrates with Porter Portal's Proctor Bridge protocol and is optimized for student Chromebooks.

**Subjects:** AP Physics, Honors Physics, Forensic Science
**Output:** Single HTML file saved to `/home/kp/Desktop/Executive Assistant/assets/Simulations/<class>/`

For Babylon.js coding patterns, performance budgets, and lighting recipes, see [babylon-reference.md](babylon-reference.md).
For the example simulation to use as a structural reference, see [example-sim.md](example-sim.md).

---

## Step 0: Verify References

Before starting, verify that the required reference files exist and are readable:
1. Read `babylon-reference.md` (in this skill's directory) — must contain sections on engine setup, lighting, materials, and performance budgets
2. Read `example-sim.md` (in this skill's directory) — structural template for the output HTML
3. Read `references/portal-bridge.md` — Proctor Bridge protocol

If any file is missing or incomplete, stop and report the issue before generating code.

## Step 1: Parse Arguments

Extract from `<ARGUMENTS>`:

- **Topic/scenario** — the subject of the simulation (e.g., "projectile motion", "blood spatter analysis", "wave interference")
- **File paths** (optional) — paths to PDFs, images, or documents that provide additional context for the simulation goals

If file paths are provided, read each one using the Read tool. Use their content to understand:
- What the simulation needs to teach
- What equipment, apparatus, or scene elements to model
- What questions or assessment criteria to target
- Any specific diagrams, layouts, or visual references

If no arguments are provided, ask: "What topic should I build a 3D simulation for? You can also provide file paths to reference materials."

---

## Step 2: Ask Class and Mode

Ask the user two questions:

**Class:** Which class is this simulation for?
- AP Physics
- Honors Physics
- Forensic Science

This determines the output subdirectory under `/home/kp/Desktop/Executive Assistant/assets/Simulations/`.

**Mode:** Should this simulation be graded or exploratory?
- **Graded** — includes assessment questions, calls `PortalBridge.answer()` and `PortalBridge.complete()`
- **Exploratory** — sandbox/free-explore experience, only calls `PortalBridge.init()` and `PortalBridge.save()`

---

## Step 3: Design the Simulation

Before writing code, plan the simulation:

1. **Educational goal** — what concept or skill the student should understand after interacting
2. **3D scene elements** — what objects, environment, and props to build (be specific)
3. **Interactions** — what the student can do (click, drag, adjust sliders, apply forces, rotate camera, toggle views)
4. **Physics/logic** — what simulation logic drives the behavior (gravity, collisions, trajectories, evidence placement)
5. **UI overlay** — what information panels, controls, and feedback the student sees
6. **Assessment** (graded mode only) — what questions to ask, correct answers, and when to trigger them

---

## Step 4: Generate the HTML File

Write a single self-contained HTML file. Follow the structure and patterns in [babylon-reference.md](babylon-reference.md).

### File Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>[Simulation Title]</title>
    <style>/* All CSS inline */</style>
    <script src="https://cdn.babylonjs.com/babylon.js"></script>
    <script src="https://cdn.babylonjs.com/materialsLibrary/babylonjs.materials.min.js"></script>
</head>
<body>
    <script>/* Portal Bridge */</script>
    <canvas id="renderCanvas"></canvas>
    <div id="ui-layer"><!-- Overlay UI --></div>
    <script>/* Babylon.js scene + simulation logic */</script>
</body>
</html>
```

### Proctor Bridge — Always Include

```javascript
const PortalBridge = (() => {
    const send = (type, data) => {
        if (window.parent) window.parent.postMessage({ source: 'portal-activity', type, ...data }, '*');
    };
    return {
        init:     ()              => send('PROCTOR_READY'),
        save:     (state, q)      => send('SAVE_STATE',  { state, currentQuestion: q }),
        answer:   (id, ok, tries) => send('ANSWER',      { questionId: id, correct: ok, attempts: tries }),
        complete: (s, t, c)       => send('COMPLETE',    { score: s, total: t, correct: c })
    };
})();
window.addEventListener('load', () => PortalBridge.init());
```

- **Graded mode:** Call `PortalBridge.answer(questionId, correct, attempts)` when a student answers a question. Call `PortalBridge.complete(score, total, correct)` when the activity finishes. Call `PortalBridge.save(stateObj, currentQuestionIndex)` periodically.
- **Exploratory mode:** Call `PortalBridge.save(stateObj, 0)` periodically to preserve student progress. Do NOT call `answer` or `complete`.

### Dark Theme UI & Proctor Bridge

Use the shared dark theme and Proctor Bridge patterns from [portal-bridge.md](../../../references/portal-bridge.md).

### Babylon.js Scene Requirements

Follow the detailed patterns in [babylon-reference.md](babylon-reference.md). The reference file has everything — engine setup, camera, lighting, shadows, materials, models, post-processing, particles, and animation patterns. Read it before writing any simulation code.

**Critical rules to internalize** (these cause the most bugs when forgotten):
- Cap `devicePixelRatio` at **1.5** — Chromebooks choke on higher values
- Shadow maps at **1024**, MSAA samples at **2** — performance over fidelity
- **Three lights maximum** — hemispheric fill + directional key + optional accent
- **Never use blanket GlowLayer** — it blooms labels into unreadable white. Use `addIncludedOnlyMesh()` or skip GlowLayer entirely
- **No emissiveColor on PBR materials** unless the mesh is whitelisted in a GlowLayer. Use `albedoColor` + proper lighting instead
- **No Havok or Ammo.js** — implement physics manually in the render loop using `engine.getDeltaTime()`
- Build all models from **Babylon.js primitives** (boxes, cylinders, spheres, etc.) — no external model files
- Make environments **realistic** — lab tables, walls, terrain, not floating objects on a grid
- **Texture major surfaces procedurally** — use the `pbrTex()` helper with Canvas 2D painting (see babylon-reference.md "Procedural Textures" section). Floors, walls, ceilings, doors, furniture tops, and equipment panels should have painted textures (tile grout, brick mortar, wood grain, metal panels, etc.), not flat-color PBR. Flat-color `pbr()` is fine only for small parts like legs, bolts, and handles
- **Freeze all static meshes** after positioning — call `freezeWorldMatrix()`, `doNotSyncBoundingInfo = true`, and `material.freeze()` on every mesh that doesn't move. Set `scene.performancePriority = BABYLON.ScenePerformancePriority.Aggressive`
- **Use Thin Instances for repeated geometry** (10+ identical objects like desks, markers, chairs) — see babylon-reference.md "Thin Instances" section
- **Use GreasedLine for thick lines** (measurement lines, trajectory traces, reference lines) instead of CreateTube — see babylon-reference.md "GreasedLine" section. Exception: textured tape still uses CreateTube + DynamicTexture

---

## Step 5: Save the File

Save the HTML file to:

```
/home/kp/Desktop/Executive Assistant/assets/Simulations/<class>/<filename>.html
```

Where:
- `<class>` is the subdirectory matching the user's class choice: `AP Physics`, `Honors Physics`, or `Forensic Science`
- `<filename>` is a descriptive kebab-case name derived from the topic (e.g., `projectile-motion-sim.html`, `blood-spatter-analysis.html`)

---

## Step 6: Summary

After writing the file, provide a brief summary:
- File path where it was saved
- What the simulation covers
- What interactions are available
- Whether it's graded or exploratory
- Any notes about limitations or things the user might want to tweak

---

## Error Handling

Use the 5-step self-correction loop (Read → Research → Patch → Retry → Log). Max 3 loops.

- **Babylon.js scene blank/black:** Check engine initialization, verify canvas element exists, confirm at least one light is in the scene, check that camera target is set.
- **Performance below 30fps:** Reduce shadow map to 512, freeze more static meshes, switch to Thin Instances for repeated geometry, cut particle count.
- **GlowLayer blooming everything:** Use `addIncludedOnlyMesh()` to whitelist specific meshes, or remove GlowLayer entirely.
- **Physics behaving wrong:** Verify delta time usage (`engine.getDeltaTime() / 1000`), check unit scaling (PIXELS_PER_METER), ensure gravity sign is correct.
- **Proctor Bridge not firing:** Ensure `PortalBridge.init()` is called on `window.load` and `postMessage` source is `'portal-activity'`.
- **Escalate immediately:** Scientific accuracy questions (ask Kellen), ambiguous educational goals.

---

## Notes

- **Output ONLY the HTML file.** Do not add explanation or commentary before/after the file content — just write it with the Write tool.
- **No external assets.** Everything must be inline or from the Babylon.js CDN. All textures, models, and particle images must be procedurally generated.
- **Chromebook performance is critical.** Follow the performance budgets in [babylon-reference.md](babylon-reference.md). If in doubt, optimize for performance over visual fidelity.
- **Scientific accuracy matters.** Physics equations, forensic science principles, and educational content must be correct. Do not fabricate inaccurate science.
- **Mobile/touch support.** The ArcRotateCamera handles touch natively. Ensure UI buttons are large enough for touch (min 44px tap targets). Use `touch-action: none` on the canvas.
- **Do NOT use Havok or Ammo.js physics engines** — they require additional large CDN downloads. Implement physics logic manually (gravity, velocity, collisions) in the render loop, as shown in the example simulation.
- **Agent delegation.** After generating the HTML file, delegate to the project's specialized agents (always prioritize these over general-purpose):
  - **qa-engineer** — for validating the HTML output (accessibility of UI overlays, Proctor Bridge integration, Chromebook performance concerns). Delegate for graded simulations where correctness is critical.
  - **content-writer** — for reviewing instructional text, UI labels, and question wording within the simulation. Delegate when the simulation includes assessment questions or complex instructions.
  - Always use project agents first. Only fall back to general-purpose agents if project agents are unavailable.
