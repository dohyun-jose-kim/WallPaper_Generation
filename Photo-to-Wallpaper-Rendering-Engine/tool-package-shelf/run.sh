#!/usr/bin/env bash
# Run project tools with all large downloads and caches kept local and ignored.
set -euo pipefail
TASK_SHELF="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TASK_ROOT="$(cd -- "$TASK_SHELF/../.." && pwd)"
export UV_CACHE_DIR="$TASK_SHELF/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$TASK_SHELF/.cache/python"
export UV_MANAGED_PYTHON=1
export PLAYWRIGHT_BROWSERS_PATH="$TASK_SHELF/browser-binaries"
export npm_config_cache="$TASK_SHELF/.cache/npm"
export OMP_NUM_THREADS=12
export OPENBLAS_NUM_THREADS=12
export VECLIB_MAXIMUM_THREADS=12
export NUMEXPR_NUM_THREADS=12
export VIPS_CONCURRENCY=12
export PATH="$TASK_ROOT/.venv/bin:$PATH"
cd -- "$TASK_ROOT"
exec "$@"
