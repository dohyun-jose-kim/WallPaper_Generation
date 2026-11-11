# Build and Compare 0.0.1

Completed 2026-11-11: all 54 cases passed in run `20261111T023907Z-52cf6f`. All image hashes verified during closeout, including 11 positive-rating `a` renames. The original manifest is preserved. [Report](index.html), [selection](tool-selection.md), [current pipeline status](../../../docs/PROJECT_STATUS.md).

The following specification records the comparison contract. Historical future-tense language below describes the original experiment, not current implementation status.

## Inputs and image geometry

Read only these originals from repository-root `data/WallPaper_v0.1_2026-10-28/`. Keep originals unchanged; compare SHA-256 before and after the run.

| ID | File | Display orientation | Expected prepared size |
| --- | --- | --- | --- |
| portrait-01 | IMG_0622.JPG | Portrait | 729 × 972 |
| landscape-01 | IMG_1003.JPG | Landscape | 1296 × 972 |

Output is **1920 × 1080, RGB, 8-bit PNG**. After EXIF orientation and color conversion, fit the complete photo inside 1728 × 972 using `scale = min(1728 / width, 972 / height)`. Proportional enlargement is allowed. Round each dimension to the nearest pixel; center using integer coordinates (floor the remaining margin divided by two). Never crop, stretch, or compress the foreground. Record the shared scale and integer rounding.

Restore the prepared foreground as the final layer, pixel-for-pixel. Blending, distortion, and shadows affect only the area outside its protected rectangle. A glass pane extends 32 px beyond each side of the photo over the common blurred extension. Keep the photo sharp. Record native corner-shape differences.

## Matrix and starting treatment

| Method | Treatment | Tools | Images |
| --- | --- | --- | ---: |
| Solid color | Source median RGB | S1, S2 | 4 |
| Gradient | Vertical interpolation between median colors of top and bottom 10% of prepared source | S1, S2 | 4 |
| Blurred background | Proportionally enlarge duplicate, crop duplicate to fill, blur | S1, S2 | 4 |
| Edge extension | Repeat boundary pixels into added area, blur | S1, S2 | 4 |
| Mirror extension | Reflect source into added area, blur | S1, S2 | 4 |
| Gallery frame | Dark background, light matte, soft shadow | S1, S2 | 4 |
| Glass: clear | Low blur, moderate refraction | All five | 10 |
| Glass: frosted | Higher blur, same basic geometry | All five | 10 |
| Glass: strong edge | Stronger refraction and edge light | All five | 10 |
| **Total** | | | **54** |

Background blur starts at standard deviation 32 px. Gallery background is `#16181D`, matte is `#E9E5DC`, matte width is 24 px. Record any additional implementation choices, including shadow settings, resampling, masks, corner radius, and sample-strip rounding. Native glass numbers are test presets and do not imply equal optics across tools.

## Reusable preparation and clean export

1. Apply `ImageOps.exif_transpose()`.
2. Convert valid embedded profiles to sRGB with `ImageCms`. Report invalid profiles as a preparation error rather than silently treating them as valid.
3. Treat untagged RGB input as sRGB and record that assumption. Record unsupported input modes explicitly.
4. Rebuild the image from pixel bytes with `Image.frombytes()`.
5. Save without EXIF, XMP, IPTC, comments, thumbnails, ICC profiles, or copied encoder information.
6. Apply the same clean writer to prepared previews, results, and thumbnails.

Independently parse exported PNG structure. Permit only `IHDR`, `IDAT`, and `IEND`; reject trailing data. Verify dimensions, bit depth, RGB color type, chunk boundaries, ordering, and CRCs. Log metadata field names if needed, never their values.

API references: [orientation](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose), [color conversion](https://pillow.readthedocs.io/en/stable/reference/ImageCms.html), [pixel buffer](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.frombytes).

## Environment contract

Use uv-managed **ARM64 Python 3.12** in repository-root `.venv`; the installed patch version is **3.12.14**. Do not use Miniforge. The prior CPython 3.9.6 environment is backed up in ignored local storage.

| Initial package pin supplied by plan | Version |
| --- | --- |
| Pillow | 13.0.0 |
| NumPy | 2.5.4 |
| pyvips | 3.2.0 |
| pyvips-binary | 8.18.7 |
| Playwright | 1.65.0 |
| psutil | 7.2.2 |
| pytest | 9.2.0 |

These pins were rechecked against published metadata and installed without changes. Transitive runtime and build dependencies were hash-locked **before installation**. Preserve that procedure for future changes. The pyvips wrapper build succeeded and uses its bundled native library; full rendering remains untested.

Use installed Node.js 26.8.1 and npm 11.19.0, verifying actual versions before use. Use esbuild 0.28.0 and React/React DOM 18.3.1 for D3, with a project-owned npm lockfile. Browser adapters must not rely on the inconsistent/missing upstream locks described in the procedures.

Use Playwright's matching Chromium, 1920 × 1080 viewport, device pixel ratio 1, browser zoom 100%. Inspect final display in Brave separately and record its version. [Browser requirements](https://playwright.dev/python/docs/browsers).

## Resource control and measurement

Run one renderer case at a time. Set supported CPU thread controls to 12 and record supported/unsupported controls. Stop the active test process tree above **36 GiB** observed memory. Stop if system available memory remains below **20%**; the implementation must record its sampling interval and sustained-low-memory window. The 80% ceiling is not a utilization target.

Allow GPU acceleration and record actual backend plus any software fallback. There is no reliable universal browser GPU 80% limit. Process-tree memory is not a complete GPU-memory measurement.

Initialization timeout: **120 seconds**. Render/export timeout: **60 seconds** per run. Record initialization separately. For each case, warm up once, then measure three warm renders; report median time and peak observed process-tree memory. Compare decoded pixels across the three measured runs and report differences. Blocked/failed cases remain in their positions; continue independent cases without substituting a different renderer.

## Checks and HTML report

| Check | Acceptance rule |
| --- | --- |
| Dimensions | Exactly 1920 × 1080, RGB, 8-bit |
| Source preservation | Protected rectangle equals prepared source pixels exactly |
| Proportions | Shared scale factor with integer rounding only |
| Metadata | Only permitted chunks; no trailing payload |
| Originals | Before/after file hashes unchanged |
| Repeatability | Compare three warm renders; report every pixel difference |
| Glass activity | Effect-on differs from effect-off outside protected rectangle |
| Resources | Runtime, process-tree memory, backend recorded; stop rules enforced |
| Browser export | No incomplete textures, missing layers, or capture errors |

The main deliverable will be `plan-docs/build-n-compare-0.0.1/index.html`, generated during implementation. Provide separate portrait/landscape views, large images, method/tool/variant filters, two-result side-by-side selection, and 100% zoom for seams and edges. Short labels show method, tool, preset, and status. Expandable details contain settings, revisions, measurements, and errors. Include failed cases in expected positions.

Use sanitized source previews. Embed report data so `file://` works without a server; use no external fonts, scripts, or image services. Keep result images in ignored local storage and reference them with relative paths. Track the template and concise findings, not private photo data. Technical checks determine eligibility; the user selects preferred appearance. Recommend tools only after reviewing actual quality, reliability, timing, memory, and adapter complexity.

## Storage

All following paths are under `Photo-to-Wallpaper-Rendering-Engine/`:

| Path | Contents |
| --- | --- |
| tool-package-shelf/ | Source manifest, separate project adapters, dependency locks, attribution, ignored upstream downloads |
| plan-docs/build-n-compare-0.0.1/ | This plan, matrix, procedures, HTML report, selection record |
| plan-docs/reseatch-0.0.1/ | Future AI research; spelling retained as requested |
| results/build-n-compare-0.0.1/ | Ignored prepared photos, outputs, thumbnails, raw run files and local review artifacts |

Keep browser binaries and upstream downloads in ignored local storage. Preserve upstream source unchanged; record revisions, inspected dependency files, licenses, fetched-file hashes, and findings. Track code/settings/source references/templates and concise findings.

## Required Git and execution order

1. Write the plan and research documents; mark older plans as historical.
2. Prepare a documentation commit on `docs/extension-research`, preserving existing relevant work.
3. Show the **exact staged diff and proposed commit message**.
4. **Wait for user confirmation immediately before committing.** This is an explicit user-plan requirement.
5. After confirmation, commit, push, open/review the PR into `dev`, run applicable checks, and use **merge commit** after checks pass.
6. Verify the branch is merged, then delete only `docs/extension-research` locally and remotely. Preserve unrelated branches.
7. Check `feat/style-comparison` for unique work and update it from `dev` without overwriting unique changes.
8. Implement preparation, S1, D1, D2, D3, then S2; run the complete matrix and produce/verify the HTML report.

Do not merge into `main` or create a release tag. Installation and synthetic initialization now pass. Full scene compatibility, useful settings, repeatability, performance, and winning tools remain unproven until measured.
