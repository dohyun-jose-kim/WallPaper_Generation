#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
BUNDLE=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
exec "$BUNDLE/python/bin/python3.12" "$BUNDLE/manage.py" "$@"
