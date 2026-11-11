# Project status

See [decisions](DECISIONS.md) and [pipeline design](pipeline-design.md).

## Completed

- Preparation committed as `1917a16`; originals preserved, RGB PNG checks and tests.
- All 54 comparison cases passed in run `20261111T023907Z-52cf6f`; 54 output hashes rechecked, 11 positive-rating renames resolved without changing the original manifest or images.
- Comparison tests: 15 passed with OS process-monitoring permission. Restricted sandbox correctly prevents the live process-monitor test.
- Four styles selected: S1 Blur, S1 Gallery, D3 Frosted, S2 Gradient.

## Current

Close comparison with three commits; PR into dev using a merge commit. Then implement all pipeline work on `feat/wallpaper-pipeline`.

## Remaining

Reusable engine package, variable geometry, Rust CLI and resource supervision, versioned protocol, transactional identities/resume, publication, private state and sanitized logs, managed installation and lifecycle tests, baseline and integration verification. Linux and Windows issues to be created.

No main merge, release, tag, branch deletion, or document archiving is authorized in this work.
