# Workflow: 3D Activity

Generate interactive 3D simulations using Babylon.js. Use when the activity requires spatial reasoning, 3D objects, camera controls, or physics.

## Step 1: Define the Simulation

1. **Subject/Topic** — What concept does the simulation demonstrate?
2. **3D elements** — What objects, environments, or phenomena need rendering?
3. **Interactions** — What can the user manipulate? (rotate, drag, adjust parameters)
4. **Physics** — Does the simulation need physics (gravity, collisions, forces)?
5. **Target device** — Desktop priority, but should degrade gracefully on tablets

## Step 2: Design

Plan the simulation:
- **Scene layout** — Objects, camera position, lighting
- **User controls** — What parameters can be adjusted (sliders, buttons, direct manipulation)
- **Visual feedback** — How changes are reflected in real-time
- **Data display** — Any measurements, graphs, or readouts

Present the design for user approval.

## Step 3: Build

Generate a single, self-contained HTML file:

### Technical Requirements
- **Single file** — HTML, CSS, JS inline
- **Babylon.js via CDN** — Load from CDN (the only allowed external dependency)
- **Responsive** — Adapt to viewport size
- **WebGL fallback** — Show a clear error message if WebGL is unavailable

### Scene Standards
- Use `HemisphericLight` + `DirectionalLight` for balanced lighting
- Camera: `ArcRotateCamera` for orbit controls (most versatile)
- Ground plane for spatial reference
- Consistent unit scale (1 unit = 1 meter unless specified)

### UI Overlay
- Parameter controls (sliders, buttons) overlaid on the 3D canvas
- Semi-transparent control panel that doesn't obscure the simulation
- Real-time readouts for measured values

### Performance
- Keep polygon counts reasonable (target 60fps on mid-range GPU)
- Use instanced meshes for repeated objects
- Dispose of unused meshes and textures

## Step 4: Test

1. Verify 3D rendering and interactions work
2. Test camera controls (orbit, zoom, pan)
3. Verify parameter adjustments update the simulation
4. Check WebGL error handling

## Step 5: Deliver

Save to the user's requested location or `assets/Simulations/`.

Report: simulation description, controls, and any physics parameters used.
