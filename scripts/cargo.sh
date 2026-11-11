#!/bin/sh
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
export RUSTUP_HOME="$ROOT/.wallpaper/tools/rustup"
export CARGO_HOME="$ROOT/.wallpaper/tools/cargo"
export PATH="$CARGO_HOME/bin:$PATH"
cd "$ROOT/orchestrator"
exec cargo "$@"
