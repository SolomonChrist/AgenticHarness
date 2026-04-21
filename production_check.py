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
VISUALIZER_RUNTIME = ROOT / "Visualizer" / ".visualizer_runtime.json"
RUNNER_RUNTIME = ROOT / "Runner" / ".runner_runtime.json"
TELEGRAM_RUNTIME = TELEGRAM_DIR / "data" / "runtime.json"


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


def record_ready(record: dict[str, str]) -> bool:
    return record.get("Enabled", "").upper() == "YES" or record.get("Automation Ready", "").upper() == "YES"


def role_block(role: str) -> str:
    text = read_text(ROLE_REGISTRY)
    pattern = re.compile(
        rf"### ROLE\s*\nRole:\s*{re.escape(role)}\s*\n.*?(?=\n### |\Z)",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


def parse_markdown_records(path: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    text = read_text(path)
    if path == ROLE_REGISTRY and "## Active Registrations" in text:
        text = text.split("## Active Registrations", 1)[1]
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("### ROLE"):
            if current:
                records.append(current)
            current = {"_type": "role"}
            continue
        if line.startswith("### HUMAN RUNNER"):
            if current:
                records.append(current)
            current = {"_type": "human"}
            continue
        if current is None or not line or line.startswith("- "):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        records.append(current)
    by_role: dict[str, dict[str, str]] = {}
    final: list[dict[str, str]] = []
    for record in records:
        role = record.get("Role", "").strip()
        if record.get("_type") == "role":
            if not role:
                continue
            existing = by_role.get(role)
            if existing is None or (record_ready(record) and not record_ready(existing)):
                by_role[role] = record
        else:
            final.append(record)
    final.extend(by_role.values())
    return final


def parse_heartbeat(role: str) -> dict[str, str]:
    path = ROOT / "_heartbeat" / f"{role}.md"
    data: dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("|") and line.endswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0] not in {"Field", "---"}:
                data[parts[0]] = parts[1]
        elif ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def telegram_configured() -> bool:
    env_text = read_text(TELEGRAM_DIR / ".env.telegram")
    token = scalar(env_text, "TELEGRAM_BOT_TOKEN")
    allowed = scalar(env_text, "TELEGRAM_ALLOWED_USER_IDS")
    return bool(token and not token.startswith("YOUR_") and allowed)


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


def service_line(name: str, priority: str, required: bool, status: dict, failures: list[str]) -> None:
    alive = bool(status.get("alive"))
    state = str(status.get("status", "unknown"))
    ok = alive or (not required and not telegram_configured() and name == "Telegram bridge")
    optional_note = "" if required else "optional"
    detail = f"{state} / priority {priority} {optional_note}".strip()
    check(name, ok, detail, failures)


def role_health(record: dict[str, str]) -> dict[str, str | bool]:
    role = record.get("Role", "").strip()
    heartbeat = parse_heartbeat(role)
    enabled = record.get("Enabled", "").upper()
    ready = record.get("Automation Ready", "").upper()
    mode = record.get("Execution Mode", "") or "unknown"
    harness = heartbeat.get("Harness") or record.get("Harness Type") or record.get("Harness Key") or "unknown"
    model = heartbeat.get("Model") or record.get("Model / Profile") or "default"
    holder = heartbeat.get("Claimed By") or "unclaimed"
    status = heartbeat.get("Status") or "unclaimed"
    launch = record.get("Launch Command", "")
    automation_ok = mode == "manual" or (enabled == "YES" and ready == "YES" and bool(launch))
    return {
        "role": role,
        "status": status,
        "holder": holder,
        "harness": harness,
        "model": model,
        "mode": mode,
        "enabled": enabled or "NO",
        "automation_ready": ready or "NO",
        "launch_command": launch,
        "automation_ok": automation_ok,
    }


def print_role_health() -> list[str]:
    failures: list[str] = []
    print("\nRegistered Bots / Roles:")
    records = [record for record in parse_markdown_records(ROLE_REGISTRY) if record.get("_type") == "role" and record.get("Role")]
    if not records:
        print("[FAIL] No registered role entries found.")
        return ["Registered roles"]
    for record in records:
        health = role_health(record)
        marker = "PASS" if health["automation_ok"] else "WARN"
        if health["role"] == "Chief_of_Staff" and not health["automation_ok"]:
            marker = "FAIL"
            failures.append("Chief role automation")
        print(
            f"[{marker}] {health['role']}: status {health['status']} / holder {health['holder']} / "
            f"harness {health['harness']} / model {health['model']} / mode {health['mode']} / "
            f"enabled {health['enabled']} / automation {health['automation_ready']}"
        )
    return failures


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
    telegram_file_failures = {"Telegram Chief inbox", "Telegram human outbox"}
    if any(failure in telegram_file_failures for failure in failures) and telegram_configured():
        emit("py service_manager.py stop telegram")
        emit("py service_manager.py start telegram")
    if "Wake queue available" in failures:
        emit("py service_manager.py start runner")
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

    print("Services:")
    service_line("Runner service", "CRITICAL", True, runner_status, failures)
    check("Runner mode", scalar(runner_cfg, "Runner Mode").upper() == "ACTIVE", scalar(runner_cfg, "Runner Mode") or "missing", failures)
    service_line("Visualizer", "CRITICAL", True, visualizer_status, failures)
    service_line("Telegram bridge", "OPTIONAL_AFTER_CONFIG", telegram_configured(), telegram_status, failures)

    print("\nChief Daemon Path:")
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
    failures.extend(print_role_health())

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
