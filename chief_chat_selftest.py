#!/usr/bin/env python3
"""Self-test for the Telegram-first ChiefChat path."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ChiefChat.chief_chat_service import run_once
from chat_ledger import parse_chat_records
from operator_messaging import append_operator_message


TEMP_DIRS: list[tempfile.TemporaryDirectory] = []


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_root() -> Path:
    temp = tempfile.TemporaryDirectory()
    TEMP_DIRS.append(temp)
    root = Path(temp.name)
    write(root / "AGENTIC_HARNESS.md", "# Agentic Harness\n")
    write(root / "HUMANS.md", "ID: TestHuman\n")
    write(root / "LAYER_LAST_ITEMS_DONE.md", "# Events\n")
    write(root / "LAYER_TASK_LIST.md", "# Tasks\n")
    write(root / "MEMORY" / "agents" / "Chief_of_Staff" / "SOUL.md", "Be warm, concise, and operational.\n")
    write(root / "MEMORY" / "agents" / "Chief_of_Staff" / "ALWAYS.md", "Remember this is a test harness.\n")
    write(root / "Runner" / "ROLE_LAUNCH_REGISTRY.md", "### ROLE\nRole: Chief_of_Staff\nEnabled: YES\nAutomation Ready: YES\n")
    write(root / "Runner" / ".runner_state.json", json.dumps({"roles": {"Chief_of_Staff": {"provider_cooldown_until": "2999-01-01T00:00:00-05:00"}}}))
    write(
        root / "ChiefChat" / "CHIEF_CHAT_CONFIG.md",
        "\n".join(
            [
                "Chat Provider: fake",
                "Chat Model: fake",
                "Browser Enabled: NO",
                "Max Messages Per Pass: 5",
            ]
        ),
    )
    return root


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: expected {needle!r} in {text!r}")


def main() -> int:
    root = make_root()
    append_operator_message(root, "Hi", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed message, got {processed}")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "I am here", "telegram-style reply")
    records = parse_chat_records(root)
    if not any(record.get("direction") == "chief_to_operator" for record in records):
        raise AssertionError("expected Chief reply in chat ledger")

    append_operator_message(root, "Look up the latest status of example.com", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed web message, got {processed}")
    tasks = (root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    assert_contains(tasks, "TASK-WEB-", "web task creation")
    assert_contains(tasks, "Browser automation is disabled", "browser fallback note")
    print("CHIEF CHAT SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
