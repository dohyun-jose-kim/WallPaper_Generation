# Project status

See [decisions](DECISIONS.md) and [pipeline design](pipeline-design.md).

## Completed

- Preparation committed as `1917a16`; originals preserved, RGB PNG checks and tests.
- Renderer comparison committed as `782ac75`; selection/status as `243134e`. [PR #3](https://github.com/dohyun-jose-kim/WallPaper_Generation/pull/3) merged into dev as `159e9bc`; branches retained.
- All 54 comparison cases passed in run `20261111T023907Z-52cf6f`; 54 output hashes rechecked, 11 positive-rating renames resolved without changing the original manifest or images.
- Comparison tests: 15 passed with OS process-monitoring permission. Restricted sandbox correctly prevents the live process-monitor test.
- Four styles selected: S1 Blur, S1 Gallery, D3 Frosted, S2 Gradient.

## Current

Pipeline implementation on `feat/wallpaper-pipeline`: reusable engine and separate D3 production bundle complete. All eight selected FHD outputs match baseline pixels exactly; 41 Python tests passed. Rust orchestration and installation verification in progress. Linux [#4](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/4) and Windows [#5](https://github.com/dohyun-jose-kim/WallPaper_Generation/issues/5) opened.

The original comparison JPEG-named inputs are multi-frame MPO containers. Production rejects these as specified. Baseline parity uses their preserved clean single-frame PNG preparations; historical comparison preparation retains its original first-frame behavior.

## Remaining

Reusable engine package, variable geometry, Rust CLI and resource supervision, versioned protocol, transactional identities/resume, publication, private state and sanitized logs, managed installation and lifecycle tests, baseline and integration verification. Linux and Windows issues to be created.

No main merge, release, tag, branch deletion, or document archiving is authorized in this work.
