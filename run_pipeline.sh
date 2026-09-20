#!/bin/bash
# Wrapper để cron gọi: tự xác định đường dẫn project, dùng đúng python trong venv,
# và dùng flock để không chạy chồng lên lần chạy trước nếu nó vẫn còn đang chạy.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCKFILE="$PROJECT_DIR/.pipeline.lock"

exec 200>"$LOCKFILE"
if ! flock -n 200; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Previous run still in progress, skipping this trigger." >> "$PROJECT_DIR/logs/cron.log"
    exit 1
fi

cd "$PROJECT_DIR"
"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/main.py"
