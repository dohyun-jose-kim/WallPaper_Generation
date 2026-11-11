# WALL-E — wallpaper engine made by DH-thejose

WALL-E is a local macOS ARM64 CLI. One content photo produces four PNG wallpapers while preserving the complete, sharp photo:

| Suffix | Style | Renderer |
| --- | --- | --- |
| `.1.png` | Blurred background | S1 — Pillow + NumPy |
| `.2.png` | Gallery frame | S1 — Pillow + NumPy |
| `.3.png` | Frosted glass | D3 — TypeScript + React in Chromium |
| `.4.png` | Gradient | S2 — libvips + pyvips |

[Project status and evidence](docs/PROJECT_STATUS.md) · [Decisions](docs/DECISIONS.md) · [Pipeline design](docs/pipeline-design.md) · [Comparison report](Photo-to-Wallpaper-Rendering-Engine/plan-docs/build-n-compare-0.0.1/index.html) · [Changelog](CHANGELOG.md)

## Use

After [managed installation](packaging/README.md), use your requested launcher or `PREFIX/current/bin/wall-e`:

```sh
wall-e --workspace "$HOME/Pictures/Wallpapers" init
wall-e --workspace "$HOME/Pictures/Wallpapers" doctor
wall-e --workspace "$HOME/Pictures/Wallpapers" render /absolute/photo.png
wall-e --workspace "$HOME/Pictures/Wallpapers" render one.jpg two.png --preset QHD
wall-e --workspace "$HOME/Pictures/Wallpapers" render photo.png --preset FHD --swap
wall-e --workspace "$HOME/Pictures/Wallpapers" render photo.png --width 1080 --height 1920 --border 8
wall-e --workspace "$HOME/Pictures/Wallpapers" render photo.png --reference existing-wallpaper.png
wall-e --workspace "$HOME/Pictures/Wallpapers" resume WALL-E_20261111_001
```

One command uses one target size. Default: 1920×1080 and 5% border per edge. `--border` accepts 3–20 percent. `--brand` changes the filename prefix (letters, digits, `-`, `_`, up to 48 characters). Workspace defaults live in `.wallpaper/settings.json`: `brand`, `width`, `height`, and fractional `border`.

Preset, custom dimensions, and wallpaper reference are mutually exclusive. A wallpaper reference supplies its displayed EXIF-oriented dimensions exactly. Presets: FHD, QHD, UHD, WUXGA, WQXGA, Ultrawide; `--swap` swaps preset axes. Content-photo orientation never changes the target.

Dimensions must be 512–8192 per axis and at most 16,777,216 pixels. Ratios 1:2 through 2:1 are accepted normally; 1:3 through 3:1 are accepted with a warning outside that central range. More extreme ratios require manual layout customization. Oversized references are rejected without resizing. These are validation limits, not claims of tested performance; resource admission may refuse a valid size.

Single-frame JPEG and PNG are accepted. Orientation and valid embedded profiles are applied before metadata removal; untagged RGB/grayscale is treated as sRGB. Transparency is composited onto `#16181D`. Invalid profiles, untagged CMYK, animated/multi-frame inputs, files above 200 MiB, and images above 100 million decoded pixels fail individually while other jobs continue. Some phone `.JPG` files are multi-frame MPO containers and are rejected in this version.

Outputs appear together only after all four pass checks:

```text
wall-pic-out/YYYYMMDD/WALL-E_YYYYMMDD_001/
  WALL-E_YYYYMMDD_001.1.png
  WALL-E_YYYYMMDD_001.2.png
  WALL-E_YYYYMMDD_001.3.png
  WALL-E_YYYYMMDD_001.4.png
```

New runs allocate new numbers; explicit resume retains the original identity and stored settings and requires matching input content. Different existing outputs are never overwritten. SQLite allocation continues through `999`, `a001` … `z999`, `aa001` onward. A workspace admits one CLI run at a time; that run can process multiple photos concurrently.

Rust monitors CPU, available memory and worker process trees every second, reserves memory, and permits one Chromium render at a time. Cancellation terminates managed process groups. Logs contain sanitized job events and resource measurements; private state retains paths needed for resume. Logs rotate at 10 MiB and retain closed segments for 30 days within 250 MiB. Temporary images are removed after completion or terminal failure. Monitoring failure stops managed work. These are sampled controls, not a hard OS CPU cap or complete GPU-memory measurement.

## Development and verification

Development requires uv and Node/npm; installed users need neither those tools nor Rust. `scripts/setup-dev.sh` installs pinned Rust and Python dependencies into ignored project storage without editing shell profiles. Existing dependency setup details remain in the [tool shelf](Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/README.md).

```sh
./scripts/setup-dev.sh
./scripts/cargo.sh build --locked
./orchestrator/target/debug/wall-e --workspace /tmp/wall-e-work doctor
./scripts/check.sh
.venv/bin/python scripts/build-release.py
.venv/bin/python tests/integration/check_install.py
```

Browser/process-monitor tests need ordinary macOS process access and fail inside restrictive sandboxes. The baseline check needs the preserved local comparison results and compares all eight selected images pixel-for-pixel. Private photos/results remain ignored by Git.

The independent engine accepts an explicit JSON job via `python -m wallpaper_engine.worker --request job.json`; see the [protocol](contracts/README.md). Existing comparison entry points remain under `Photo-to-Wallpaper-Rendering-Engine/code/`; reusable code lives in that engine's `src/wallpaper_engine/` package.

## Repository workflow

The comparison merged into `dev` through [PR #3](https://github.com/dohyun-jose-kim/WallPaper_Generation/pull/3). Pipeline work uses `feat/wallpaper-pipeline` with separate reviewable commits. Keep `main`, existing tags, branches and historical documents unchanged during this work. Release publication, branch deletion and archiving are deferred. [Linux support](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/4) and [Windows support](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/5) are follow-up issues.
