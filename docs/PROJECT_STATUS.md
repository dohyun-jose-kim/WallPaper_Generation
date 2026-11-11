# Project status

See [decisions](DECISIONS.md), [pipeline design](pipeline-design.md), and [verification evidence](verification.md).

## Completed comparison

- `1917a16` — clean preparation, metadata removal, PNG checks and tests.
- `782ac75` — 54-case renderer comparison, measured results, offline report and rating lookup.
- `243134e` — selected styles and accurate pipeline status.
- [PR #3](https://github.com/dohyun-jose-kim/WallPaper_Generation/pull/3) merged into `dev` as `159e9bc` with a merge commit. Existing branches retained.
- All 54 output hashes match the preserved run `20261111T023907Z-52cf6f`. Eleven positive-rating `a` renames resolve without changing filenames, images, ratings or the original manifest.
- S1 Blur, S1 Gallery, D3 Frosted and S2 Gradient selected for both orientations.

## Pipeline implementation

All pipeline work is on `feat/wallpaper-pipeline`, published for review in [draft PR #6](https://github.com/dohyun-jose-kim/WallPaper_Generation/pull/6). Usage and verification records were committed in `9fd6417`.

- `03fd49f` — reusable engine package, separate D3 production entry point and packaged JavaScript, variable targets/borders, input policy, exact foreground restoration.
- `3dd43fa` — Rust CLI, protocol, durable publication and resource supervision.
- `59f4d1d` — strict workspace settings and specific sanitized color-input errors.
- Rust CLI: init/render/resume/doctor; preset/custom/reference targets, SQLite identities, same-input resume, result journal and atomic complete-set publication.
- Persistent sysinfo monitor, CPU/memory admission, growing reservations, one browser slot, deadlines, bounded JSONL, one transient retry, process-group cancellation and temporary-image cleanup.
- Private state and sanitized Rust-owned logs with rotation and retention.
- `c48cfb6` — pinned developer scripts, offline distribution, selected-prefix installation, optional launcher, upgrade validation, rollback and owned-file uninstall.
- Linux [#4](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/4) and Windows [#5](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/5) created as follow-up work.

## Verification

See the [evidence record](verification.md) for commands and exact coverage. Eight selected FHD outputs match the preserved baseline pixels. Tests cover image preparation and export, target geometry and ratios, resource policy, transactional allocation, browser serialization, worker faults, cancellation, privacy, resume, collision protection and installation lifecycle. The local release artifact is built on this branch, without publication.

Original comparison `.JPG` inputs are multi-frame MPO containers. Production rejects them as specified. Baseline parity uses their preserved clean single-frame PNG preparations; historical comparison preparation retains its original first-frame behavior.

## Remaining and deferred

Implementation is ready for review; the pipeline branch is not merged. Linux and Windows support, release publication/signing/notarization, main integration, tags, branch deletion and document archiving remain deferred. Engineering size/resource limits do not imply performance certification across all allowed dimensions or hardware.
