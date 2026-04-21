#!/usr/bin/env python3
"""Append a clean operator-facing reply for Telegram, Visualizer, or desktop transport."""

from __future__ import annotations

import argparse
from pathlib import Path

from coordination_io import read_text
from operator_messaging import append_operator_reply


ROOT = Path(__file__).resolve().parent
HUMANS = ROOT / "HUMANS.md"


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
    parser.add_argument(
        "--channel",
        default="all",
        choices=["all", "telegram", "visualizer", "desktop"],
        help="Reply transport target. 'all' is visible everywhere.",
    )
    parser.add_argument("--reply-to", default="", help="Optional operator message id this reply answers.")
    args = parser.parse_args()

    human_id = args.human_id.strip() or active_human_id()
    message = " ".join(args.message).strip()
    if not message:
        raise SystemExit("Message cannot be empty.")

    append_operator_reply(
        ROOT,
        message,
        human_id=human_id,
        from_role=args.from_role,
        channel=args.channel,
        reply_to=args.reply_to.strip(),
    )
    print(f"Reply queued for {human_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
