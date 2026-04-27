#!/usr/bin/env python3
"""Compatibility wrapper that routes Chief_of_Staff launches to ChiefChat."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ChiefChat.chief_chat_service import run_once, status


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one cheap ChiefChat pass.")
    parser.add_argument("--role", default="Chief_of_Staff")
    parser.add_argument("--workdir", default=str(ROOT))
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    root = Path(args.workdir).resolve()
    if args.role != "Chief_of_Staff":
        raise SystemExit("cheap_chief_router.py only supports Chief_of_Staff.")
    if args.status:
        print(json.dumps(status(root), indent=2))
        return 0
    processed = run_once(root)
    print(json.dumps({"processed": processed, **status(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
