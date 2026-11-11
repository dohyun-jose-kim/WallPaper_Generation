# Installation readiness — 2026-11-11

Status: **installation and synthetic smoke checks completed; implementation can begin**. No wallpaper adapters, source-photo processing, matrix runs, timing comparison, visual selection or completed HTML report exist yet. No AI models were downloaded.

## Resolved environment

| Component | Verified result |
| --- | --- |
| Platform | macOS 27.2.1, ARM64; 48 GiB unified memory, 15 logical CPUs |
| Python | uv-managed CPython 3.12.14, root `.venv`; prior 3.9.6 environment preserved in ignored cache |
| uv | Existing 0.12.11 |
| Python direct dependencies | All seven approved versions installed without changing pins |
| pyvips / libvips | pyvips 3.2.0 wrapper build succeeded; bundled pyvips-binary 8.18.7 native module verified, API mode enabled |
| Color conversion | Pillow 13.0.0 with LittleCMS 2.19; synthetic sRGB conversion passed |
| Node / npm | Existing 26.8.1 / 11.19.0 |
| Browser dependencies | esbuild 0.28.0; React and React DOM 18.3.1 |
| Chromium | Playwright 1.65.0, Chromium 158.0.8127.18 / revision 1254; matching headless shell and FFmpeg installed |
| Existing Brave | App version 156.1.98.63; browser engine reports 156.0.8078.80 |
| GPU backend | Chromium and Brave: ANGLE Metal Renderer, Apple M5 Pro; no software fallback detected |

Runtime/test and build dependencies each have a hash-locked requirements file. The project-owned npm lockfile includes integrity hashes. No upstream repository install scripts or npm lifecycle scripts were executed; esbuild's installed ARM64 binary was verified through the API.

## Completed checks

- `uv pip check`: all 16 installed distributions compatible; the count includes build dependencies.
- All seven Python direct versions match the plan. Python is ARM64 3.12.14 and the native libvips module belongs to the bundled binary distribution.
- Synthetic EXIF transpose, sRGB conversion, PNG pixel round-trip, libvips array conversion, identity bilinear `mapim`, Gaussian blur, and psutil memory access passed.
- All 21 selected upstream files match recorded SHA-256 values at the three specified full revisions.
- D1/D2/D3 unchanged entry points and React DOM bundle successfully with esbuild. This checks transpilation/bundling, not TypeScript semantic types.
- Chromium and Brave both expose WebGL2. D1/D2 constructors and shader compilation passed; D3 and React DOM exports load successfully. D3 component mounting and effect behavior remain untested.
- Synthetic capture is 1920 × 1080, DPR 1, zoom 1; center pixel matches the specified CSS color. No page errors were reported.

The first browser launch under the restricted command sandbox aborted. The same checks passed outside that sandbox using isolated temporary profiles. No existing browser profile was accessed. The Brave check is synthetic and headless; it does not replace the later visual check of actual results.

## Implementation handoff

Use the [installation and verification commands](../../tool-package-shelf/README.md), [source manifest](../../tool-package-shelf/source-manifest.json), and [attribution findings](../../tool-package-shelf/ATTRIBUTION.md). Raw inspection/downloads, smoke bundles and smoke JSON stay in ignored local storage. Only source references, dependency locks, preparation scripts and concise findings are intended for Git.

Next work starts with the common photo-preparation/export component, then S1, D1, D2, D3 and S2. Fill in detailed settings, measurement boundaries, watchdog timing, result states and retry behavior at the relevant implementation step, as requested. Keep all 54 matrix cases `planned` until actual execution. Installation checks do not make a renderer technically eligible or establish image quality/performance.
