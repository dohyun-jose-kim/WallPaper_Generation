# WALL-E pipeline design

See [status](PROJECT_STATUS.md) and [decisions](DECISIONS.md).

```text
USER: content photos + target settings + optional wallpaper reference
  |
  v
RUST ORCHESTRATOR
  resolve settings and workspace / validate targets
  allocate daily job IDs transactionally / queue and monitor resources
  start independent workers / serialize Chromium / collect JSONL events
  verify results / publish complete output directories atomically
  |
  | version 1 job JSONL -> events + browser-slot request <- grant
  v
INDEPENDENT ENGINE: Python + TypeScript
  read unchanged original / orient / convert sRGB / remove metadata
  fit full photo / render S1 Blur, S1 Gallery, D3 Frosted, S2 Gradient
  restore sharp foreground / export RGB8 PNG / verify chunks and pixels
  |
  v
Result: artifacts, hashes, checks, timings, backend -> Rust publication
```

## Boundaries and layout

`orchestrator/` owns CLI, scheduling, state, logs and publication. `contracts/` defines versioned messages. `config/` holds defaults and presets. The existing `Photo-to-Wallpaper-Rendering-Engine/` holds `src/wallpaper_engine`, `code/` comparison wrappers, `tests/`, `tool-package-shelf/`, `plan-docs/` and ignored `results/`. `packaging/` owns managed installation; `scripts/` development and release builds; `tests/integration/` whole pipeline verification. Ignored runtime paths: `wall-pic-in/`, `wall-pic-out/`, `logs/`, `.wallpaper/`, `dist/`.

Engine requests carry explicit source/work paths, width, height, border, styles and thread allowance. The engine does not choose workspace paths, brand or daily numbering. Standalone mode owns its browser slot. Unsupported protocol versions fail. Exit codes: 0 success, 2 invalid input/settings, 3 processing failure.

## Settings and rendering

Mutually exclusive preset, custom width/height, wallpaper reference (or default FHD). Presets: FHD 1920×1080, QHD 2560×1440, UHD 3840×2160, WUXGA 1920×1200, WQXGA 2560×1600, Ultrawide 3440×1440. Preset swapping allowed. Reference uses displayed EXIF-oriented dimensions exactly. One target per command.

Ratio r=w/h: 0.5–2 normal; 1/3–0.5 and 2–3 warn; outside 1/3–3 requires manual layout. Warning: “This aspect ratio may produce an awkward composition or an incomplete-looking background. The complete source photo will still be preserved.” Each dimension 512–8192; total ≤16,777,216. Fit inside (1−2×border) on each axis, proportionally, enlargement allowed, nearest pixel half-up, centered. Border default .05, range .03–.20. Pixel effects scale by min(w,h)/1080; dimensionless controls unchanged. D3 FHD: CSS blur 16, displacement 35, extension 32, radius 32.

Read originals only; orientation before stripping metadata, valid profiles to sRGB, untagged RGB/grayscale assumed sRGB, alpha on #16181D, invalid profile and untagged CMYK rejected. Reject animations/multiple frames and non-JPEG/PNG. Guards 200 MiB/100M decoded pixels. Rebuild pixels for prepared and exported images. PNG checks: IHDR/IDAT/IEND only, CRCs, RGB8 dimensions, no trailing data, exact foreground.

## Scheduling and durability

Refresh the same sysinfo monitor every second; successive CPU samples. Maximum jobs min(4,max(1,CPUs/4)); 80% thread budget divided by maximum jobs. Start one, admit additional after two CPU samples below 70%; stop admission at 80%. One Chromium slot. Reserve 2 GiB + 128×source pixels + 1024×output pixels, increase future reservations for observed peaks. Account for unused active reservations, preserve 25% available memory, aggregate managed memory ≤75% total. Two samples below 20% available or aggregate violation: terminate largest managed job. Monitor failure stops managed work. Never terminate unrelated apps.

Timeouts: init 120s, render/export stage 60s, resource/browser wait 300s, active job 900s. Retry once only for transient browser startup or unexpected worker crash. Continue independent jobs. Cancellation stops admission and process groups, then force termination after grace period.

Local allocation date determines `wall-pic-out/YYYYMMDD/BRAND_YYYYMMDD_001/BRAND_YYYYMMDD_001.{1,2,3,4}.png`. Sequence 001–999, a001–z999, aa001 onward. SQLite transactional allocation; resume requires identical input hash and settings; retries retain identity. Stage on destination filesystem and atomically rename only after all four pass verification; never overwrite another output.

Rust alone writes application JSONL logs with run/job IDs, stages, timings, backend, dimensions, resource samples, retries, errors, verification and publication. No filenames, source paths, metadata values, image bytes or raw errors. Rotate 10 MiB, closed segments 30 days/250 MiB, oldest first. Private state `.wallpaper/state.sqlite` may retain source paths. Remove temporary pixels after success/terminal failure.

## Installation and acceptance

Pinned Rust and Cargo.lock; ignored local developer downloads, no profile changes. Distribute executable, wheel, production browser assets, locks, defaults and attribution. User selects prefix; show locations/dependencies/launcher choice first. Python environment created at final path; matching Chromium; no runtime Rust/Node/npm. Validate upgrade before activation, retain previous version for rollback, uninstall owned files only, preserve workspaces.

Acceptance includes same-environment FHD baseline equality, preset/custom/portrait/square/reference geometry and ratio boundaries, input/color/orientation/privacy safeguards, naming concurrency/overflow/resume/collisions, resource/cancellation/crash tests, installation outside repo with spaces and without dev tools on PATH, upgrade/rollback/uninstall, and consistent docs. Release build/testing stays on pipeline branch; publication later.
