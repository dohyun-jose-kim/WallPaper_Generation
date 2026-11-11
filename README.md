# WALL-E — wallpaper engine made by DH-thejose

WALL-E is a local command-line tool for macOS on Apple Silicon. It turns one content photo into four 8-bit RGB PNG wallpapers, keeping the complete photo sharp and proportional.

Version **0.0.2** is being prepared for review. No new rendering features are being added during public-release preparation. There is no published installer release yet; you can run from a source checkout or build and install a local bundle.

| File suffix | Style | Renderer |
| --- | --- | --- |
| `.1.png` | Blurred background | S1 — Pillow + NumPy |
| `.2.png` | Gallery frame | S1 — Pillow + NumPy |
| `.3.png` | Frosted glass | D3 — TypeScript + React in Chromium |
| `.4.png` | Gradient | S2 — libvips + pyvips |

[Project status](docs/PROJECT_STATUS.md) · [Design and interfaces](docs/pipeline-design.md) · [Verification](docs/verification.md) · [Installation](packaging/README.md) · [Changelog](CHANGELOG.md)

## Quick start from source

The supported platform is **macOS ARM64**. Before setup, install Git, Apple's Command Line Tools, uv, and Node.js with npm. Setup downloads the pinned Rust/Python toolchains, dependencies, and Chromium into ignored project storage. Run it from a fresh checkout; see the [tool shelf](Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/README.md) before recreating an existing environment.

From the repository root:

```sh
./scripts/setup-dev.sh

WALLE_BIN="$PWD/orchestrator/target/debug/wall-e"
WALLE_WORKSPACE="$HOME/Pictures/WALL-E"

"$WALLE_BIN" --help
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" init
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" doctor
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" render "/absolute/path/to/photo.png" --preset FHD
```

Replace the photo path with your own single-frame JPEG or PNG. A successful render prints a job ID followed by `complete`. Open the output folder on macOS with:

```sh
open "$WALLE_WORKSPACE/wall-pic-out"
```

To use an installation separate from the source checkout, follow the [local bundle installation guide](packaging/README.md). Installed users do not need Rust, Node.js, npm, uv, or a separately installed Python. The installer does not add a command to PATH automatically; invoke the installed executable by its full path or use a launcher you explicitly requested.

## Commands and target settings

| Command | Purpose |
| --- | --- |
| `init` | Create workspace folders, local settings, and state |
| `doctor` | Check the engine, Chromium/WebGL, SQLite, and OS monitoring |
| `render` | Process one or more photo paths into four wallpapers per photo |
| `resume` | Reuse specified job IDs and their stored settings |

`--workspace` defaults to the current directory. Use the same workspace when resuming a job. Relative photo and reference paths resolve from the directory where you run the command, not from the workspace. `render` accepts explicit file paths; it does not automatically scan `wall-pic-in/`.

After defining `WALLE_BIN` and `WALLE_WORKSPACE` as above:

```sh
# Multiple content photos, one target size
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" render one.jpg two.png --preset QHD

# Portrait preset, or custom dimensions with an 8% border per edge
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" render photo.png --preset FHD --swap
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" render photo.png --width 1080 --height 1920 --border 8

# Match the displayed dimensions of an existing wallpaper
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" render photo.png --reference existing-wallpaper.png

# Replace the example ID with the ID printed for your job
"$WALLE_BIN" --workspace "$WALLE_WORKSPACE" resume WALL-E_YYYYMMDD_001
```

A **content photo** provides the foreground. A **wallpaper reference** supplies only the target dimensions and ratio, after EXIF orientation. One command uses one target size for every content photo. Content-photo orientation does not change that target.

Choose one target mode: `--preset`, `--width` together with `--height`, or `--reference`. If none is supplied, workspace defaults apply: initially **1920 × 1080** with a **5% border per edge**.

| Preset | Width × height |
| --- | --- |
| `FHD` | 1920 × 1080 |
| `QHD` | 2560 × 1440 |
| `UHD` | 3840 × 2160 |
| `WUXGA` | 1920 × 1200 |
| `WQXGA` | 2560 × 1600 |
| `Ultrawide` | 3440 × 1440 |

Preset names are case-sensitive. `--swap` swaps the axes of a named preset. `--border` accepts **3–20 percent per edge**; the photo is proportionally fitted inside the remaining area, enlarged if needed, and centered. Pixel-based visual effects scale with the shorter canvas dimension.

Each dimension must be **512–8192 pixels**, with at most **16,777,216 total pixels**. Width/height ratios from **0.5 through 2** are accepted normally; ratios from **1/3 through 3** are allowed with a composition warning outside that central range. More extreme ratios require manual layout customization. Oversized wallpaper references are rejected without resizing. These are validation limits, not performance guarantees; resource admission can still refuse a valid target.

`--brand` changes the output prefix: 1–48 ASCII letters, digits, hyphens, or underscores. Workspace defaults are stored in `.wallpaper/settings.json`. For example:

```json
{"brand":"WALL-E","width":1920,"height":1080,"border":0.05}
```

The settings file uses a fraction for `border` (`0.05` means 5%), while the CLI uses a percentage (`--border 5`).

## Input handling and output files

WALL-E accepts single-frame JPEG and PNG files. It applies orientation and converts valid embedded color profiles to sRGB, treats untagged RGB/grayscale as sRGB, and composites transparency onto `#16181D`. Originals are opened read-only. Exported PNGs are rebuilt from pixel data without embedded metadata.

Invalid profiles, untagged CMYK, animated/multi-frame inputs, files larger than **200 MiB**, and images above **100 million decoded pixels** are rejected. Other valid jobs continue. Some phone files named `.JPG` are multi-frame MPO containers and are unsupported in this version.

A complete, verified set appears under your workspace:

```text
wall-pic-out/
  YYYYMMDD/
    WALL-E_YYYYMMDD_001/
      WALL-E_YYYYMMDD_001.1.png
      WALL-E_YYYYMMDD_001.2.png
      WALL-E_YYYYMMDD_001.3.png
      WALL-E_YYYYMMDD_001.4.png
```

The local date is assigned when a job number is allocated. New runs get new numbers: `001`–`999`, then `a001`–`z999`, then `aa001` onward. Retries and explicit resume retain their identities. Resume requires unchanged input content and uses the original job's stored settings. A valid completed set is reported as already complete; different existing outputs are never overwritten.

## Architecture

```text
USER
  Content photos + one target setting + optional wallpaper reference
                              |
                              v
+------------------------------------------------------------------+
| RUST CLI / ORCHESTRATOR                                          |
| Resolve settings and workspace paths; validate the target        |
| Allocate job IDs in SQLite; queue photos and monitor resources   |
| Start workers; grant one Chromium slot; collect events/results   |
+------------------------------------------------------------------+
           | Versioned JSON Lines job request and browser grant
           v
+------------------------------------------------------------------+
| INDEPENDENT IMAGE ENGINE - Python + TypeScript                   |
| Read original -> apply orientation -> convert to sRGB            |
| Rebuild clean pixels -> fit the complete photo to the canvas     |
|                                                                  |
|  .1 S1 Blur    .2 S1 Gallery    .3 D3 Frosted    .4 S2 Gradient  |
|                                                                  |
| Restore the sharp foreground as the final layer                  |
| Export RGB PNGs; verify dimensions, chunks, CRCs and foreground  |
+------------------------------------------------------------------+
           | Events + artifact paths, hashes, checks and timings
           v
+------------------------------------------------------------------+
| RUST PUBLICATION                                                 |
| Check the complete result; journal it; atomically publish 4 files|
| Write sanitized logs and status; remove temporary image files    |
+------------------------------------------------------------------+
                              |
                              v
               wall-pic-out/YYYYMMDD/JOB_ID/
```

The engine receives explicit paths and resolved settings; the orchestrator owns workspace layout, naming, scheduling, and publication. The reusable package lives in `Photo-to-Wallpaper-Rendering-Engine/src/wallpaper_engine/`. Historical comparison entry points remain in that engine's `code/` directory. The production D3 browser bundle is separate from the comparison adapter. See the [pipeline design](docs/pipeline-design.md) and [JSONL protocol](contracts/README.md) for details.

## Runtime behavior and current limitations

The interface is command-based. It has no interactive file picker, progress bar, or built-in preview. Terminal output primarily reports completion or a sanitized failure code; detailed stage and resource events are in the workspace's `logs/` directory. Press **Ctrl+C** to stop admission and cancel managed workers.

One CLI run owns a workspace at a time, while photo jobs within that run may execute concurrently. Rust samples CPU, available memory, and worker process trees every second, reserves memory before admission, and permits one Chromium rendering job at a time. Monitoring failure stops managed work. These controls are sampled safeguards, not a hard OS CPU cap or a complete GPU-memory measurement.

Private state in `.wallpaper/state.sqlite` retains source paths needed for resume. Application logs omit source filenames, source paths, metadata values, image bytes, and raw library errors. Logs rotate at 10 MiB; closed segments are retained for up to 30 days within a 250 MiB budget. Managed temporary images are cleaned up after completion or terminal failure.

Common failure codes include `invalid_profile`, `untagged_cmyk`, `resource_refused`, and `browser_startup`. A plain invalid-input message can also mean an unsupported format or unreadable file. Run `doctor` to check environment failures. Browser and process monitoring checks need ordinary macOS process access and can fail in restrictive sandboxes.

## Verification

After source setup, these checks use synthetic inputs and do not require private comparison photos:

```sh
./scripts/cargo.sh fmt --check
./scripts/cargo.sh clippy --locked --all-targets -- -D warnings
./scripts/cargo.sh test --locked -- --include-ignored
./scripts/cargo.sh build --locked
.venv/bin/python -m pytest \
  Photo-to-Wallpaper-Rendering-Engine/code/tests \
  Photo-to-Wallpaper-Rendering-Engine/tests \
  tests/integration/test_cli.py -q
```

`./scripts/check.sh` additionally runs the eight-image baseline comparison. That final step requires private files under the ignored engine `results/` tree, so the complete script cannot pass from a fresh public checkout alone. The [offline comparison report](Photo-to-Wallpaper-Rendering-Engine/plan-docs/build-n-compare-0.0.1/index.html) likewise references local images that are not included in Git.

Build a local bundle and test its installation lifecycle with:

```sh
.venv/bin/python scripts/build-release.py
.venv/bin/python tests/integration/check_install.py
```

These commands build and test locally; they do not upload a release or create a Git tag. Verification results and their limits are recorded in [docs/verification.md](docs/verification.md).

## Project status

Feature development is paused while documentation and publication readiness are reviewed. The user plans to handle the PR, clean up branches, and then make the repository public. Version `0.0.2` is prepared in the packages; the `v0.0.2` tag is reserved for the final merged commit. The existing `v0.0.1` tag is retained.

[Linux support](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/4) and [Windows support](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/5) remain follow-up work. See [project status](docs/PROJECT_STATUS.md) and [decisions](docs/DECISIONS.md) for the implementation record and accepted choices.
