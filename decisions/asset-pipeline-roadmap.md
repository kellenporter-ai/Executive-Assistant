# Asset Pipeline Roadmap

**Date:** 2026-03-07
**Status:** Planning
**Tags:** DECISION, 3D, INFRASTRUCTURE

## Context

We currently build all 3D models from Babylon.js primitives inline in self-contained HTML files. This works for educational simulations but has a ceiling: complex models (realistic lab equipment, detailed crime scenes, anatomical models) look toy-like when built from boxes and cylinders. The Gemini deep research identified an industry-standard pipeline for high-fidelity web 3D that we can adopt incrementally.

## Current State (Phase 0)

- All geometry is procedural Babylon.js primitives
- All textures are DynamicTexture + Canvas 2D
- No external model files (.glb, .gltf)
- No asset compression tooling
- Simulations are single self-contained HTML files
- Target: Chromebook WebGL2

## Phase 1: External glTF Assets (Low Effort, High Impact)

**Goal:** Load pre-made .glb models instead of building everything from primitives.

**What changes:**
- Allow simulations to reference external `.glb` files hosted alongside the HTML
- Use `BABYLON.SceneLoader.ImportMeshAsync()` to load models
- Source models from free libraries (Sketchfab CC0, Kenney assets, Poly Pizza) or create in Blender
- Store assets in a shared `assets/models/` directory

**What stays the same:**
- HTML files remain the primary deliverable
- Procedural primitives still used for simple shapes (walls, floors, boxes)
- Chromebook performance budgets still enforced

**New skill/agent work:**
- Update 3d-activity skill to support a `--models` flag listing .glb files to include
- Update babylon-reference.md with glTF loading patterns
- Add model budget: max 50K triangles total per scene, max 10MB total asset size

**Tooling needed:**
- Blender (free, already available on Linux)
- `gltf-transform` CLI (`npm install -g @gltf-transform/cli`) for inspecting and optimizing models

**Decision point:** Do we host assets alongside sims (simple) or set up a CDN/asset server (scalable)?

---

## Phase 2: Meshoptimizer Compression (Medium Effort)

**Goal:** Compress .glb geometry for faster loading on school networks.

**What changes:**
- Run `gltf-transform optimize input.glb output.glb --compress meshopt` on all models before deployment
- Add Meshoptimizer decoder to sim HTML: `<script src="https://cdn.babylonjs.com/meshopt_decoder.js"></script>`
- Typical 40-60% reduction in geometry payload without visual loss

**Why Meshopt over Draco:**
- No heavy WASM decoder required (Draco needs ~300KB WASM blob)
- Optimizes GPU vertex cache ordering (faster rendering, not just smaller files)
- Better animation/morph target support for future animated models
- Faster decode = faster Time-to-Interactive on Chromebooks

**Tooling needed:**
- `gltf-transform` CLI (same as Phase 1)
- Add a `compress-models` script to package.json or a Makefile

---

## Phase 3: KTX2 Texture Compression (Medium-High Effort)

**Goal:** Eliminate VRAM blowout from texture-heavy scenes.

**What changes:**
- Convert all textures from PNG/JPEG to KTX2 format using Basis Universal
- Textures stay compressed in GPU memory (80% VRAM reduction)
- Auto-transcodes to device-native format (ASTC on Apple, S3TC on desktop, ETC on Android/ChromeOS)

**Critical details:**
- **Color textures** (albedo, emissive): encode with ETC1S mode (lossy, small files)
- **Data textures** (normal, roughness, AO): encode with UASTC mode (lossless math precision)
- **Normal map swizzling**: drop Z channel, move Y to alpha, reconstruct Z in shader. Use `gltf-transform uastc --input_swizzle rgb1 --normal_mode` flag
- Add KTX2 transcoder to sims: Babylon.js has built-in support via `BABYLON.KhronosTextureContainer2`

**Tooling needed:**
- `gltf-transform` with `--texture-compress` flags
- `toktx` CLI from Khronos for standalone texture conversion
- Automated pipeline script that detects texture type and applies correct encoding

**This is where the multi-agent pipeline from the Gemini research becomes valuable:**
- Architect agent: analyzes model, decides which textures get ETC1S vs UASTC
- Builder agent: runs gltf-transform commands
- Validator agent: checks output file size, verifies normal maps aren't corrupted

---

## Phase 4: High-Poly Baking Workflow (High Effort)

**Goal:** Photorealistic-looking models at low poly counts via normal map baking.

**What changes:**
- Model high-detail versions in Blender (sculpt mode)
- Retopologize to low-poly meshes (manual or Blender's Quadriflow)
- Bake normal maps, AO maps, and curvature maps from high-poly onto low-poly UV shells
- Export low-poly .glb with baked textures
- Compress via Phase 2 + Phase 3 pipeline

**This is the "proper" art pipeline.** Each asset goes through:
1. High-poly sculpt (Blender)
2. Retopology (Blender / Instant Meshes)
3. UV unwrap (Blender)
4. Bake maps (Blender / xNormal)
5. Material setup (Blender PBR -> glTF export)
6. Meshopt compress
7. KTX2 texture compress
8. Validate & deploy

**When this makes sense:**
- When we want lab equipment that looks *real* (microscopes, gas chromatographs, pipettes)
- When we want recognizable crime scene props (specific furniture, vehicles, weapons)
- When the "wow factor" of visual quality directly impacts student engagement

**When it's overkill:**
- Simple physics demos (ramps, pulleys, pendulums) — primitives are fine
- Anything where interaction matters more than visual detail

---

## Phase 5: WebGPU (Future — Hardware Dependent)

**Goal:** Unlock compute shaders and next-gen rendering when Chromebook support lands.

**What changes:**
- Switch engine init from WebGL2 to WebGPU when available
- Use compute shaders for particle simulations, fluid dynamics, large-scale data viz
- Snapshot rendering for static scenes (record draw calls once, replay every frame)
- Zero CPU overhead for scene traversal

**Blocker:** ChromeOS WebGPU support is experimental as of early 2026. Not actionable until student Chromebooks reliably support it. Monitor via `chrome://gpu` on test devices.

**Prep work we can do now:**
- Keep scenes structured so static elements are easily separable (already doing this with freezeWorldMatrix)
- Design simulation logic to be parallelizable (separate physics step from render step)

---

## Recommended Execution Order

| Phase | Effort | Impact | When |
|---|---|---|---|
| Phase 1: External glTF | Low | High — immediate visual quality jump | Next sprint |
| Phase 2: Meshopt | Low | Medium — faster loading | Same sprint as Phase 1 |
| Phase 3: KTX2 | Medium | High — VRAM savings critical for texture-heavy scenes | After we have 5+ external models |
| Phase 4: Baking | High | Very High — photorealistic quality | When we commit to a specific showcase sim |
| Phase 5: WebGPU | Low (prep only) | Future | When ChromeOS ships stable WebGPU |

## Open Questions

1. **Asset hosting:** Alongside HTML files? S3/R2 CDN? Firebase Storage?
2. **Blender skill level:** Do we invest time learning Blender sculpting, or source CC0 models and only do compression/optimization?
3. **Automation scope:** Full multi-agent pipeline (Architect/Builder/Validator) or simpler shell script for Phases 1-3?
4. **Budget per sim:** What's the max acceptable load time on school WiFi? (Current target: <3 seconds)
