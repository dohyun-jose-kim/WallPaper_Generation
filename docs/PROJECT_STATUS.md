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

## Current priority: public-release preparation

Feature development is paused at the user's request. The active focus is English README documentation and removing unintended personal information before any visibility change. The root and engine README files are English. The current review adds an ASCII architecture, complete source/install examples, explicit preset dimensions, current CLI limitations, and a clear separation between public-checkout tests and the private baseline comparison. The tool-shelf README no longer describes implemented components as pending. The default `main` branch still contains the earlier README until an explicitly chosen integration or history-replacement operation occurs.

The privacy audit found commit/tag identities and local paths in historical documentation. The user accepts publication of the email address and the audited environment information, including information discoverable through old commits and PRs; these findings are no longer publication blockers under that preference. Test-photo files and generated outputs were not found in the scanned Git history and must remain excluded. Four tracked building-photo examples will be public if the repository is made public; their publication suitability remains to be confirmed. The ignored local executable also contains a developer build path; repository visibility does not publish that artifact. Artifact distribution remains a separate decision.

History replacement and a separate public repository were discussed as privacy options, but are not necessary solely to remove the information the user now accepts publishing. No history rewrite, force push, PR/issue deletion, repository deletion, or visibility change has been authorized or performed. Keep the existing repository and history during preparation. The user plans to handle the PR, clean up branches, and then make the repository public. Existing draft PR #6 remains available; the assistant will not create another PR, merge it, or delete branches during this documentation task.

## Version preparation

The user selected **0.0.2** for the completed revision, preserving the existing `v0.0.1` tag. Rust package/lock metadata, the Python package/version response, and the local bundle manifest are aligned to 0.0.2. The `v0.0.2` tag is reserved for the final merged commit after the user's PR; no tag or GitHub Release is created by this preparation.

## Remaining and deferred

Implementation is ready for review; the pipeline branch is not merged. Linux and Windows support, release publication/signing/notarization, main integration, tags, branch deletion and document archiving remain deferred. Engineering size/resource limits do not imply performance certification across all allowed dimensions or hardware.
