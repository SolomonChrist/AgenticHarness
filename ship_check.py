#!/usr/bin/env python3
"""Release validator for a clean Agentic Harness checkout."""

from __future__ import annotations

import py_compile
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "AGENTIC_HARNESS.md",
    "AGENTIC_HARNESS_TINY.md",
    "START_HERE.md",
    "README.md",
    "FINAL_APPLICATION_DESIGN.md",
    "COMMANDS.md",
    "RELEASE.md",
    "configure_role_daemon.py",
    "production_check.py",
    "swarm_status.py",
    "send_human_reply.py",
    "wake_role.py",
    "service_manager.py",
    "coordination_io.py",
    "role_preflight.py",
    "role_jobs.py",
    "preflight_selftest.py",
    "chat_ledger.py",
    "cheap_chief_router.py",
    "chief_chat_selftest.py",
    "ChiefChat/CHIEF_CHAT_CONFIG.md",
    "ChiefChat/README.md",
    "ChiefChat/chief_chat_service.py",
    "ChiefChat/setup_chief_chat.py",
    "n8n_harness/folder_mirror.py",
    "n8n_harness/README.md",
    "n8n_harness/setup_folder_mirror.py",
    "n8n_harness/setup_folder_mirror.bat",
    "n8n_harness/start_folder_mirror.bat",
    "Runner/runner_daemon.py",
    "Runner/scheduled_role_runner.py",
    "Runner/daily_all_hands.py",
    "Runner/harness_role_cycle.py",
    "TelegramBot/telegram_bot.py",
    "Visualizer/visualizer_server.py",
]

COMPILE_FILES = [
    "configure_role_daemon.py",
    "production_check.py",
    "swarm_status.py",
    "send_human_reply.py",
    "wake_role.py",
    "service_manager.py",
    "coordination_io.py",
    "role_preflight.py",
    "role_jobs.py",
    "preflight_selftest.py",
    "chat_ledger.py",
    "cheap_chief_router.py",
    "chief_chat_selftest.py",
    "ChiefChat/chief_chat_service.py",
    "ChiefChat/setup_chief_chat.py",
    "n8n_harness/folder_mirror.py",
    "n8n_harness/setup_folder_mirror.py",
    "reset_to_fresh_state.py",
    "Runner/runner_daemon.py",
    "Runner/scheduled_role_runner.py",
    "Runner/daily_all_hands.py",
    "Runner/claude_role_cycle.py",
    "Runner/harness_role_cycle.py",
    "TelegramBot/telegram_bot.py",
    "Visualizer/visualizer_server.py",
]

RUNTIME_PATHS = [
    "debug.log",
    ".env.telegram",
    "Runner/.runner_state.json",
    "Runner/.runner_runtime.json",
    "Runner/_wake_requests.md",
    "Runner/_reminders.json",
    "Runner/runner.log",
    "ChiefChat/data/runtime.json",
    "ChiefChat/chief_chat.log",
    "TelegramBot/.env.telegram",
    "TelegramBot/data/state.json",
    "TelegramBot/data/runtime.json",
    "TelegramBot/telegram.log",
    "Visualizer/.visualizer_runtime.json",
    "Visualizer/visualizer.log",
    "n8n_harness/mirror_config.local.json",
]

LIVE_STATE_DIRS = [
    "_heartbeat",
    "_messages",
    "Projects",
    "Runner/_generated_prompts",
]

BAD_TEXT_MARKERS = ["\ufffd", "â€œ", "â€", "â€”", "â€“"]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def dir_has_content(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def check_required_files(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            fail(errors, f"missing required file: {relative}")


def check_python_compiles(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        for relative in COMPILE_FILES:
            path = ROOT / relative
            if not path.exists():
                continue
            try:
                cfile = temp_root / (relative.replace("/", "_").replace("\\", "_") + ".pyc")
                py_compile.compile(str(path), cfile=str(cfile), doraise=True)
            except Exception as exc:
                fail(errors, f"python compile failed for {relative}: {exc}")


def check_runtime_artifacts(errors: list[str]) -> None:
    for relative in RUNTIME_PATHS:
        if (ROOT / relative).exists():
            fail(errors, f"runtime artifact present: {relative}")
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            fail(errors, f"cache directory present: {path.relative_to(ROOT)}")
    for path in ROOT.rglob(".locks"):
        if path.is_dir():
            fail(errors, f"lock directory present: {path.relative_to(ROOT)}")
    for relative in LIVE_STATE_DIRS:
        path = ROOT / relative
        if dir_has_content(path):
            fail(errors, f"live state directory is not empty: {relative}")


def check_markdown_shape(errors: list[str]) -> None:
    for relative in ["ROLES.md", "LAYER_CONFIG.md", "LAYER_TASK_LIST.md", "Runner/ROLE_LAUNCH_REGISTRY.md"]:
        text = (ROOT / relative).read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            fail(errors, f"empty markdown control file: {relative}")
    if "Chief_of_Staff" not in (ROOT / "ROLES.md").read_text(encoding="utf-8", errors="ignore"):
        fail(errors, "ROLES.md must include Chief_of_Staff")
    if "| Chief_of_Staff | unclaimed |" not in (ROOT / "LAYER_CONFIG.md").read_text(encoding="utf-8", errors="ignore"):
        fail(errors, "LAYER_CONFIG.md must reset Chief_of_Staff to unclaimed")


def check_text_encoding(errors: list[str]) -> None:
    for path in ROOT.rglob("*.md"):
        if "vendor" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in BAD_TEXT_MARKERS:
            if marker in text:
                fail(errors, f"encoding artifact {marker!r} in {path.relative_to(ROOT)}")
                break


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_python_compiles(errors)
    check_runtime_artifacts(errors)
    check_markdown_shape(errors)
    check_text_encoding(errors)
    if errors:
        print("SHIP CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SHIP CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
