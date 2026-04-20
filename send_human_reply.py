#!/usr/bin/env python3
"""Append a clean operator-facing reply for Telegram or desktop transport."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from coordination_io import append_line, read_text


ROOT = Path(__file__).resolve().parent
HUMANS = ROOT / "HUMANS.md"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def active_human_id() -> str:
    text = read_text(HUMANS)
    for line in text.splitlines():
        if line.startswith("ID:"):
            value = line.split(":", 1)[1].strip()
            if value:
                return value
    raise SystemExit("No human ID found in HUMANS.md. Complete onboarding first.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a clean reply to _messages/human_<HumanID>.md.")
    parser.add_argument("message", nargs="+", help="Reply text to send to the operator.")
    parser.add_argument("--human-id", default="", help="Override detected human ID.")
    parser.add_argument("--from-role", default="Chief_of_Staff", help="Role writing the reply.")
    args = parser.parse_args()

    human_id = args.human_id.strip() or active_human_id()
    message = " ".join(args.message).strip()
    if not message:
        raise SystemExit("Message cannot be empty.")

    outbox = ROOT / "_messages" / f"human_{human_id}.md"
    append_line(outbox, f"[{iso_now()}] [{args.from_role}] {message}")
    print(f"Reply queued for {human_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
