#!/usr/bin/env python3
"""
Small file coordination helpers for Agentic Harness daemons.

The goal is not heavyweight database locking. It is to make the built-in
Python daemons append and rewrite markdown/json files safely enough that:

- writes are atomic where possible
- short-lived lock files reduce inter-daemon collisions
- readers see either the old file or the fully written new file
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class FileLockTimeout(RuntimeError):
    pass


def _lock_dir_for(path: Path) -> Path:
    return path.parent / ".locks"


def _lock_path_for(path: Path) -> Path:
    safe_name = path.name.replace(":", "_")
    return _lock_dir_for(path) / f"{safe_name}.lock"


def _read_lock_payload(lock_path: Path) -> dict[str, Any]:
    try:
        return json.loads(lock_path.read_text(encoding="utf-8", errors="ignore"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _pid_is_alive(pid: object) -> bool:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False

    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            process = kernel32.OpenProcess(0x1000, False, pid_int)
            if not process:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == 259
            finally:
                kernel32.CloseHandle(process)
        except Exception:
            return True

    try:
        os.kill(pid_int, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def read_text(path: Path, *, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return default


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        # Windows + OneDrive can briefly lock the destination while another
        # thread/process reads or syncs it. Retry the atomic swap instead of
        # crashing daemon threads on transient WinError 5/32 failures.
        last_error: OSError | None = None
        for attempt in range(20):
            try:
                os.replace(temp_path, path)
                last_error = None
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.05 * (attempt + 1))
            except OSError as exc:
                last_error = exc
                if getattr(exc, "winerror", None) not in {5, 32}:
                    raise
                time.sleep(0.05 * (attempt + 1))
        if last_error is not None:
            raise last_error
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


@contextmanager
def file_lock(path: Path, *, timeout_seconds: float = 5.0, stale_seconds: float = 30.0):
    lock_dir = _lock_dir_for(path)
    lock_path = _lock_path_for(path)
    lock_dir.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0.1, timeout_seconds)

    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            payload = {
                "pid": os.getpid(),
                "path": str(path),
                "created_at": time.time(),
            }
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except OSError:
                age = 0.0
            payload = _read_lock_payload(lock_path)
            lock_pid = payload.get("pid")
            if (lock_pid and not _pid_is_alive(lock_pid)) or age > stale_seconds:
                try:
                    lock_path.unlink()
                    continue
                except OSError:
                    pass
            if time.time() >= deadline:
                raise FileLockTimeout(f"Timed out waiting for lock on {path}")
            time.sleep(0.05)

    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except OSError:
            pass


def append_line(path: Path, line: str, *, timeout_seconds: float = 5.0) -> None:
    with file_lock(path, timeout_seconds=timeout_seconds):
        existing = read_text(path)
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        atomic_write_text(path, existing + prefix + line + "\n")
