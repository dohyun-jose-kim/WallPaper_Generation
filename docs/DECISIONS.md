# Decisions

See [status](PROJECT_STATUS.md) and [design](pipeline-design.md).

Accepted 2026-11-11:

- WALL-E — wallpaper engine made by DH-thejose; user-configurable brand.
- One content photo yields S1 Blur (.1), S1 Gallery (.2), D3 Frosted (.3), S2 Gradient (.4).
- Preserve the existing engine tree and comparison evidence. Package reusable code and build a separate D3 production entry point.
- macOS ARM64 first; Rust orchestrator and independent Python/TypeScript engine, versioned JSON Lines.
- Default 1920×1080, border 5% per edge (3–20% allowed), whole photo fitted and restored exactly.
- Target ratio 1/3 through 3 inclusive; warn outside 1/2 through 2. Dimensions 512–8192, at most 16,777,216 pixels. No force override or silent reduction.
- Pixel controls scale by min(width,height)/1080. At FHD retain comparison settings exactly.
- JPEG/PNG only, orientation and sRGB conversion, grayscale accepted, alpha onto #16181D, invalid profiles/untagged CMYK/multiframe rejected. Input guards: 200 MiB and 100 million pixels.
- SQLite transactional daily numbering, explicit resume, four verified files atomically published without replacing existing outputs.
- Resource and timeout defaults in the design are engineering limits, not performance claims; sampled controls are not an OS CPU cap or full GPU measurement.
- User-selected installation prefix, optional launcher, no PATH/profile edits. Preserve workspaces and previous installation for rollback.
- Comparison PR merges into dev with a merge commit; all pipeline changes on one branch. Main, release/tag creation, branch deletion and archiving deferred.

Replaced: older comparison documents' pending-selection status and merged-branch cleanup instructions. The supplied implementation plan is the current authority.

Implementation clarifications:

- Original comparison `.JPG` inputs are multi-frame MPO. Keep historical first-frame preparation reproducible, reject those containers in production, and use their clean prepared PNGs for exact renderer baseline checks.
- Brand characters are limited to ASCII letters/digits/hyphen/underscore, length 1–48, to keep output components portable.
- One orchestrator owns a workspace lock; photo jobs within that run remain concurrent. SQLite allocation also handles independent concurrent transactions.
- The managed distribution includes a relocatable Python runtime and matching Chromium, installs offline from hashed wheels, and retains all preceding versions until explicit uninstall. No system Python, Node/npm, or Rust is required at runtime.
- Atomic publication uses macOS `RENAME_EXCL`; Windows and Linux need platform-specific validation before support is enabled.
