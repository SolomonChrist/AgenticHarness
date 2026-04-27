#!/usr/bin/env python3
"""Fast Chief_of_Staff chat daemon backed by the markdown chat ledger."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chat_ledger import pending_operator_messages, update_chat_status
from coordination_io import append_line, atomic_write_text, read_text
from operator_messaging import active_human_id, append_operator_reply


RUNNING = True
CHIEF_ROLE = "Chief_of_Staff"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_bool(value: str, default: bool = False) -> bool:
    text = str(value or "").strip().upper()
    if text in {"YES", "TRUE", "1", "ON", "ACTIVE", "ENABLED"}:
        return True
    if text in {"NO", "FALSE", "0", "OFF", "DISABLED"}:
        return False
    return default


def parse_int(value: str, default: int) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def parse_float(value: str, default: float) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def parse_key_values(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def tail(path: Path, max_chars: int) -> str:
    text = read_text(path)
    return text[-max_chars:].strip()


def append_event(root: Path, message: str) -> None:
    append_line(root / "LAYER_LAST_ITEMS_DONE.md", f"[{iso_now()}] [CHIEF_CHAT] {message}")


def runtime_file(root: Path) -> Path:
    return root / "ChiefChat" / "data" / "runtime.json"


def update_runtime(root: Path, status: str, *, last_error: str = "") -> None:
    path = runtime_file(root)
    payload = {
        "component": "chief-chat",
        "status": status,
        "pid": os.getpid(),
        "updated_at": iso_now(),
        "last_error": last_error,
        "chat_ledger": str(root / "_messages" / "CHAT.md"),
    }
    atomic_write_text(path, json.dumps(payload, indent=2))


def config_path(root: Path) -> Path:
    return root / "ChiefChat" / "CHIEF_CHAT_CONFIG.md"


def load_config(root: Path) -> dict[str, str]:
    defaults = {
        "Chat Provider": "openai-compatible",
        "Chat Model": "local-model-name",
        "OpenAI Compatible Base URL": "http://127.0.0.1:1234/v1",
        "Ollama Base URL": "http://127.0.0.1:11434",
        "OpenCode Command Template": 'opencode run "{PROMPT}" --model "{MODEL}" --dir "{WORKDIR}"',
        "Reply Timeout Seconds": "20",
        "Max Messages Per Pass": "3",
        "Browser Enabled": "YES",
        "Browser Inactivity Timeout Seconds": "30",
        "Browser Max Run Seconds": "120",
        "Browser Headless": "NO",
        "Poll Seconds": "0.5",
        "Status Reply On Model Failure": "YES",
    }
    values = parse_key_values(config_path(root))
    return {**defaults, **values}


def soul_context(root: Path) -> str:
    parts = [
        ("Chief soul", root / "MEMORY" / "agents" / CHIEF_ROLE / "SOUL.md", 4000),
        ("Chief always memory", root / "MEMORY" / "agents" / CHIEF_ROLE / "ALWAYS.md", 5000),
        ("Human registry", root / "HUMANS.md", 3000),
        ("Role registry", root / "Runner" / "ROLE_LAUNCH_REGISTRY.md", 5000),
        ("Recent events", root / "LAYER_LAST_ITEMS_DONE.md", 5000),
        ("Task list", root / "LAYER_TASK_LIST.md", 6000),
    ]
    chunks: list[str] = []
    for label, path, limit in parts:
        content = tail(path, limit)
        if content:
            chunks.append(f"## {label}\n{content}")
    return "\n\n".join(chunks)


def recent_chat_context(root: Path, max_chars: int = 9000) -> str:
    return tail(root / "_messages" / "CHAT.md", max_chars)


def build_prompt(root: Path, message: dict[str, str], extra_context: str = "") -> str:
    body = message.get("body", "").strip()
    context = soul_context(root)
    chat = recent_chat_context(root)
    return f"""You are Chief_of_Staff, the user's fast human-feeling operator interface.

Use the Chief soul/personality and memory below. Be warm, direct, specific, and operational.
You are the orchestration layer. For deep coding, research, or long web work, create or route tasks instead of pretending the chat model did it.
Do not mention internal file paths, daemon cycles, or provider errors unless the user asks or it is needed to unblock them.
Keep the reply concise enough for Telegram.

{context}

## Recent unified chat
{chat}

## Extra local action context
{extra_context}

## New operator message
{body}

Reply as Chief_of_Staff."""


def http_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def openai_compatible_reply(config: dict[str, str], prompt: str) -> str:
    base = config.get("OpenAI Compatible Base URL", "http://127.0.0.1:1234/v1").rstrip("/")
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    payload = {
        "model": config.get("Chat Model", "local-model-name"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.35,
        "max_tokens": 600,
        "stream": False,
    }
    result = http_json(url, payload, parse_int(config.get("Reply Timeout Seconds", "20"), 20))
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI-compatible endpoint returned no choices.")
    message = choices[0].get("message", {})
    return str(message.get("content", "")).strip()


def ollama_reply(config: dict[str, str], prompt: str) -> str:
    base = config.get("Ollama Base URL", "http://127.0.0.1:11434").rstrip("/")
    payload = {
        "model": config.get("Chat Model", "llama3.1"),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    result = http_json(f"{base}/api/chat", payload, parse_int(config.get("Reply Timeout Seconds", "20"), 20))
    return str(result.get("message", {}).get("content", "")).strip()


def opencode_reply(root: Path, config: dict[str, str], prompt: str) -> str:
    template = config.get("OpenCode Command Template", "")
    if not template:
        raise RuntimeError("OpenCode Command Template is empty.")
    command = (
        template.replace("{PROMPT}", prompt.replace('"', '\\"'))
        .replace("{MODEL}", config.get("Chat Model", ""))
        .replace("{WORKDIR}", str(root))
    )
    completed = subprocess.run(
        command,
        cwd=str(root),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=parse_int(config.get("Reply Timeout Seconds", "20"), 20),
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "OpenCode command failed").strip())
    return completed.stdout.strip()


def fake_reply(_config: dict[str, str], message: dict[str, str]) -> str:
    text = message.get("body", "").strip()
    lowered = text.lower()
    if lowered in {"hi", "hello", "hey"}:
        return "I am here, online, and watching the system. What should we move next?"
    return f"I got it. I saved this in the shared chat and I am ready to route the next step: {text}"


def model_reply(root: Path, config: dict[str, str], prompt: str, message: dict[str, str]) -> str:
    provider = config.get("Chat Provider", "openai-compatible").strip().lower()
    if provider in {"fake", "test"}:
        return fake_reply(config, message)
    if provider in {"openai", "openai-compatible", "lmstudio", "lm-studio"}:
        return openai_compatible_reply(config, prompt)
    if provider == "ollama":
        return ollama_reply(config, prompt)
    if provider == "opencode":
        return opencode_reply(root, config, prompt)
    raise RuntimeError(f"Unknown Chat Provider: {provider}")


WEB_PATTERNS = [
    r"\b(search|google|look up|browse|browser|web|online|current|latest|today|news)\b",
    r"\b(weather|price|stock|website|page|url|research)\b",
]


def is_web_request(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in WEB_PATTERNS)


def task_exists(root: Path, task_id: str) -> bool:
    return task_id in read_text(root / "LAYER_TASK_LIST.md")


def append_web_task(root: Path, message: dict[str, str], note: str) -> str:
    msg_id = message.get("id", "") or "UNKNOWN"
    task_id = f"TASK-WEB-{msg_id.upper()}"
    if task_exists(root, task_id):
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat note for {task_id}: {note}")
        return task_id
    body = message.get("body", "").strip()
    block = f"""
## TASK
ID: {task_id}
Title: Web/current-info request from operator
Project: operator-requests
Owner Role: Researcher
Status: TODO
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Request:
{body}
ChiefChat Notes:
- {note}
Done When:
- The operator receives a sourced answer or a clear blocker
""".strip()
    append_line(root / "LAYER_TASK_LIST.md", block)
    append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] Researcher: web_task:{task_id}")
    return task_id


def browser_profile_dir(root: Path) -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME") or str(root / ".local_state")
    return Path(base) / "AgenticHarness" / "ChiefChat" / "browser-profile"


def try_browser_search(root: Path, config: dict[str, str], query: str) -> str:
    if not parse_bool(config.get("Browser Enabled", "YES"), True):
        return "Browser automation is disabled in ChiefChat config."
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return "Browser automation is not installed. Run `py ChiefChat\\setup_chief_chat.py` to install/check Playwright."

    max_seconds = parse_int(config.get("Browser Max Run Seconds", "120"), 120)
    headless = parse_bool(config.get("Browser Headless", "NO"), False)
    profile = browser_profile_dir(root)
    profile.mkdir(parents=True, exist_ok=True)
    search_url = "https://duckduckgo.com/?q=" + urllib.parse.quote(query)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(profile), headless=headless)
        try:
            page = context.new_page()
            page.goto(search_url, wait_until="domcontentloaded", timeout=max_seconds * 1000)
            page.wait_for_timeout(1500)
            title = page.title()
            body_text = page.locator("body").inner_text(timeout=5000)
            lines = [line.strip() for line in body_text.splitlines() if line.strip()]
            useful = "\n".join(lines[:12])
            return f"Opened browser search for: {query}\nPage title: {title}\nVisible result text:\n{useful[:1800]}"
        finally:
            context.close()


def setup_failure_reply(config: dict[str, str], error: Exception) -> str:
    provider = config.get("Chat Provider", "openai-compatible")
    if provider in {"openai-compatible", "openai", "lmstudio", "lm-studio"}:
        target = config.get("OpenAI Compatible Base URL", "http://127.0.0.1:1234/v1")
        return (
            "I received your message, but my cheap local chat model is not reachable yet. "
            f"Start LM Studio or another OpenAI-compatible server at `{target}`, then send the message again. "
            f"Last error: {error}"
        )
    if provider == "ollama":
        return (
            "I received your message, but Ollama is not reachable yet. "
            "Start Ollama and make sure the configured model is pulled, then send the message again. "
            f"Last error: {error}"
        )
    return f"I received your message, but the ChiefChat provider `{provider}` failed: {error}"


def process_message(root: Path, config: dict[str, str], message: dict[str, str]) -> bool:
    msg_id = message.get("id", "")
    if not msg_id:
        return False
    update_chat_status(root, msg_id, "processing")
    append_event(root, f"PROCESSING - Operator message {msg_id} via {message.get('channel', 'unknown')}")

    extra = ""
    if is_web_request(message.get("body", "")):
        task_id = append_web_task(root, message, "ChiefChat created this task before attempting local browser work.")
        browser_note = try_browser_search(root, config, message.get("body", ""))
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat browser note for {task_id}: {browser_note}")
        extra = f"Web task created: {task_id}\nLocal browser attempt:\n{browser_note}"

    prompt = build_prompt(root, message, extra_context=extra)
    try:
        reply = model_reply(root, config, prompt, message)
        if not reply:
            raise RuntimeError("model returned an empty reply")
    except Exception as exc:
        reply = setup_failure_reply(config, exc) if parse_bool(config.get("Status Reply On Model Failure", "YES"), True) else ""
        update_chat_status(root, msg_id, "failed")
        append_event(root, f"MODEL_FAILURE - Operator message {msg_id}: {exc}")
    else:
        update_chat_status(root, msg_id, "sent")

    if reply:
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"REPLIED - Operator message {msg_id}")
    return True


def run_once(root: Path) -> int:
    config = load_config(root)
    count = 0
    max_messages = max(1, parse_int(config.get("Max Messages Per Pass", "3"), 3))
    update_runtime(root, "active")
    for message in pending_operator_messages(root)[:max_messages]:
        if process_message(root, config, message):
            count += 1
    update_runtime(root, "active")
    return count


def status(root: Path) -> dict[str, Any]:
    runtime = {}
    try:
        runtime = json.loads(read_text(runtime_file(root)) or "{}")
    except Exception:
        runtime = {}
    return {
        "runtime": runtime,
        "pending_messages": len(pending_operator_messages(root)),
        "config": load_config(root),
    }


def shutdown(*_args: object) -> None:
    global RUNNING
    RUNNING = False


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast Chief_of_Staff chat service.")
    parser.add_argument("--root", default=str(ROOT), help="Agentic Harness root.")
    parser.add_argument("--once", action="store_true", help="Process pending messages once and exit.")
    parser.add_argument("--status", action="store_true", help="Print runtime status and exit.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.status:
        print(json.dumps(status(root), indent=2))
        return 0
    if args.once:
        processed = run_once(root)
        print(json.dumps({"processed": processed, **status(root)}, indent=2))
        return 0

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    config = load_config(root)
    poll_seconds = max(0.1, parse_float(config.get("Poll Seconds", "0.5"), 0.5))
    update_runtime(root, "active")
    append_event(root, "START - ChiefChat service started.")
    while RUNNING:
        try:
            run_once(root)
            time.sleep(poll_seconds)
        except Exception as exc:
            update_runtime(root, "degraded", last_error=str(exc))
            append_event(root, f"ERROR - {exc}")
            time.sleep(2)
    update_runtime(root, "stopped")
    append_event(root, "STOP - ChiefChat service stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
