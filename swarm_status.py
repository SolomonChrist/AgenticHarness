#!/usr/bin/env python3
"""Human-readable status for Agentic Harness daemons and bot cycles."""

from __future__ import annotations

import json
import re
from pathlib import Path

from service_manager import process_alive, service_status


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "Runner"
REGISTRY = RUNNER / "ROLE_LAUNCH_REGISTRY.md"
RUNNER_STATE = RUNNER / ".runner_state.json"
WAKE_QUEUE = RUNNER / "_wake_requests.md"
EVENTS = ROOT / "LAYER_LAST_ITEMS_DONE.md"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def scalar(block: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", block, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def role_blocks() -> list[str]:
    text = read_text(REGISTRY)
    return re.findall(r"### ROLE\s*\n.*?(?=\n### |\Z)", text, flags=re.DOTALL)


def pending_wake_count() -> int:
    state = load_json(RUNNER_STATE)
    seen = set(state.get("wake_requests_seen", []))
    lines = [line.strip() for line in read_text(WAKE_QUEUE).splitlines() if line.strip()]
    return sum(1 for line in lines if line not in seen)


def print_services() -> None:
    print("SERVICES")
    for name in ["chief-chat", "runner", "telegram", "telegram-watchdog", "visualizer"]:
        status = service_status(name)
        alive = "alive" if status.get("alive") else "down"
        pid = status.get("pid", "-")
        updated = status.get("updated_at", "-")
        detail = status.get("chief_responder_status") or status.get("mode") or status.get("status", "-")
        print(f"- {name}: {alive} | pid {pid} | {detail} | updated {updated}")


def print_roles() -> None:
    print("\nDAEMONIZED ROLES")
    state = load_json(RUNNER_STATE).get("roles", {})
    if not isinstance(state, dict):
        state = {}
    found = False
    for block in role_blocks():
        role = scalar(block, "Role")
        if not role:
            continue
        enabled = scalar(block, "Enabled")
        ready = scalar(block, "Automation Ready")
        mode = scalar(block, "Execution Mode")
        harness = scalar(block, "Harness Type") or scalar(block, "Harness Key")
        model = scalar(block, "Model / Profile") or "(default)"
        command = scalar(block, "Launch Command")
        if enabled.upper() != "YES" and ready.upper() != "YES":
            continue
        found = True
        role_state = state.get(role, {}) if isinstance(state.get(role, {}), dict) else {}
        pid = int(role_state.get("pid", 0) or 0)
        cycle_alive = process_alive(pid)
        last_launch = role_state.get("last_launch_at", "-")
        last_error = role_state.get("last_launch_error", "")
        log_path = role_state.get("last_launch_log", "")
        print(f"- {role}: {mode} | {harness} | {model} | cycle {'running' if cycle_alive else 'not running'} | pid {pid or '-'}")
        print(f"  enabled={enabled or '-'} ready={ready or '-'} command={'yes' if command else 'no'} last_launch={last_launch}")
        if log_path:
            print(f"  log={log_path}")
        if last_error:
            print(f"  error={last_error}")
    if not found:
        print("- none yet. Run configure_role_daemon.py after manually proving a role.")


def print_activity() -> None:
    print("\nACTIVITY")
    print(f"- pending wake requests: {pending_wake_count()}")
    recent = [
        line
        for line in read_text(EVENTS).splitlines()
        if line.strip().startswith("[")
    ][-8:]
    if recent:
        print("- recent events:")
        for line in recent:
            print(f"  {line}")
    else:
        print("- recent events: none")


def main() -> int:
    print("AGENTIC HARNESS STATUS\n")
    print_services()
    print_roles()
    print_activity()
    print("\nUse `py production_check.py` for pass/fail readiness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
