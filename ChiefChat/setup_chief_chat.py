#!/usr/bin/env python3
"""Setup/check helper for the fast ChiefChat service."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ChiefChat" / "CHIEF_CHAT_CONFIG.md"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def scalar(text: str, key: str) -> str:
    for raw in text.splitlines():
        if ":" not in raw:
            continue
        found, value = raw.split(":", 1)
        if found.strip() == key:
            return value.strip()
    return ""


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run(command: list[str]) -> bool:
    print(" ".join(command))
    completed = subprocess.run(command, cwd=str(ROOT))
    return completed.returncode == 0


def check_model_endpoint() -> tuple[bool, str]:
    config = read_text(CONFIG)
    provider = scalar(config, "Chat Provider") or "openai-compatible"
    if provider == "ollama":
        base = scalar(config, "Ollama Base URL") or "http://127.0.0.1:11434"
        url = base.rstrip("/") + "/api/tags"
    elif provider in {"openai-compatible", "openai", "lmstudio", "lm-studio"}:
        base = scalar(config, "OpenAI Compatible Base URL") or "http://127.0.0.1:1234/v1"
        url = base.rstrip("/")
        if url.endswith("/v1"):
            url += "/models"
    else:
        return True, f"Provider {provider} uses command/manual validation."
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status < 400, f"{url} responded with HTTP {response.status}"
    except Exception as exc:
        return False, f"{url} is not reachable yet: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/check ChiefChat optional dependencies.")
    parser.add_argument("--check-only", action="store_true", help="Only check; do not run installs.")
    args = parser.parse_args()

    print("ChiefChat setup/check")
    print(f"Root: {ROOT}")
    ok = True

    playwright_ok = module_available("playwright")
    if not playwright_ok:
        print("Playwright is not installed.")
        if not args.check_only:
            playwright_ok = run([sys.executable, "-m", "pip", "install", "playwright"])
    else:
        print("Playwright Python package: OK")
    ok = ok and playwright_ok

    if playwright_ok and not args.check_only:
        if not run([sys.executable, "-m", "playwright", "install", "chromium"]):
            ok = False
            print("Chromium install failed. Browser mode can still be fixed manually with:")
            print("py -m playwright install chromium")

    endpoint_ok, endpoint_detail = check_model_endpoint()
    print(f"Model endpoint: {endpoint_detail}")
    if not endpoint_ok:
        ok = False
        print("Start LM Studio/Ollama or edit ChiefChat\\CHIEF_CHAT_CONFIG.md to your preferred cheap model path.")

    print("ChiefChat setup OK" if ok else "ChiefChat setup needs attention")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
