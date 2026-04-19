#!/usr/bin/env python3
"""
Configure a role to be owned by the Runner daemon.

This is the handoff path after a manual first claim:
- the human/manual harness proves the role once
- this helper records the CLI provider Runner should use
- Runner can then wake the role from Telegram, role dispatches, or timers
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNNER_CONFIG = ROOT / "Runner" / "RUNNER_CONFIG.md"
ROLE_REGISTRY = ROOT / "Runner" / "ROLE_LAUNCH_REGISTRY.md"
HARNESS_CATALOG = ROOT / "Runner" / "HARNESS_CATALOG.md"

PROVIDER_COMMANDS = {
    "claude": ("Claude Code", "{AUTO_CLAUDE_CYCLE}"),
    "opencode": ("OpenCode", "{AUTO_OPENCODE_CYCLE}"),
    "goose": ("Goose", "{AUTO_GOOSE_CYCLE}"),
    "ollama": ("Ollama", "{AUTO_OLLAMA_CYCLE}"),
}


def replace_key(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(key)}:\s*).*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(rf"\g<1>{value}", text, count=1)
    return text.rstrip() + f"\n{key}: {value}\n"


def set_runner_active() -> None:
    text = RUNNER_CONFIG.read_text(encoding="utf-8")
    text = replace_key(text, "Runner Enabled", "YES")
    text = replace_key(text, "Runner Mode", "ACTIVE")
    text = replace_key(text, "Fast Wake Poll Seconds", "1")
    text = replace_key(text, "Urgent Wake Backoff Seconds", "8")
    RUNNER_CONFIG.write_text(text, encoding="utf-8")


def provider_details(provider: str, name: str, command_template: str) -> tuple[str, str, str]:
    if provider == "custom":
        if not name.strip():
            raise SystemExit("--name is required when --provider custom")
        if not command_template.strip():
            raise SystemExit("--command-template is required when --provider custom")
        if "{PROMPT}" not in command_template and "{PROMPT_FILE}" not in command_template:
            raise SystemExit("custom command template must include {PROMPT} or {PROMPT_FILE}")
        return name.strip(), command_template.strip(), f"custom-{name.strip()}"
    harness_type, launch_command = PROVIDER_COMMANDS[provider]
    return harness_type, launch_command, provider


def role_block(role: str, provider: str, model: str, interval: int, bootstrap: str, name: str, command_template: str) -> str:
    harness_type, launch_command, provider_key = provider_details(provider, name, command_template)
    harness_key = f"{provider_key}-{model}".strip("-") if model else provider_key
    prompt = (
        f"This is an existing Agentic Harness system. "
        f"Claim or renew the {role} role if available or stale, check messages and tasks, "
        "reply to the operator when needed, then exit."
    )
    wake_message = "Check operator messages, check status, reply if needed, and continue orchestration."
    if role != "Chief_of_Staff":
        wake_message = f"Check messages for {role}, check assigned tasks, continue work, then report status."

    return f"""### ROLE
Role: {role}
Enabled: YES
Automation Ready: YES
Execution Mode: interval
Harness Key: {harness_key}
Harness Type: {harness_type}
Launch Command: {launch_command}
Working Directory: {ROOT}
Model / Profile: {model}
Bootstrap File: {bootstrap}
Startup Prompt: {prompt}
Wake Message: {wake_message}
Check Interval Minutes: {interval}
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source: configure_role_daemon.py
Last Confirmed:
Notes: Daemon-owned CLI cycle. Safe to close the original desktop/manual harness after this is configured and Runner is running.
"""


def upsert_role(role: str, provider: str, model: str, interval: int, bootstrap: str, name: str, command_template: str) -> None:
    text = ROLE_REGISTRY.read_text(encoding="utf-8")
    block = role_block(role, provider, model, interval, bootstrap, name, command_template).rstrip()
    pattern = re.compile(
        rf"### ROLE\s*\nRole:\s*{re.escape(role)}\s*\n.*?(?=\n### |\Z)",
        re.DOTALL,
    )
    if pattern.search(text):
        text = pattern.sub(lambda _match: block, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    ROLE_REGISTRY.write_text(text, encoding="utf-8")


def upsert_custom_harness(name: str, command_template: str, model: str) -> None:
    if not name.strip():
        return
    catalog = HARNESS_CATALOG.read_text(encoding="utf-8")
    key = f"custom-{name.strip()}"
    block = f"""### HARNESS
Harness Key: {key}
Display Name: {name.strip()}
Family: Custom CLI
Available On This System: YES
Default Launch Command: {command_template.strip()}
Default Working Directory: {ROOT}
Default Role Types:
- Chief_of_Staff
- Researcher
- Engineer
Model / Profile Notes: {model.strip() or 'Use CLI default if blank.'}
Prompt / Bootstrap Notes: Command templates may use {{PROMPT}}, {{PROMPT_FILE}}, {{ROLE}}, {{WORKDIR}}, and {{MODEL}}.
Last Confirmed:
Learned From: configure_role_daemon.py
Notes: User-supplied prompt-based CLI provider.
""".rstrip()
    pattern = re.compile(
        rf"### HARNESS\s*\nHarness Key:\s*{re.escape(key)}\s*\n.*?(?=\n### |\Z)",
        re.DOTALL,
    )
    if pattern.search(catalog):
        catalog = pattern.sub(lambda _match: block, catalog, count=1)
    else:
        catalog = catalog.rstrip() + "\n\n" + block + "\n"
    HARNESS_CATALOG.write_text(catalog, encoding="utf-8")


def start_runner() -> int:
    return subprocess.call([sys.executable, "service_manager.py", "start", "runner"], cwd=str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure a role for daemon-owned Runner automation.")
    parser.add_argument("--role", default="Chief_of_Staff")
    parser.add_argument("--provider", choices=sorted([*PROVIDER_COMMANDS, "custom"]), required=True)
    parser.add_argument("--name", default="", help="Display/provider name for --provider custom.")
    parser.add_argument("--command-template", default="", help="Custom CLI command template using {PROMPT} or {PROMPT_FILE}.")
    parser.add_argument("--model", default="")
    parser.add_argument("--interval-minutes", type=int, default=2)
    parser.add_argument("--bootstrap-file", default="AGENTIC_HARNESS_TINY.md")
    parser.add_argument("--start-runner", action="store_true")
    args = parser.parse_args()

    set_runner_active()
    upsert_role(
        args.role,
        args.provider,
        args.model.strip(),
        max(1, args.interval_minutes),
        args.bootstrap_file,
        args.name,
        args.command_template,
    )
    if args.provider == "custom":
        upsert_custom_harness(args.name, args.command_template, args.model)
    print(f"Configured {args.role} as daemon-owned via {args.provider}.")
    print("Runner is set to ACTIVE.")
    if args.start_runner:
        return start_runner()
    print("Start Runner with: py service_manager.py start runner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
