#!/usr/bin/env python3
"""Tiny watchdog that restarts the Telegram bridge if it exits."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordination_io import atomic_write_text  # noqa: E402
from service_manager import service_status, start_service, telegram_configured  # noqa: E402


RUNTIME_FILE = ROOT / "TelegramBot" / "data" / "watchdog_runtime.json"
LOG_FILE = ROOT / "TelegramBot" / "telegram_watchdog.log"
DEFAULT_INTERVAL_SECONDS = 300
RUNNING = True


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_runtime(status: str, **extra: object) -> None:
    payload = {
        "component": "telegram-watchdog",
        "status": status,
        "pid": os.getpid(),
        "updated_at": iso_now(),
        **extra,
    }
    atomic_write_text(RUNTIME_FILE, json.dumps(payload, indent=2))


def log(line: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8", errors="replace") as handle:
        handle.write(f"[{iso_now()}] {line}\n")


def check_once(*, update_runtime: bool = True) -> dict[str, object]:
    if not telegram_configured():
        if update_runtime:
            write_runtime("inactive", last_action="skipped_not_configured", last_error="")
        return {"ok": True, "action": "skipped_not_configured", "summary": "Telegram is not configured."}

    status = service_status("telegram")
    if status.get("alive"):
        if update_runtime:
            write_runtime(
                "active",
                telegram_alive=True,
                telegram_pid=int(status.get("pid", 0) or 0),
                last_action="already_running",
                last_error="",
            )
        return {"ok": True, "action": "already_running", "summary": f"Telegram is running (pid {status.get('pid')})."}

    log("Telegram bridge is not running; attempting restart.")
    result = start_service("telegram")
    after = service_status("telegram")
    alive = bool(after.get("alive"))
    action = "restarted" if alive else "restart_failed"
    last_error = "" if alive else str(after.get("last_error", "") or f"start_service exited {result}")
    if update_runtime:
        write_runtime(
            "active" if alive else "degraded",
            telegram_alive=alive,
            telegram_pid=int(after.get("pid", 0) or 0),
            last_action=action,
            last_error=last_error,
        )
    log(f"{action}: pid={after.get('pid', 0)} status={after.get('status', 'unknown')} error={last_error}")
    return {"ok": alive, "action": action, "summary": last_error or "Telegram bridge restarted."}


def shutdown(*_args: object) -> None:
    global RUNNING
    RUNNING = False
    write_runtime("stopped", last_action="stopped", last_error="")
    raise SystemExit(0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Restart Telegram bridge if it crashes.")
    parser.add_argument("--once", action="store_true", help="Run one check and exit.")
    parser.add_argument("--status", action="store_true", help="Print watchdog runtime status and exit.")
    parser.add_argument("--interval-seconds", type=int, default=DEFAULT_INTERVAL_SECONDS, help="Check interval; default 300 seconds.")
    args = parser.parse_args()

    if args.status:
        try:
            print(RUNTIME_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(json.dumps({"component": "telegram-watchdog", "status": "inactive", "alive": False}, indent=2))
        return 0

    if args.once:
        result = check_once(update_runtime=False)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    interval = max(30, int(args.interval_seconds or DEFAULT_INTERVAL_SECONDS))
    write_runtime("active", interval_seconds=interval, last_action="started", last_error="")
    log(f"Telegram watchdog started. interval_seconds={interval}")
    while RUNNING:
        try:
            check_once()
        except Exception as exc:
            message = str(exc)
            write_runtime("degraded", last_action="watchdog_error", last_error=message)
            log(f"watchdog_error: {message}")
        time.sleep(interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
