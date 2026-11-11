# Five renderer procedures

Status: planned, not acquired or executed in this documentation stage. Apply all geometry, protection, export, measurement, timeout, and failure rules in the [current plan](README.md).

## Acquisition before execution

Before downloading each repository, inspect manifests, lockfiles, installation scripts, required source files, and license notices **at the selected revision**. Record the full revision, dependency findings, source URLs, license text locations, and required file list in `tool-package-shelf/`. Fetch only needed files, hash them, and preserve upstream source unchanged in ignored storage. Project adapters remain separate.

The supplied prior inspection reports D1 lacks an npm lockfile and D2/D3 have manifest differences in their lockfiles. Recheck at the pinned revisions and use project-owned adapter dependencies/locks. Library and model licenses do not automatically cover demo assets; use only the local prepared photos as scene inputs.

## S1 — Pillow + NumPy

Reuse library padding, blur, masks, and composition. Generate solid, gradient, blurred background, edge, mirror, gallery, and all three glass presets for both inputs (18 cases). Build project-specific glass maps using a rounded-rectangle distance field, smooth edge displacement, bilinear sampling, and directional highlight. Label this a **project approximation**, not Apple's renderer. Store/share the numeric maps with S2. Restore the protected foreground last and use the clean PNG writer.

## D1 — medfa12/liquid-glass-react

Pinned revision: `a7d3c5ebd04b7efdf264a901cc521f77878744d1` ([renderer core](https://github.com/medfa12/liquid-glass-react/blob/a7d3c5ebd04b7efdf264a901cc521f77878744d1/src/renderer.ts)).

Check WebGL2. Supply the common backdrop, size the pane to photo plus 32 px per side, and freeze parameters. Render once and copy the frame immediately, before its drawing buffer may be cleared. Compose the protected photo and clean-export. Produce six glass cases. Record backend, full resolved native parameter object, corner geometry, and texture/capture checks. Failed WebGL initialization is a recorded failure, not permission to substitute another renderer.

## D2 — ybouane/liquidglass

Pinned revision: `59af227103795f06421a96e2c7d3dceb081decd2` ([GlassRenderer](https://github.com/ybouane/liquidglass/blob/59af227103795f06421a96e2c7d3dceb081decd2/src/GlassRenderer.ts)).

Use `GlassRenderer` directly to avoid the DOM-capture dependency path. Upload prepared backdrop, apply blur, render panel, then compose panel and background into one canvas. Restore protected photo and clean-export. Produce six glass cases. Record native values, geometry, WebGL/backend and initialization/export completion. A panel-only capture is not a complete result.

## D3 — rdev/liquid-glass-react

Pinned revision: `ac48eab18d1f7f444ae30002d240cae29c863a21` ([React component](https://github.com/rdev/liquid-glass-react/blob/ac48eab18d1f7f444ae30002d240cae29c863a21/src/index.tsx)).

Bundle the component using project-owned React/React DOM 18.3.1 and esbuild 0.28.0. Render the complete scene in Chromium, fix pointer state, disable elasticity, and use `standard` mode. Wait for all image decoding and layout completion; capture complete scene. Restore protected photo and clean-export. Produce six glass cases. Record native corner shape, fixed pointer coordinates, all native controls and browser errors. Additional modes are diagnostics outside the matrix.

## S2 — libvips + pyvips

Use bundled libvips, upstream array conversion and `mapim` examples. Generate the same 18 cases as S1, using the **same numeric glass maps**. Use bilinear interpolation and record boundary handling, rounding, blur and interpolation differences. Force lazy evaluation through pixel materialization/export before stopping timers. Restore prepared foreground and clean-export. Compare S1/S2 decoded pixel differences, runtime and memory rather than assuming equivalent numbers imply equivalent output.

## Initial glass controls

| Tool | Clear | Frosted | Strong edge |
| --- | --- | --- | --- |
| S1/S2 | Blur 4 px; displacement 4 px | Blur 12 px; displacement 4 px | Blur 4 px; displacement 12 px |
| D1 | `clear` preset | `regular` preset | `clear`, refraction amounts doubled |
| D2 | Blur 0.1; refraction 0.35 | Blur 0.5; refraction 0.35 | Blur 0.1; refraction 0.69 |
| D3 | Blur 0.0625; displacement 35 | Blur 0.375; displacement 35 | Blur 0.0625; displacement 70 |

Freeze every other native setting per tool and record resolved values from the pinned source. For project controls whose values were not specified, record the chosen constants before rendering. Equal native numbers do not establish optical equivalence. Use an effect-off diagnostic for each glass configuration, outside the 54-case matrix; compare outside the protected foreground and record changed-pixel counts. Do not claim activity if only the restored photo differs.
