#!/usr/bin/env python3
"""Append a structured Runner wake request for a role."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from coordination_io import append_line


ROOT = Path(__file__).resolve().parent
WAKE_QUEUE = ROOT / "Runner" / "_wake_requests.md"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    parser = argparse.ArgumentParser(description="Queue an immediate Runner wake request.")
    parser.add_argument("--role", required=True, help="Role to wake, e.g. Chief_of_Staff.")
    parser.add_argument("--reason", default="manual_wake", help="Structured wake reason.")
    args = parser.parse_args()

    role = args.role.strip()
    reason = args.reason.strip() or "manual_wake"
    if not role:
        raise SystemExit("--role is required.")
    append_line(WAKE_QUEUE, f"[{iso_now()}] {role}: {reason}")
    print(f"Wake queued for {role}: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
