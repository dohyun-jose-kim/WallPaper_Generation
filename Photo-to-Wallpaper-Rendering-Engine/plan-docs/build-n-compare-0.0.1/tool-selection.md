# Tool selection record

Status: **Four methods selected** after user image review on 2026-11-11: Blurred background, Gallery frame, Glass: frosted, and Gradient. Method selection is complete for this comparison. The future single-image pipeline remains a separate task.

## Selected methods

Carry these methods forward for portrait and landscape photos. The tool assignments below follow the user's positive file ratings and explicit selections. Use the same method, tool, and starting settings for both orientations; adapt geometry proportionally to the source photo.

| Method | Tool | Visual review evidence |
| --- | --- | --- |
| Blurred background | S1 — Pillow + NumPy | Portrait and landscape marked `a` |
| Gallery frame | S1 — Pillow + NumPy | Portrait and landscape marked `a` |
| Glass: frosted | D3 — rdev | Portrait and landscape marked `a`; Frosted explicitly selected |
| Gradient | S2 — libvips + pyvips | Portrait marked `a`; landscape explicitly selected in conversation |

Keep the tested settings as the starting values. The user explicitly selected landscape S2 Gradient to keep the methods consistent across orientations. All eight selected method/orientation combinations are now accepted. No further selection review is pending.

Solid color, Edge extension, Mirror extension, Glass: clear, and Glass: strong edge are not carried forward in the current selection. Preserve their comparison results for reference.

## Current glass setting

| Control | Selected value |
| --- | --- |
| Renderer | D3 — rdev |
| Preset | Frosted |
| Mode | `standard` |
| `blurAmount` | `0.375` |
| Resulting CSS blur | `16px` |
| `displacementScale` | `35` |
| `saturation` | `140` |
| `aberrationIntensity` | `2` |
| `cornerRadius` | `32` |
| `elasticity` | `0` |
| `overLight` | `false` |

Keep the existing tested geometry and composition: the pane extends 32 px beyond the photo, and the sharp prepared photo is restored as the final layer. The selected values match the existing D3 Frosted adapter. No new render is required to record this choice.

User-marked reference files in run `20261111T023907Z-52cf6f`:

- `portrait-01__glass-frosted__D3a.png`
- `landscape-01__glass-frosted__D3a.png`

The `a` suffix records a positive user rating. Clear also received a positive rating; the user then chose Frosted as the current setting. Preserve the comparison presets and results for reference.

## Comparison evidence

The completed run contains 54 cases with status `passed`. See the [comparison report](index.html) for per-case settings, checks, runtime, and observed process-tree memory. Process-tree memory is not a complete GPU-memory measurement.

No additional full comparison run is required to record this selection. Check any changed settings or future pipeline implementation separately. The selection record does not imply that the future single-image pipeline is implemented.
