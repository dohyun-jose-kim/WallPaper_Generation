# Project status

See [decisions](DECISIONS.md), [pipeline design](pipeline-design.md), and [verification evidence](verification.md).

## Completed comparison

- `1917a16` — clean preparation, metadata removal, PNG checks and tests.
- `782ac75` — 54-case renderer comparison, measured results, offline report and rating lookup.
- `243134e` — selected styles and accurate pipeline status.
- [PR #3](https://github.com/dohyun-jose-kim/WallPaper_Generation/pull/3) merged into `dev` as `159e9bc` with a merge commit. The completed comparison branch was subsequently removed.
- All 54 output hashes match the preserved run `20261111T023907Z-52cf6f`. Eleven positive-rating `a` renames resolve without changing filenames, images, ratings or the original manifest.
- S1 Blur, S1 Gallery, D3 Frosted and S2 Gradient selected for both orientations.

## Pipeline implementation

The pipeline was merged into `dev` through [PR #6](https://github.com/dohyun-jose-kim/WallPaper_Generation/pull/6) as `7a1cbd1`. Usage and verification records were committed in `9fd6417`; English documentation and version 0.0.2 preparation were committed in `a9e7f5f`. The completed work branches have been removed locally and remotely; `main` and `dev` remain.

- `03fd49f` — reusable engine package, separate D3 production entry point and packaged JavaScript, variable targets/borders, input policy, exact foreground restoration.
- `3dd43fa` — Rust CLI, protocol, durable publication and resource supervision.
- `59f4d1d` — strict workspace settings and specific sanitized color-input errors.
- Rust CLI: init/render/resume/doctor; preset/custom/reference targets, SQLite identities, same-input resume, result journal and atomic complete-set publication.
- Persistent sysinfo monitor, CPU/memory admission, growing reservations, one browser slot, deadlines, bounded JSONL, one transient retry, process-group cancellation and temporary-image cleanup.
- Private state and sanitized Rust-owned logs with rotation and retention.
- `c48cfb6` — pinned developer scripts, offline distribution, selected-prefix installation, optional launcher, upgrade validation, rollback and owned-file uninstall.
- Linux [#4](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/4) and Windows [#5](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/5) created as follow-up work.

## Verification

See the [evidence record](verification.md) for commands and exact coverage. Eight selected FHD outputs match the preserved baseline pixels. Tests cover image preparation and export, target geometry and ratios, resource policy, transactional allocation, browser serialization, worker faults, cancellation, privacy, resume, collision protection and installation lifecycle. The local version 0.0.2 artifact passed installation lifecycle checks and remains unpublished.

Original comparison `.JPG` inputs are multi-frame MPO containers. Production rejects them as specified. Baseline parity uses their preserved clean single-frame PNG preparations; historical comparison preparation retains its original first-frame behavior.

## Public repository preparation

The English README review is complete, including the ASCII architecture, source/install examples, preset dimensions, CLI limitations, and the distinction between public-checkout tests and the private baseline comparison. No new product features were added during publication preparation.

The privacy audit found commit/tag identities and historical local paths. The user accepts the audited email and environment information being public, including through historical commits and PRs. Private test-photo files and generated outputs were not found in the scanned Git history and remain excluded. The existing four tracked building-photo examples remain part of the repository being published. Local runtime state, logs, and distribution artifacts remain ignored; repository visibility does not publish those files.

After confirming branch cleanup, the user authorized creating, reviewing, and merging a `dev` to `main` PR, tagging the final merge commit `v0.0.2`, verifying the English README/ASCII diagram/version on `main`, and then making the repository public. This supersedes the earlier deferral of main integration, tag creation, and visibility changes. Existing history and `v0.0.1` are preserved. No force push or history replacement is needed.

## Version and publication sequence

Rust package/lock metadata, the Python package/version response, and the local bundle manifest agree on **0.0.2**. The publication PR carries this status snapshot; its GitHub merge record, the remote `v0.0.2` tag, and repository visibility are the authoritative records for the subsequent publication steps. No GitHub Release or installer assets are included in this operation.

## Remaining and deferred

Linux [#4](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/4) and Windows [#5](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/5), installer distribution/signing/notarization, and document archiving remain follow-up work. Keep `main` and `dev`. Engineering size/resource limits do not imply performance certification across all allowed dimensions or hardware.
