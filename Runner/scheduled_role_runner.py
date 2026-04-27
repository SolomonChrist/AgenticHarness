#!/usr/bin/env python3
"""Run one CLI-first scheduled role preflight and optional launch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RUNNER_ROOT = Path(__file__).resolve().parent
ROOT = RUNNER_ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from runner_daemon import RunnerDaemon


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one Agentic Harness scheduled role check.")
    parser.add_argument("--role", required=True, help="Role to check and possibly launch.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the preflight decision.")
    parser.add_argument("--reason", default="", help="Optional explicit run reason, such as daily_all_hands.")
    args = parser.parse_args()

    daemon = RunnerDaemon(RUNNER_ROOT)
    try:
        result = daemon.run_role_once(args.role.strip(), dry_run=args.dry_run, force_reason=args.reason.strip())
        if not args.dry_run:
            daemon.save_state()
    finally:
        if not args.dry_run:
            daemon.update_runtime_status("one-shot")
    if not args.dry_run:
        print(json.dumps(result, indent=2))
    return 0 if result.get("decision") in {"run", "skip"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
