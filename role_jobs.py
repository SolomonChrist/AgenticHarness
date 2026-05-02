#!/usr/bin/env python3
"""CLI cron/job board for Agentic Harness roles."""

from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path

from coordination_io import atomic_write_text, read_text
from role_preflight import collect_role_names, evaluate_role_preflight, load_json, load_role_registry, parse_key_values
from service_manager import service_status, telegram_configured


ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "Runner" / "ROLE_LAUNCH_REGISTRY.md"
ANSI = sys_supports_ansi = os.name != "nt" or bool(os.getenv("WT_SESSION") or os.getenv("ANSICON") or os.getenv("TERM"))


class C:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def paint(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{color}{text}{C.RESET}"


def status_color(status: str) -> str:
    upper = (status or "").upper()
    if upper in {"RUN_ALLOWED", "DAILY_ALL_HANDS", "LAUNCHED"}:
        return C.GREEN
    if upper.startswith("SKIPPED"):
        return C.YELLOW
    if upper.startswith("PAUSED"):
        return C.RED
    return C.CYAN


def bool_marker(value: bool, enabled: bool) -> str:
    return paint("ON ", C.GREEN, enabled) if value else paint("OFF", C.RED, enabled)


def replace_key_line(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(key)}:\s*).*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(rf"\g<1>{value}", text, count=1)
    return text.rstrip() + f"\n{key}: {value}\n"


def set_role_enabled(role: str, enabled: bool) -> None:
    text = read_text(REGISTRY)
    pattern = re.compile(
        rf"### ROLE\s*\nRole:\s*{re.escape(role)}\s*\n.*?(?=\n### |\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"Role not found in {REGISTRY}: {role}")
    block = replace_key_line(match.group(0), "Enabled", "YES" if enabled else "NO")
    atomic_write_text(REGISTRY, text[: match.start()] + block + text[match.end() :])


def manual_role_prompt(role: str, *, short: bool = False, claude_command: bool = False) -> str:
    role = role.strip()
    short_prompt = f"continue, check your tasks as {role}"
    if short:
        prompt = short_prompt
    else:
        prompt = "\n".join(
            [
                "Read AGENTIC_HARNESS_TINY.md first. Do not read the full protocol unless you are blocked.",
                short_prompt,
                "",
                "Before acting, re-check the role lease and stand down if another unexpired holder owns this role.",
                "If the lease is free or stale, claim it, renew it during meaningful work, and write a clean end-of-run status.",
                f"Check `_messages/{role}.md`, `LAYER_TASK_LIST.md`, `Projects/*/TASKS.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and the relevant project files.",
                "Do the next concrete assigned task for this role, update the markdown control plane, and avoid broad refactors unless the task requires them.",
                "If there is no actionable work, write a concise standby/status note and stop.",
            ]
        )
    if claude_command:
        escaped = prompt.replace('"', '\\"')
        return f'claude -p "{escaped}" --model haiku --dangerously-skip-permissions'
    return prompt


def role_rows() -> list[dict[str, str]]:
    registry = load_role_registry(ROOT)
    runner_cfg = parse_key_values(ROOT / "Runner" / "RUNNER_CONFIG.md")
    state = load_json(ROOT / "Runner" / ".runner_state.json")
    rows: list[dict[str, str]] = []
    for role in collect_role_names(ROOT):
        config = registry.get(role)
        if not config:
            rows.append(
                {
                    "role": role,
                    "enabled": False,
                    "registered": False,
                    "status": "UNREGISTERED",
                    "reason": "role_not_registered",
                    "pending": 0,
                    "harness": "",
                    "model": "",
                    "lease": "unclaimed",
                    "command": "",
                }
            )
            continue
        preflight = evaluate_role_preflight(ROOT, role, config, runner_cfg=runner_cfg, state=state)
        lease = preflight.get("lease", {}) if isinstance(preflight.get("lease"), dict) else {}
        harness = str(config.get("Harness Type", config.get("harness_type", ""))) if isinstance(config, dict) else ""
        model = str(config.get("Model / Profile", config.get("model_profile", ""))) if isinstance(config, dict) else ""
        rows.append(
            {
                "role": role,
                "enabled": bool(preflight.get("schedule_enabled")),
                "registered": True,
                "status": str(preflight.get("status", "UNKNOWN")),
                "reason": str(preflight.get("reason", "")),
                "pending": int(preflight.get("pending_count", 0) or 0),
                "harness": harness,
                "model": model,
                "lease": str(lease.get("status", "unknown")),
                "command": str(preflight.get("command_preview", "")),
            }
        )
    return rows


def print_status(color: bool = True) -> None:
    rows = role_rows()
    print("ROLE JOBS")
    for row in rows:
        if not row["registered"]:
            print(f"[UNREGISTERED] {row['role']}")
            continue
        ready = "READY" if row["status"] not in {"SKIPPED_DISABLED", "UNREGISTERED"} else "NOT_READY"
        status_text = paint(row["status"], status_color(row["status"]), color)
        print(
            f"[{bool_marker(bool(row['enabled']), color)}] {row['role']} / {ready} / "
            f"{status_text} / pending {row['pending']} / {row['reason']}"
        )
        print(f"      {row['command']}")


def service_rows() -> list[dict[str, object]]:
    names = ["chief-chat", "runner", "telegram", "telegram-watchdog", "visualizer"]
    rows: list[dict[str, object]] = []
    for name in names:
        if name in {"telegram", "telegram-watchdog"} and not telegram_configured():
            rows.append({"name": name, "status": "optional_not_configured", "alive": False, "pid": 0})
            continue
        status = service_status(name)
        rows.append(
            {
                "name": name,
                "status": str(status.get("status", "inactive")),
                "alive": bool(status.get("alive")),
                "pid": int(status.get("pid", 0) or 0),
                "last_error": str(status.get("last_error", "")),
            }
        )
    return rows


def print_dashboard(color: bool = True) -> None:
    rows = role_rows()
    srows = service_rows()
    alerts = []
    for row in srows:
        if row["status"] not in {"active", "optional_not_configured"} and row["name"] != "visualizer":
            alerts.append(f"{row['name']} is {row['status']}")
    for row in rows:
        if row["registered"] and str(row["status"]).startswith("PAUSED"):
            alerts.append(f"{row['role']} is {row['status']}")
    print(paint("AGENTIC HARNESS DASHBOARD", C.BOLD, color))
    print(paint(f"root: {ROOT}", C.DIM, color))
    if alerts:
        print(paint("ALERTS", C.YELLOW, color))
        for item in alerts:
            print(paint(f"  - {item}", C.YELLOW, color))
        print("")
    print("")
    print(paint("SERVICES", C.CYAN, color))
    for row in srows:
        st = row["status"]
        alive = bool(row.get("alive"))
        pid = int(row.get("pid", 0) or 0)
        if st == "active" and alive:
            line = paint("ACTIVE", C.GREEN, color)
        elif st == "optional_not_configured":
            line = paint("OPTIONAL", C.DIM, color)
        elif alive:
            line = paint(st.upper(), C.YELLOW, color)
        else:
            line = paint(st.upper(), C.RED, color)
        print(f"  {row['name']:<17} {line:<18} pid={pid}")
        if row.get("last_error"):
            print(f"    last_error: {row['last_error']}")
    print("")
    print(paint("ROLES", C.CYAN, color))
    for row in rows:
        if not row["registered"]:
            print(f"  {row['role']:<16} {paint('UNREGISTERED', C.RED, color)}")
            continue
        status_text = paint(row["status"], status_color(row["status"]), color)
        enabled = bool_marker(bool(row["enabled"]), color)
        lease = str(row["lease"]).upper()
        harness = row["harness"] or "unknown"
        model = row["model"] or "default"
        print(
            f"  {row['role']:<16} [{enabled}] {status_text:<22} "
            f"pending={row['pending']:<2} lease={lease:<9} harness={harness} model={model}"
        )
        print(paint(f"    why: {row['reason']}", C.DIM, color))
        if row["command"]:
            print(paint(f"    run: {row['command']}", C.DIM, color))
    print("")
    print(paint("QUICK ACTIONS", C.CYAN, color))
    print("  py role_jobs.py enable Chief_of_Staff")
    print("  py role_jobs.py disable Chief_of_Staff")
    print("  py role_jobs.py prompt Researcher")
    print("  py service_manager.py start core")
    print("  py service_manager.py stop telegram")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or toggle Agentic Harness role cron jobs.")
    sub = parser.add_subparsers(dest="command", required=True)
    status_cmd = sub.add_parser("status")
    status_cmd.add_argument("--no-color", action="store_true")
    dash_cmd = sub.add_parser("dashboard")
    dash_cmd.add_argument("--no-color", action="store_true")
    dash_cmd.add_argument("--watch", type=float, default=0.0, help="Refresh every N seconds.")
    enable = sub.add_parser("enable")
    enable.add_argument("role")
    disable = sub.add_parser("disable")
    disable.add_argument("role")
    prompt_cmd = sub.add_parser("prompt")
    prompt_cmd.add_argument("role")
    prompt_cmd.add_argument("--short", action="store_true", help="Print only the short live-harness nudge.")
    prompt_cmd.add_argument("--claude-command", action="store_true", help="Print a Claude Code CLI command using the prompt.")
    args = parser.parse_args()

    if args.command == "status":
        print_status(color=not args.no_color and ANSI)
        return 0
    if args.command == "dashboard":
        use_color = not args.no_color and ANSI
        if args.watch and args.watch > 0:
            while True:
                if os.name == "nt":
                    os.system("cls")
                else:
                    os.system("clear")
                print_dashboard(color=use_color)
                time.sleep(max(0.5, args.watch))
        print_dashboard(color=use_color)
        return 0
    if args.command == "prompt":
        print(manual_role_prompt(args.role, short=args.short, claude_command=args.claude_command))
        return 0
    set_role_enabled(args.role, args.command == "enable")
    print(f"{args.role}: {'enabled' if args.command == 'enable' else 'disabled'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
