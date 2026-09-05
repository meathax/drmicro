#!/bin/sh
set -eu
task_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then exec python3 "$task_dir/dev.py" "$@"; fi
exec python "$task_dir/dev.py" "$@"
