#!/usr/bin/env python3
"""Run the configurable Daily All Hands recovery/check-in pass."""

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

from role_preflight import collect_role_names
from runner_daemon import RunnerDaemon


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Daily All Hands for all configured Agentic Harness roles.")
    parser.add_argument("--dry-run", action="store_true", help="Only print preflight decisions.")
    args = parser.parse_args()

    daemon = RunnerDaemon(RUNNER_ROOT)
    runner_cfg = daemon.load_runner_config()
    registry = daemon.load_role_registry()
    roles = [role for role in collect_role_names(ROOT) if role in registry]
    results = []
    try:
        for role in roles:
            results.append(
                daemon.run_role_once(
                    role,
                    runner_cfg=runner_cfg,
                    dry_run=args.dry_run,
                    force_reason="daily_all_hands",
                )
            )
        if not args.dry_run:
            daemon.save_state()
    finally:
        if not args.dry_run:
            daemon.update_runtime_status("one-shot-daily-all-hands", runner_cfg=runner_cfg)
    if not args.dry_run:
        print(json.dumps({"roles": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
