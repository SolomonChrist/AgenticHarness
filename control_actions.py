#!/usr/bin/env python3
"""Deterministic operator control actions shared by Telegram and Visualizer."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from coordination_io import append_line, read_text


ROOT = Path(__file__).resolve().parent
ROLE_REGISTRY = ROOT / "Runner" / "ROLE_LAUNCH_REGISTRY.md"
WAKE_QUEUE = ROOT / "Runner" / "_wake_requests.md"


MODEL_ALIASES = {
    ("claude", "haiku"): "claude-haiku-4-5-20251001",
    ("claude", "sonnet"): "claude-sonnet-4-5-20250929",
}

PROVIDER_ALIASES = {
    "claude": "claude",
    "claude code": "claude",
    "opencode": "opencode",
    "open code": "opencode",
    "goose": "goose",
    "ollama": "ollama",
}


def iso_now() -> str:
    from datetime import datetime

    return datetime.now().astimezone().isoformat(timespec="seconds")


def scalar(block: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", block, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def role_block(role: str) -> str:
    text = read_text(ROLE_REGISTRY)
    pattern = re.compile(
        rf"### ROLE\s*\nRole:\s*{re.escape(role)}\s*\n.*?(?=\n### |\Z)",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


def normalize_provider(text: str) -> str:
    lowered = text.lower()
    for label, provider in PROVIDER_ALIASES.items():
        if label in lowered:
            return provider
    return ""


def normalize_model(provider: str, text: str) -> str:
    lowered = text.lower()
    for (model_provider, label), model in MODEL_ALIASES.items():
        if provider == model_provider and label in lowered:
            return model
    match = re.search(r"\b(claude-[a-z0-9.-]+|[a-z0-9][a-z0-9._:-]{2,})\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def configure_role(role: str, provider: str, model: str) -> tuple[bool, str]:
    command = [
        sys.executable,
        "configure_role_daemon.py",
        "--role",
        role,
        "--provider",
        provider,
        "--model",
        model,
        "--bootstrap-file",
        "AGENTIC_HARNESS_TINY.md",
        "--start-runner",
    ]
    completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout or "configuration command failed").strip()
    append_line(WAKE_QUEUE, f"[{iso_now()}] {role}: operator_configured_daemon")
    return True, completed.stdout.strip()


def default_provider_model_for(role: str) -> tuple[str, str]:
    block = role_block(role)
    provider_text = scalar(block, "Harness Type") or scalar(block, "Harness Key")
    model = scalar(block, "Model / Profile")
    provider = normalize_provider(provider_text)
    if provider and model:
        return provider, model
    chief = role_block("Chief_of_Staff")
    chief_provider = normalize_provider(scalar(chief, "Harness Type") or scalar(chief, "Harness Key"))
    chief_model = scalar(chief, "Model / Profile")
    return chief_provider or "claude", chief_model or "claude-haiku-4-5-20251001"


def current_harness_reply(role: str = "Chief_of_Staff") -> str:
    block = role_block(role)
    if not block:
        return f"{role} is not registered with Runner yet."
    return (
        f"{role} is currently set to:\n"
        f"- Harness: {scalar(block, 'Harness Type') or scalar(block, 'Harness Key') or 'unknown'}\n"
        f"- Model: {scalar(block, 'Model / Profile') or 'default'}\n"
        f"- Mode: {scalar(block, 'Execution Mode') or 'unknown'}\n"
        f"- Automation ready: {scalar(block, 'Automation Ready') or 'NO'}"
    )


def maybe_handle_control_message(text: str) -> str | None:
    lowered = text.lower()

    if re.search(r"\b(what|which)\b.*\b(harness|model)\b.*\b(on|using|running)\b", lowered):
        return current_harness_reply("Chief_of_Staff")

    if "reset yourself" in lowered or "switch yourself" in lowered or "change yourself" in lowered:
        provider = normalize_provider(lowered)
        model = normalize_model(provider, lowered) if provider else ""
        if not provider:
            return "Which CLI provider should I switch Chief_of_Staff to? For example: Claude Code, OpenCode, Goose, or Ollama."
        if not model:
            return "Which model should I use for Chief_of_Staff?"
        ok, detail = configure_role("Chief_of_Staff", provider, model)
        if not ok:
            return f"I tried to switch Chief_of_Staff, but the daemon update failed:\n{detail}"
        return f"Chief_of_Staff is now configured for {provider} / {model}. Runner will use that on the next wake."

    role_match = re.search(r"\b(use|set|launch|start|spawn|setup|configure|daemonize)\b.*\b(researcher|engineer|qa|documentation)\b", lowered)
    if role_match:
        role = role_match.group(2).capitalize()
        if role == "Qa":
            role = "QA"
        provider = normalize_provider(lowered)
        model = normalize_model(provider, lowered) if provider else ""
        if not provider:
            provider, model = default_provider_model_for(role)
        if not model:
            _, model = default_provider_model_for(role)
        ok, detail = configure_role(role, provider, model)
        if not ok:
            return f"I tried to configure {role}, but it failed:\n{detail}"
        return f"{role} is now daemonized on {provider} / {model}. Runner can wake it automatically."

    return None
