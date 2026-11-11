# Renderer installation and implementation preparation

Installation completed on 2026-11-11 for Build and Compare 0.0.1. See [verified environment](../plan-docs/build-n-compare-0.0.1/environment-readiness.md). This shelf contains dependency locks, immutable source references and installation smoke checks. Wallpaper adapters, photo preparation, benchmark runner and comparison report are not implemented yet.

## Installed environment

- Root `.venv`: uv-managed CPython **3.12.14**, ARM64, selected by root `.python-version`.
- uv **0.12.11**, Node.js **26.8.1**, npm **11.19.0** were already installed; no global upgrades performed.
- Python pins: Pillow 13.0.0, NumPy 2.5.4, pyvips 3.2.0, pyvips-binary 8.18.7, Playwright 1.65.0, psutil 7.2.2, pytest 9.2.0. Transitives are hash-locked in `requirements.lock`.
- pyvips build dependencies are separately hash-locked in `requirements-build.lock`; pyvips was built without an unpinned isolated build environment. The loaded native module belongs to pyvips-binary and reports libvips **8.18.7**.
- Project-owned npm lock: esbuild **0.28.0**, React/React DOM **18.3.1**, with transitive dependencies and integrity hashes.
- Playwright Chromium **158.0.8127.18**, revision **1254**, including matching headless shell and FFmpeg **1013**, installed in `browser-binaries/`.

The old Python 3.9.6 virtual environment is preserved at `.cache/venv-before-python312/` for reference. It is not used by the new environment; moving it back would be necessary before using its original absolute-path entry points. Miniforge was not used.

## Reproduce installation

Run these commands from the repository root. `run.sh` anchors paths to this repository, selects the root `.venv`, and places uv, Python downloads, npm cache and Playwright binaries in ignored project storage. Bootstrap commands below are for a fresh checkout; preserve an existing environment before recreating it.

```sh
SHELF=Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf
"$SHELF/run.sh" uv python install 3.12.14 --no-bin
"$SHELF/run.sh" uv venv --python 3.12.14 --managed-python .venv
"$SHELF/run.sh" uv pip install --python .venv/bin/python --require-hashes --only-binary :all: --requirement "$SHELF/requirements-build.lock"
"$SHELF/run.sh" uv pip sync --python .venv/bin/python --require-hashes --no-build-isolation "$SHELF/requirements-build.lock" "$SHELF/requirements.lock"
"$SHELF/run.sh" npm --prefix "$SHELF" ci --ignore-scripts --no-audit --no-fund
"$SHELF/run.sh" python -m playwright install chromium
"$SHELF/run.sh" python "$SHELF/acquire_sources.py"
```

`npm ci --ignore-scripts` deliberately skips lifecycle scripts; the installed ARM64 esbuild optional package works through esbuild's API and was verified by actual bundling. No D1/D2/D3 upstream install/build scripts were executed. TypeScript is transpiled by esbuild; this is not a TypeScript type-checking setup.

Root-engine `requirements.txt` points to the runtime lock. Include the build lock when rebuilding pyvips, as above. The checked-in locks target ARM64 macOS with Python 3.12; other platforms have not been tested.

## Verify installation without rendering photos

```sh
SHELF=Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf
"$SHELF/run.sh" uv pip check --python .venv/bin/python
"$SHELF/run.sh" python "$SHELF/acquire_sources.py" --verify-only
"$SHELF/run.sh" node "$SHELF/smoke-build.mjs"
"$SHELF/run.sh" python "$SHELF/smoke_environment.py"
# Optional, when Brave is installed at /Applications/Brave Browser.app:
"$SHELF/run.sh" python "$SHELF/smoke_environment.py" --brave
```

Checks use synthetic pixels and an isolated temporary browser profile, never the user's photos or normal browser profile. They exercise orientation, LittleCMS, PNG round-trip, libvips array/mapim/blur, dependency versions, esbuild, WebGL2, upstream D1/D2 constructors and shader compilation, D3/React DOM imports, viewport/DPR/zoom and a synthetic screenshot. D3 is not mounted, and no glass image is generated. Native browser launches may require an execution environment outside a restricted command sandbox.

Smoke bundles are ignored under `dist/smoke/`; raw results are ignored at `.cache/installation-smoke.json`. These are installation diagnostics, not matrix results or performance benchmarks. The synthetic Brave check does not replace final visual review of the future HTML report.

## Sources, local storage and attribution

`source-manifest.json` records the three full upstream revisions, acquisition findings, inspection hashes, and the 21 files needed locally. `acquire_sources.py` downloads only those files and verifies SHA-256; it refuses to overwrite an existing file with mismatched bytes. Files in `upstream/` remain unchanged. Project adapters must be kept outside `upstream/`.

See [attribution](ATTRIBUTION.md) and preserved license notices in `licenses/`. D2 declares MIT in its manifest and README but has no standalone license file at the selected revision; that finding is retained rather than inventing a notice. Demo photographs, videos, example applications, DOM capture dependencies and AI models were not acquired.

Ignored storage: `.cache/`, `browser-binaries/`, `upstream/`, `dist/`, `node_modules/`, repository-root `.venv`, and engine `results/`. Keep generated photos/previews/raw measurements in `results/build-n-compare-0.0.1/`. Source manifests, locks, attribution, project scripts and concise findings remain eligible for Git tracking.

`run.sh` sets supported thread-control environment variables to 12. It does not implement the matrix runner's process-memory watchdog, sustained-low-memory stop or case timeouts; those belong to the upcoming implementation.

## Updating dependencies

Keep the approved direct pins unless a documented change is needed. Regenerate locks before installation, inspect the resulting changes, then rerun smoke checks:

```sh
SHELF=Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf
"$SHELF/run.sh" uv pip compile "$SHELF/requirements-build.in" --python .venv/bin/python --python-platform aarch64-apple-darwin --generate-hashes --output-file "$SHELF/requirements-build.lock"
"$SHELF/run.sh" uv pip compile "$SHELF/requirements.in" --python .venv/bin/python --python-platform aarch64-apple-darwin --build-constraints "$SHELF/requirements-build.lock" --generate-hashes --output-file "$SHELF/requirements.lock"
"$SHELF/run.sh" npm --prefix "$SHELF" install --package-lock-only --ignore-scripts --no-audit --no-fund
```
