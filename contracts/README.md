# Engine protocol version 1

Transport: UTF-8 JSON Lines, one object per line, maximum 65,536 bytes. Unknown versions/types fail the job. stdout is protocol only; stderr is never copied into application logs. Worker exit: 0 success, 2 invalid input/settings, 3 processing failure. The orchestrator requires both a valid complete record and exit 0 before publication.

Initial request (absolute paths; border is a fraction):

```json
{"version":1,"type":"job","source":"/absolute/content.png","source_sha256":"hex digest","width":1920,"height":1080,"border":0.05,"styles":["blur","gallery","frosted","gradient"],"threads":3,"work_dir":"/absolute/staging"}
```

Events: `stage` (`prepare`, `browser_initialization`, `render`, `export`, with style where applicable), `progress` (completed/total), `browser_slot_request`, `browser_slot_release`, `complete`, `error`. Rust replies with exactly `{"version":1,"type":"browser_slot_grant"}`. Browser slots are held until release or managed process termination. Standalone `wallpaper-engine --request job.json` grants its slot locally.

`complete` contains `artifacts` (four ordered objects with path, style, sha256, checks, seconds, backend), source_sha256, dimensions, rectangle, foreground_sha256 and total seconds. `checks` includes chunk types/count, crc_valid, trailing_bytes and foreground_exact. `error` uses fixed codes `invalid_input`, `browser_startup`, `verification_failed`, `processing_failed`; only browser_startup may request retry. Rust never trusts worker artifact paths for publication: it verifies the four expected paths and hashes itself. The result is journaled before atomic publication to permit recovery after a crash between rename and state update.

Probe commands: `--inspect path` emits `inspected` with displayed dimensions and SHA-256; `--doctor` emits `ready` after checking packaged assets, libvips and a real Chromium/WebGL launch. No source filenames or metadata are emitted.
