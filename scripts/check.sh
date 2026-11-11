#!/bin/sh
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"
./scripts/cargo.sh fmt --check
./scripts/cargo.sh clippy --locked --all-targets -- -D warnings
./scripts/cargo.sh test --locked -- --include-ignored
./scripts/cargo.sh build --locked
.venv/bin/python -m pytest Photo-to-Wallpaper-Rendering-Engine/code/tests Photo-to-Wallpaper-Rendering-Engine/tests tests/integration/test_cli.py -q
.venv/bin/python scripts/check-baseline.py
