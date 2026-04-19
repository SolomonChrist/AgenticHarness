#!/usr/bin/env python3
"""
Small local service manager for Agentic Harness daemons.

Use this instead of ad hoc background shell syntax when starting or
stopping Runner / Telegram / Visualizer on Windows.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from ctypes import wintypes


ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable or "python"

CREATE_FLAGS = 0
if os.name == "nt":
    CREATE_FLAGS = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

SERVICES = {
    "runner": {
        "script": ROOT / "Runner" / "runner_daemon.py",
        "runtime": ROOT / "Runner" / ".runner_runtime.json",
        "log": ROOT / "Runner" / "runner.log",
    },
    "telegram": {
        "script": ROOT / "TelegramBot" / "telegram_bot.py",
        "runtime": ROOT / "TelegramBot" / "data" / "runtime.json",
        "log": ROOT / "TelegramBot" / "telegram.log",
    },
    "visualizer": {
        "script": ROOT / "Visualizer" / "visualizer_server.py",
        "runtime": ROOT / "Visualizer" / ".visualizer_runtime.json",
        "log": ROOT / "Visualizer" / "visualizer.log",
    },
}


def load_runtime(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            process_query_limited_information = 0x1000
            still_active = 259
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL

            handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == still_active
            finally:
                kernel32.CloseHandle(handle)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def service_status(name: str) -> dict:
    cfg = SERVICES[name]
    runtime = load_runtime(cfg["runtime"])
    pid = int(runtime.get("pid", 0) or 0)
    alive = process_alive(pid)
    runtime["alive"] = alive
    if runtime.get("status") == "active" and not alive:
        runtime["status"] = "inactive"
    runtime.setdefault("component", name)
    runtime.setdefault("status", "inactive")
    return runtime


def start_service(name: str) -> int:
    cfg = SERVICES[name]
    status = service_status(name)
    if status.get("alive"):
        print(f"{name}: already running (pid {status.get('pid')})")
        return 0

    cfg["log"].parent.mkdir(parents=True, exist_ok=True)
    handle = open(cfg["log"], "a", encoding="utf-8")
    try:
        subprocess.Popen(
            [PYTHON, str(cfg["script"])],
            cwd=str(ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_FLAGS,
            close_fds=(os.name != "nt"),
        )
    finally:
        handle.close()

    deadline = time.time() + 5
    while time.time() < deadline:
        status = service_status(name)
        if status.get("alive") or status.get("status") == "active":
            print(f"{name}: started")
            return 0
        time.sleep(0.25)
    print(f"{name}: start attempted; check log {cfg['log']}")
    return 1


def stop_service(name: str) -> int:
    status = service_status(name)
    pid = int(status.get("pid", 0) or 0)
    if not pid or not process_alive(pid):
        print(f"{name}: not running")
        return 0
    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        print(f"{name}: failed to stop pid {pid}: {exc}")
        return 1

    deadline = time.time() + 5
    while time.time() < deadline:
        if not process_alive(pid):
            print(f"{name}: stopped")
            return 0
        time.sleep(0.25)
    print(f"{name}: stop signal sent but process still alive (pid {pid})")
    return 1


def print_status(names: list[str]) -> int:
    for name in names:
        status = service_status(name)
        print(json.dumps({name: status}, indent=2))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in {"start", "stop", "status"}:
        print("Usage: py service_manager.py <start|stop|status> <runner|telegram|visualizer|all>")
        return 1

    action = argv[1]
    target = argv[2].lower()
    names = list(SERVICES) if target == "all" else [target]
    if any(name not in SERVICES for name in names):
        print("Unknown service.")
        return 1

    if action == "start":
        return max(start_service(name) for name in names)
    if action == "stop":
        return max(stop_service(name) for name in names)
    return print_status(names)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
