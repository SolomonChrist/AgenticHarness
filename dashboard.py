#!/usr/bin/env python3
"""One-command CLI dashboard launcher for Agentic Harness."""

from __future__ import annotations

import argparse
import sys

import role_jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the Agentic Harness CLI dashboard.")
    parser.add_argument("--once", action="store_true", help="Print one dashboard snapshot and exit.")
    parser.add_argument("--interval", type=float, default=2.0, help="Refresh interval in seconds.")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors.")
    args = parser.parse_args()

    role_args = ["dashboard"]
    if args.no_color:
        role_args.append("--no-color")
    if not args.once:
        role_args.extend(["--watch", str(max(0.5, args.interval))])

    old_argv = sys.argv[:]
    try:
        sys.argv = ["role_jobs.py", *role_args]
        return role_jobs.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())
