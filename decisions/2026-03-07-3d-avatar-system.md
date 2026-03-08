# 3D Avatar System — Babylon.js Character Models

**Date:** 2026-03-07
**Type:** CONTEXT-SYNC
**Source:** Git history (9 commits on Avatar3D, characterModels, CustomizeModal), current session debugging

## What Changed

Updated `current_priorities.md` to reflect the 3D avatar system as active (no longer just "avatar customization" of the 2D SVG). Also updated asset pipeline status from "planning" to Phase 1 complete.

## Previous State

- "Avatar customization" listed as SVG polish work (hair geometry, fabric textures)
- "3D asset pipeline" listed as planning, Phase 1 next sprint

## New State

- "3D avatar system (active)" — full Babylon.js 3D character model system deployed with Flux Store integration
- "3D asset pipeline" — Phase 1 complete (external glTF loading working in production)

## Technical Notes for Future Sessions

Key findings from the debugging session that future work should know:

1. **Quaternius GLB materials have alpha=0** — must force `mat.alpha = 1` on all materials after loading
2. **PBR materials need environment texture (IBL) to look correct** — without it, models are nearly black. Fix: convert PBR → StandardMaterial after load
3. **glTF stores colors in linear space** — StandardMaterial with strong lighting (hemi 1.4 + dir 1.0) compensates. No manual gamma correction needed.
4. **Kenney models have 0 animations** — removed from the model catalog. Only Quaternius animated models are usable.
5. **Camera alpha=-PI/2** faces the front of the model (Blender convention: models face -Z)
6. **Scene clearColor must be opaque** — transparent canvas bleeds the purple portal UI through

### Files involved
- `components/dashboard/Avatar3D.tsx` — core 3D renderer
- `components/dashboard/AvatarDisplay.tsx` — unified wrapper (3D or 2D fallback)
- `components/dashboard/CustomizeModal.tsx` — 2D/3D tab switcher
- `lib/characterModels.ts` — model manifest (8 models)
- `services/dataService.ts` — selectCharacterModel(), purchaseCharacterModel()
- `functions/src/index.ts` — FLUX_SHOP_CATALOG character model entries
- `firestore.rules` — selectedCharacterModel in allowed gamification sub-fields
- `types.ts` — CHARACTER_MODEL type, selectedCharacterModel, ownedCharacterModels fields
