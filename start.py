#!/usr/bin/env python3
"""One-command startup for an Agentic Harness install."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable or "python"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def parse_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def run(label: str, args: list[str]) -> int:
    print()
    print(f"== {label} ==")
    completed = subprocess.run(args, cwd=str(ROOT))
    return int(completed.returncode or 0)


def open_url_json(url: str, timeout: int = 2) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AgenticHarness-start/1.0"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def model_status() -> tuple[str, str]:
    config = {
        "Chat Provider": "openai-compatible",
        "Chat Model": "local-model-name",
        "OpenAI Compatible Base URL": "http://127.0.0.1:1234/v1",
        "Ollama Base URL": "http://127.0.0.1:11434",
    }
    config.update(parse_key_values(ROOT / "ChiefChat" / "CHIEF_CHAT_CONFIG.md"))
    provider = config.get("Chat Provider", "openai-compatible").strip().lower()
    model = config.get("Chat Model", "local-model-name").strip() or "provider default"

    if provider in {"fake", "test"}:
        return "ok", "ChiefChat is using the fake/test model path."
    if provider in {"openai", "openai-compatible", "lmstudio", "lm-studio"}:
        base = config.get("OpenAI Compatible Base URL", "http://127.0.0.1:1234/v1").rstrip("/")
        try:
            payload = open_url_json(f"{base}/models")
            models = [
                str(item.get("id", "")).strip()
                for item in payload.get("data", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip()
            ]
            detail = ", ".join(models[:3]) if models else model
            return "ok", f"Local OpenAI-compatible model server is reachable at {base}. Models: {detail}"
        except Exception as exc:
            return (
                "warn",
                f"ChiefChat is configured for an OpenAI-compatible local model at {base}, but it is not reachable: {exc}",
            )
    if provider == "ollama":
        base = config.get("Ollama Base URL", "http://127.0.0.1:11434").rstrip("/")
        try:
            payload = open_url_json(f"{base}/api/tags")
            models = [
                str(item.get("name", "")).strip()
                for item in payload.get("models", [])
                if isinstance(item, dict) and str(item.get("name", "")).strip()
            ]
            detail = ", ".join(models[:3]) if models else model
            return "ok", f"Ollama is reachable at {base}. Models: {detail}"
        except Exception as exc:
            return "warn", f"ChiefChat is configured for Ollama at {base}, but it is not reachable: {exc}"
    if provider == "opencode":
        return "info", "ChiefChat is configured for OpenCode CLI. Make sure `opencode` is available on PATH."
    return "info", f"ChiefChat provider is `{provider}`. Check ChiefChat/CHIEF_CHAT_CONFIG.md if replies fail."


def print_model_status() -> None:
    state, message = model_status()
    print()
    print("== Local Model Check ==")
    prefix = {"ok": "OK", "warn": "WARNING", "info": "INFO"}.get(state, "INFO")
    print(f"{prefix}: {message}")
    if state == "warn":
        print("Start LM Studio/Ollama or change ChiefChat/CHIEF_CHAT_CONFIG.md, then send Telegram a test message.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Agentic Harness with one command.")
    parser.add_argument("--core", action="store_true", help="Start only ChiefChat, Runner, and Telegram when configured.")
    parser.add_argument("--no-check", action="store_true", help="Skip production_check.py.")
    parser.add_argument("--no-model-check", action="store_true", help="Skip the local model endpoint check.")
    parser.add_argument("--open-dashboard", action="store_true", help="Open the Visualizer dashboard URL after startup.")
    args = parser.parse_args()

    print("Agentic Harness startup")
    print(f"Root: {ROOT}")
    target = "core" if args.core else "all"

    exit_code = run(f"Starting services ({target})", [PYTHON, "service_manager.py", "start", target])
    exit_code = max(exit_code, run("Service status", [PYTHON, "service_manager.py", "status", "all"]))
    if not args.no_check:
        exit_code = max(exit_code, run("Production check", [PYTHON, "production_check.py"]))
    if not args.no_model_check:
        print_model_status()
    if args.open_dashboard:
        webbrowser.open("http://127.0.0.1:8787/dashboard.html")
        print()
        print("Opened Visualizer dashboard: http://127.0.0.1:8787/dashboard.html")

    print()
    if exit_code == 0:
        print("Startup complete.")
    else:
        print("Startup finished with warnings or errors. Read the output above.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
