#!/usr/bin/env python3
"""Live production readiness check for Agentic Harness."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from service_manager import service_status


ROOT = Path(__file__).resolve().parent
RUNNER_CONFIG = ROOT / "Runner" / "RUNNER_CONFIG.md"
ROLE_REGISTRY = ROOT / "Runner" / "ROLE_LAUNCH_REGISTRY.md"
WAKE_QUEUE = ROOT / "Runner" / "_wake_requests.md"
CHIEF_HEARTBEAT = ROOT / "_heartbeat" / "Chief_of_Staff.md"
CHIEF_INBOX = ROOT / "_messages" / "Chief_of_Staff.md"
TELEGRAM_DIR = ROOT / "TelegramBot"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def scalar(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def bool_scalar(text: str, key: str) -> bool:
    return scalar(text, key).upper() in {"YES", "TRUE", "ACTIVE", "ENABLED"}


def role_block(role: str) -> str:
    text = read_text(ROLE_REGISTRY)
    pattern = re.compile(
        rf"### ROLE\s*\nRole:\s*{re.escape(role)}\s*\n.*?(?=\n### |\Z)",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


def telegram_human_file() -> Path | None:
    runtime_path = TELEGRAM_DIR / "data" / "runtime.json"
    try:
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    except Exception:
        runtime = {}
    human_id = str(runtime.get("human_id", "")).strip()
    if not human_id:
        env_text = read_text(TELEGRAM_DIR / ".env.telegram")
        human_id = scalar(env_text, "HUMAN_ID")
    return ROOT / "_messages" / f"human_{human_id}.md" if human_id else None


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    marker = "PASS" if ok else "FAIL"
    print(f"[{marker}] {name}: {detail}")
    if not ok:
        failures.append(name)


def corrective_command() -> str:
    block = role_block("Chief_of_Staff")
    model = scalar(block, "Model / Profile") or "<model>"
    harness_type = scalar(block, "Harness Type").lower()
    if "opencode" in harness_type:
        provider = "opencode"
    elif "ollama" in harness_type:
        provider = "ollama"
    elif "goose" in harness_type:
        provider = "goose"
    else:
        provider = "claude"
    return f"py configure_role_daemon.py --role Chief_of_Staff --provider {provider} --model {model} --start-runner"


def print_corrective_commands(failures: list[str]) -> None:
    printed: set[str] = set()

    def emit(command: str) -> None:
        if command not in printed:
            print(command)
            printed.add(command)

    service_map = {
        "Runner service": "py service_manager.py start runner",
        "Telegram bridge": "py service_manager.py start telegram",
        "Visualizer": "py service_manager.py start visualizer",
    }
    daemon_failures = {
        "Runner mode",
        "Chief registry entry",
        "Chief daemon enabled",
        "Chief automation ready",
        "Chief launch command",
    }
    for failure in failures:
        command = service_map.get(failure)
        if command:
            emit(command)
    if any(failure in daemon_failures for failure in failures):
        emit(corrective_command())
    if any(failure in {"Telegram Chief inbox", "Telegram human outbox", "Wake queue available"} for failure in failures):
        emit("py service_manager.py stop telegram")
        emit("py service_manager.py start telegram")
    if not printed:
        emit("py service_manager.py status all")


def main() -> int:
    failures: list[str] = []
    runner_status = service_status("runner")
    telegram_status = service_status("telegram")
    visualizer_status = service_status("visualizer")
    runner_cfg = read_text(RUNNER_CONFIG)
    chief_block = role_block("Chief_of_Staff")
    launch_command = scalar(chief_block, "Launch Command")
    human_file = telegram_human_file()

    check("Runner service", bool(runner_status.get("alive")), str(runner_status.get("status", "unknown")), failures)
    check("Runner mode", scalar(runner_cfg, "Runner Mode").upper() == "ACTIVE", scalar(runner_cfg, "Runner Mode") or "missing", failures)
    check("Telegram bridge", bool(telegram_status.get("alive")), str(telegram_status.get("status", "unknown")), failures)
    check("Visualizer", bool(visualizer_status.get("alive")), str(visualizer_status.get("status", "unknown")), failures)
    check("Chief heartbeat", CHIEF_HEARTBEAT.exists(), str(CHIEF_HEARTBEAT), failures)
    check("Chief registry entry", bool(chief_block), "found" if chief_block else "missing", failures)
    check("Chief daemon enabled", bool_scalar(chief_block, "Enabled"), scalar(chief_block, "Enabled") or "missing", failures)
    check("Chief automation ready", bool_scalar(chief_block, "Automation Ready"), scalar(chief_block, "Automation Ready") or "missing", failures)
    check("Chief launch command", bool(launch_command), launch_command or "missing", failures)
    check("Telegram Chief inbox", CHIEF_INBOX.exists(), str(CHIEF_INBOX), failures)
    check("Telegram human outbox", bool(human_file and human_file.exists()), str(human_file or "HUMAN_ID missing"), failures)

    wake_ok = WAKE_QUEUE.parent.exists()
    if WAKE_QUEUE.exists():
        try:
            read_text(WAKE_QUEUE)
        except Exception:
            wake_ok = False
    wake_detail = str(WAKE_QUEUE) if WAKE_QUEUE.exists() else f"{WAKE_QUEUE} (not created yet)"
    check("Wake queue available", wake_ok, wake_detail, failures)

    if failures:
        print("\nPRODUCTION CHECK FAILED")
        print("Recommended corrective command(s):")
        print_corrective_commands(failures)
        return 1

    print("\nPRODUCTION CHECK PASSED")
    print("Chief_of_Staff is daemonized. It is safe to close the original desktop harness window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
