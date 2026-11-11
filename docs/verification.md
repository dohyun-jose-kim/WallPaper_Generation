# Pipeline verification — 2026-11-11

[Status](PROJECT_STATUS.md) · [Design](pipeline-design.md) · [Decisions](DECISIONS.md)

Environment: macOS ARM64, Python 3.12.14, Rust 1.99.1, locked Python/Node dependencies and Playwright Chromium. Process/browser checks run with ordinary OS access. Restricted sandbox execution cannot launch Chromium; it produces a sanitized failure and no published set.

## Reproducible checks

`./scripts/check.sh` runs formatting, Clippy with warnings denied, Rust tests including process-monitor tests, Python unit/integration tests, and exact baseline comparison.

- Rust: 10 tests, covering name overflow (`999`, `a001`, `z999`, `aa001`), concurrent SQLite allocation/resume, CPU admission, memory headroom and aggregate thresholds, invalid-monitor samples, deadline boundaries, log rotation/retention/live segments, malformed workers, transient crash/startup retry, browser-slot contention, terminal invalid-input handling and publication collisions.
- Python/CLI: 53 tests, covering orientation, profiles, grayscale/palette/alpha, metadata removal, PNG chunks/CRCs/trailing data, original preservation, full-photo geometry at border limits, input guards, single-frame policy, protocol rejection, explicit export verification failures, custom/preset/reference targets, portrait/square output, ratio boundaries, oversized references, valid-job continuation, batch naming, exact foreground pixels, resume/collision protection, sanitized logs and cancellation cleanup.
- Baseline: all eight selected FHD wallpapers have exactly equal decoded pixels to the preserved comparison outputs. Uses clean preparation PNGs because production rejects the original MPO containers. No baseline image or manifest was rewritten.
- Comparison closeout: 15 comparison tests at closeout; all 54 output SHA-256 values rechecked, including 11 positive-rating renames. The comparison test suite remains part of the combined checks.

Memory-pressure and busy-CPU thresholds are tested with synthetic measurements; the checks do not deliberately exhaust the host's RAM or CPU. Actual process monitoring, worker crashes, serialized browser access and cancellation are exercised on macOS. Hardware/GPU memory is not completely measurable by this policy.

## Installation lifecycle

`.venv/bin/python scripts/build-release.py` assembles `dist/wall-e-macos-arm64/` locally. The manifest records each file hash and symlink target. `.venv/bin/python tests/integration/check_install.py` verifies:

- Plan-only mode makes no installation writes.
- Offline installation in a fresh temporary prefix outside the repository, with spaces in prefix/workspace/launcher paths.
- Final-location Python environment creation and packaged Chromium/WebGL startup.
- Real four-style rendering with PATH restricted to `/usr/bin:/bin` (no developer Rust, Node/npm, uv or Python required).
- A second build installs and validates before activation; the prior version remains available.
- A corrupted candidate is rejected without changing the active version.
- Rollback validates and reactivates the previous version.
- Uninstall removes only recorded application files and its unchanged launcher; workspace output hashes and unrecorded user files survive.

The bundle is a local build, not a published or notarized release. Tests use disposable installations; no permanent user installation or PATH/profile edits are made.

Final local artifact build ID: `a22dbb8bd265d6c1`. Manifest: `dist/wall-e-macos-arm64/manifest.json`. Compiled executable SHA-256: `b4181e2e30adb795d3fc05eb96c63a19f03e82ca11eaa406629d44d5fcc50547`. Final source checks: 10 Rust tests, 53 Python/CLI tests, all eight baseline comparisons; final offline lifecycle test passed. Artifacts remain ignored local files.
