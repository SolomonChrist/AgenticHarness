#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python service_manager.py start telegram
