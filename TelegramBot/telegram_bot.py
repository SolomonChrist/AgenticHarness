#!/usr/bin/env python3
"""
Telegram bridge for the active Chief_of_Staff / MasterBot.

This layer only moves messages between Telegram and the V13 markdown files.
"""

from __future__ import annotations

import html
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Run: pip install requests python-dotenv")
    sys.exit(1)


HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env.telegram")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_IDS = [
    int(part.strip())
    for part in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
    if part.strip().isdigit()
]
HARNESS_ROOT = Path(os.getenv("HARNESS_ROOT", str(HERE.parent))).resolve()
HUMAN_ID = os.getenv("HUMAN_ID", "").strip()
BOT_NAME = os.getenv("BOT_NAME", "Harness Bridge").strip() or "Harness Bridge"
OWNER_NAME = os.getenv("OWNER_NAME", "Operator").strip() or "Operator"
POLL_INTERVAL = max(5, int(os.getenv("POLL_INTERVAL_SECONDS", "10")))

if not BOT_TOKEN:
    print("TELEGRAM_BOT_TOKEN not set.")
    sys.exit(1)

if not ALLOWED_USER_IDS:
    print("TELEGRAM_ALLOWED_USER_IDS not set.")
    sys.exit(1)

if not HUMAN_ID:
    print("HUMAN_ID not set.")
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
RUNNING = True
DATA_DIR = HERE / "data"
STATE_FILE = DATA_DIR / "state.json"
CHIEF_FILE = HARNESS_ROOT / "_messages" / "Chief_of_Staff.md"
HUMAN_FILE = HARNESS_ROOT / "_messages" / f"human_{HUMAN_ID}.md"
EVENT_FILE = HARNESS_ROOT / "LAYER_LAST_ITEMS_DONE.md"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHIEF_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_update_id": 0, "seen_human_lines": []}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_update_id": 0, "seen_human_lines": []}


def save_state(state: dict) -> None:
    ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


STATE = load_state()


def tg(method: str, **kwargs) -> dict:
    try:
        response = requests.post(f"{API_BASE}/{method}", json=kwargs, timeout=20)
        return response.json()
    except Exception:
        return {"ok": False}


def send(chat_id: int, text: str) -> None:
    safe = html.escape(text, quote=False)
    chunks = [safe[i:i + 3900] for i in range(0, max(len(safe), 1), 3900)]
    for chunk in chunks:
        tg("sendMessage", chat_id=chat_id, text=chunk, parse_mode="HTML")


def is_allowed(user_id: int | None) -> bool:
    return bool(user_id in ALLOWED_USER_IDS)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_text(path)
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(existing + prefix + line + "\n", encoding="utf-8")


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log_event(line: str) -> None:
    append_line(EVENT_FILE, line)


def validate_root() -> bool:
    return (HARNESS_ROOT / "AGENTIC_HARNESS.md").exists()


def write_user_message(message: str, source: str = "telegram") -> None:
    ts = iso_now()
    append_line(CHIEF_FILE, f"[{ts}] [{source}] [{HUMAN_ID}] {message}")
    log_event(f"[{ts}] [TELEGRAM_BRIDGE] NOTIFY - Operator message routed to Chief_of_Staff")


def write_wake_message() -> None:
    ts = iso_now()
    append_line(
        CHIEF_FILE,
        f"[{ts}] [telegram] [{HUMAN_ID}] Wake request received. Please review messages and continue orchestration.",
    )
    log_event(f"[{ts}] [TELEGRAM_BRIDGE] NOTIFY - Wake request sent to Chief_of_Staff")


def help_text() -> str:
    return (
        f"Hello {OWNER_NAME}. I'm {BOT_NAME}.\n\n"
        "I only bridge messages to the active MasterBot.\n\n"
        "Commands:\n"
        "/start\n"
        "/help\n"
        "/wake\n\n"
        "Any other message is sent directly to Chief_of_Staff."
    )


def handle_command(text: str) -> str:
    if text.startswith("/start") or text.startswith("/help"):
        return help_text()
    if text.startswith("/wake"):
        write_wake_message()
        return "Wake message sent to Chief_of_Staff."
    write_user_message(text)
    return "Message sent to Chief_of_Staff."


def poll_human_replies() -> None:
    while RUNNING:
        content = read_text(HUMAN_FILE)
        seen = set(STATE.get("seen_human_lines", []))
        changed = False
        for line in content.splitlines():
            entry = line.strip()
            if not entry or entry in seen:
                continue
            for user_id in ALLOWED_USER_IDS:
                send(user_id, entry)
            seen.add(entry)
            changed = True
        if changed:
            STATE["seen_human_lines"] = list(seen)[-1000:]
            save_state(STATE)
        time.sleep(POLL_INTERVAL)


def poll_updates() -> None:
    global RUNNING
    while RUNNING:
        response = tg("getUpdates", timeout=25, offset=STATE.get("last_update_id", 0) + 1)
        if not response.get("ok"):
            time.sleep(3)
            continue
        for update in response.get("result", []):
            STATE["last_update_id"] = update["update_id"]
            message = update.get("message", {})
            chat = message.get("chat", {})
            user = message.get("from", {})
            text = message.get("text", "").strip()
            if not text:
                continue
            if not is_allowed(user.get("id")):
                send(chat.get("id"), "Unauthorized.")
                continue
            reply = handle_command(text)
            send(chat.get("id"), reply)
            save_state(STATE)


def shutdown(*_args) -> None:
    global RUNNING
    RUNNING = False
    save_state(STATE)
    sys.exit(0)


def main() -> None:
    ensure_dirs()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    print(f"Starting {BOT_NAME} for {HARNESS_ROOT}")
    if not validate_root():
        print(f"Harness root not found or missing AGENTIC_HARNESS.md: {HARNESS_ROOT}")
    if not HUMAN_FILE.exists():
        HUMAN_FILE.write_text("", encoding="utf-8")
    threading.Thread(target=poll_human_replies, daemon=True).start()
    poll_updates()


if __name__ == "__main__":
    main()
