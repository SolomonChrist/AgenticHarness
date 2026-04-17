#!/usr/bin/env sh
set -eu
if command -v python3 >/dev/null 2>&1; then
  python3 "$(dirname "$0")/runner_daemon.py"
else
  python "$(dirname "$0")/runner_daemon.py"
fi
