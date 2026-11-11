#!/bin/sh
# Developer-only tools stay inside ignored project storage. No shell profile changes.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
SHELF="$ROOT/Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf"
export RUSTUP_HOME="$ROOT/.wallpaper/tools/rustup"
export CARGO_HOME="$ROOT/.wallpaper/tools/cargo"
export UV_CACHE_DIR="$ROOT/.wallpaper/uv-cache"
export UV_PYTHON_INSTALL_DIR="$SHELF/.cache/python"
export PLAYWRIGHT_BROWSERS_PATH="$SHELF/browser-binaries"
mkdir -p "$ROOT/.wallpaper/tools"
if [ ! -x "$CARGO_HOME/bin/cargo" ]; then
  curl --fail --location https://sh.rustup.rs --output "$ROOT/.wallpaper/tools/rustup.sh"
  sh "$ROOT/.wallpaper/tools/rustup.sh" -y --no-modify-path --profile minimal --default-toolchain 1.99.1
fi
cd "$ROOT"
uv python install 3.12.14
uv venv --python 3.12.14 .venv
uv pip install --python .venv/bin/python --require-hashes -r "$SHELF/requirements-build.lock"
uv pip install --python .venv/bin/python --require-hashes --no-build-isolation -r "$SHELF/requirements.lock"
.venv/bin/python -m playwright install chromium
.venv/bin/python "$SHELF/acquire_sources.py"
npm --prefix "$SHELF" ci --ignore-scripts --cache "$SHELF/.cache/npm"
node "$SHELF/build-adapters.mjs"
node "$SHELF/build-production.mjs"
"$ROOT/scripts/cargo.sh" build --locked
