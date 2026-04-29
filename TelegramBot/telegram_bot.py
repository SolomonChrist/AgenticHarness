#!/usr/bin/env python3
"""
Telegram bridge for the active Chief_of_Staff / MasterBot.

This layer only moves messages between Telegram and the Agentic Harness markdown files.
"""

from __future__ import annotations

import html
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Run: pip install requests python-dotenv")
    sys.exit(1)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordination_io import append_line as append_line_safe, atomic_write_text, read_text
from control_actions import maybe_handle_control_message
from message_filters import clean_operator_reply
from operator_messaging import append_operator_message, collect_telegram_feed

load_dotenv(HERE / ".env.telegram", encoding="utf-8-sig")

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
POLL_INTERVAL = max(1, int(os.getenv("POLL_INTERVAL_SECONDS", "2")))
REPLY_WAIT_SECONDS = max(0, int(os.getenv("TELEGRAM_REPLY_WAIT_SECONDS", "20")))
ACK_AFTER_SECONDS = max(0, int(os.getenv("TELEGRAM_ACK_AFTER_SECONDS", "0")))
TYPING_INTERVAL_SECONDS = max(2, int(os.getenv("TELEGRAM_TYPING_INTERVAL_SECONDS", "4")))
USE_ENV_PROXY = os.getenv("TELEGRAM_USE_ENV_PROXY", "NO").strip().upper() in {"YES", "TRUE", "1", "ON"}
TRIGGER_RUNNER_ON_MESSAGE = os.getenv("TELEGRAM_TRIGGER_RUNNER_ON_MESSAGE", "YES").strip().upper() in {"YES", "TRUE", "1", "ON"}
TRIGGER_RUNNER_MIN_SECONDS = max(0, int(os.getenv("TELEGRAM_TRIGGER_RUNNER_MIN_SECONDS", "20")))
WAIT_FOR_REPLY_ON_MESSAGE = os.getenv("TELEGRAM_WAIT_FOR_REPLY_ON_MESSAGE", "YES").strip().upper() in {"YES", "TRUE", "1", "ON"}

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
RUNTIME_FILE = DATA_DIR / "runtime.json"
LOCK_FILE = DATA_DIR / "telegram.lock"
CHIEF_FILE = HARNESS_ROOT / "_messages" / "Chief_of_Staff.md"
HUMAN_FILE = HARNESS_ROOT / "_messages" / f"human_{HUMAN_ID}.md"
EVENT_FILE = HARNESS_ROOT / "LAYER_LAST_ITEMS_DONE.md"
RUNNER_WAKE_FILE = HARNESS_ROOT / "Runner" / "_wake_requests.md"
REMINDERS_FILE = HARNESS_ROOT / "Runner" / "_reminders.json"
RUNNER_CONFIG_FILE = HARNESS_ROOT / "Runner" / "RUNNER_CONFIG.md"
ROLE_REGISTRY_FILE = HARNESS_ROOT / "Runner" / "ROLE_LAUNCH_REGISTRY.md"
RUNNER_RUNTIME_FILE = HARNESS_ROOT / "Runner" / ".runner_runtime.json"
CHIEF_CHAT_RUNTIME_FILE = HARNESS_ROOT / "ChiefChat" / "data" / "runtime.json"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHIEF_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_update_id": 0, "seen_human_message_hashes": []}
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        state.setdefault("last_update_id", 0)
        state.setdefault("seen_human_message_hashes", [])
        return state
    except Exception:
        return {"last_update_id": 0, "seen_human_message_hashes": []}


def save_state(state: dict) -> None:
    ensure_dirs()
    with STATE_LOCK:
        atomic_write_text(STATE_FILE, json.dumps(state, indent=2))


def update_runtime(status: str, *, last_error: str = "") -> None:
    chief_ready = chief_chat_ready()
    ensure_dirs()
    payload = {
        "component": "telegram",
        "status": status,
        "pid": os.getpid(),
        "bot_name": BOT_NAME,
        "harness_root": str(HARNESS_ROOT),
        "human_id": HUMAN_ID,
        "updated_at": iso_now(),
        "last_error": last_error,
        "harness_root_valid": validate_root(),
        "chief_file_exists": CHIEF_FILE.exists(),
        "human_file_exists": HUMAN_FILE.exists(),
        "chief_responder_ready": chief_ready,
        "chief_responder_status": "chief_chat_ready" if chief_ready else "bridge_only_needs_chief_chat",
        "runner_daemon_alive": runner_daemon_alive(),
    }
    atomic_write_text(RUNTIME_FILE, json.dumps(payload, indent=2))


STATE = load_state()
LAST_TELEGRAM_ERROR = ""
LAST_RUNNER_TRIGGER_AT = 0.0
STATE_LOCK = threading.Lock()
RUNNER_TRIGGER_LOCK = threading.Lock()
TELEGRAM_SESSION = requests.Session()
TELEGRAM_SESSION.trust_env = USE_ENV_PROXY


def sanitize_error(text: object) -> str:
    clean = str(text or "")
    if BOT_TOKEN:
        clean = clean.replace(BOT_TOKEN, "<telegram-token>")
    clean = re.sub(r"/bot[^/\s]+", "/bot<telegram-token>", clean)
    return clean


def tg(method: str, **kwargs) -> dict:
    global LAST_TELEGRAM_ERROR
    try:
        response = TELEGRAM_SESSION.post(f"{API_BASE}/{method}", json=kwargs, timeout=20)
        payload = response.json()
        if not payload.get("ok"):
            LAST_TELEGRAM_ERROR = sanitize_error(f"{method}: {payload.get('description', payload)}")
            update_runtime("degraded", last_error=LAST_TELEGRAM_ERROR)
        return payload
    except Exception as exc:
        LAST_TELEGRAM_ERROR = sanitize_error(f"{method}: {exc}")
        update_runtime("degraded", last_error=LAST_TELEGRAM_ERROR)
        return {"ok": False, "description": LAST_TELEGRAM_ERROR}


def send(chat_id: int, text: str) -> bool:
    safe = html.escape(text, quote=False)
    chunks = [safe[i:i + 3900] for i in range(0, max(len(safe), 1), 3900)]
    ok = True
    for chunk in chunks:
        result = tg("sendMessage", chat_id=chat_id, text=chunk, parse_mode="HTML")
        ok = ok and bool(result.get("ok"))
    return ok


def send_typing(chat_id: int) -> None:
    tg("sendChatAction", chat_id=chat_id, action="typing")


def is_allowed(user_id: int | None) -> bool:
    return bool(user_id in ALLOWED_USER_IDS)


def append_line(path: Path, line: str) -> None:
    append_line_safe(path, line)


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log_event(line: str) -> None:
    append_line(EVENT_FILE, line)


def validate_root() -> bool:
    return (HARNESS_ROOT / "AGENTIC_HARNESS.md").exists()


def markdown_scalar(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def role_registry_block(role: str) -> str:
    text = read_text(ROLE_REGISTRY_FILE)
    pattern = re.compile(
        rf"### ROLE\s*\nRole:\s*{re.escape(role)}\s*\n.*?(?=\n### |\Z)",
        flags=re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


def truthy_value(value: str) -> bool:
    return value.strip().upper() in {"YES", "TRUE", "ACTIVE", "ENABLED"}


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            process_query_limited_information = 0x1000
            still_active = 259
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == still_active
            finally:
                kernel32.CloseHandle(handle)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_single_instance_lock() -> None:
    ensure_dirs()
    try:
        existing = json.loads(read_text(LOCK_FILE) or "{}")
    except Exception:
        existing = {}
    existing_pid = int(existing.get("pid", 0) or 0)
    if existing_pid and process_alive(existing_pid) and existing_pid != os.getpid():
        print(f"Telegram bridge already running for this workspace (pid {existing_pid}).")
        raise SystemExit(0)
    atomic_write_text(
        LOCK_FILE,
        json.dumps({"pid": os.getpid(), "started_at": iso_now()}, indent=2),
    )


def release_single_instance_lock() -> None:
    try:
        existing = json.loads(read_text(LOCK_FILE) or "{}")
    except Exception:
        existing = {}
    if int(existing.get("pid", 0) or 0) == os.getpid():
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass


def runner_daemon_alive() -> bool:
    try:
        runtime = json.loads(read_text(RUNNER_RUNTIME_FILE) or "{}")
    except Exception:
        return False
    if str(runtime.get("status", "")).lower() != "active":
        return False
    try:
        pid = int(runtime.get("pid", 0) or 0)
    except Exception:
        pid = 0
    return process_alive(pid)


def chief_daemon_ready() -> bool:
    runner_mode = markdown_scalar(read_text(RUNNER_CONFIG_FILE), "Runner Mode").upper()
    block = role_registry_block("Chief_of_Staff")
    return (
        runner_mode == "ACTIVE"
        and truthy_value(markdown_scalar(block, "Enabled"))
        and truthy_value(markdown_scalar(block, "Automation Ready"))
        and bool(markdown_scalar(block, "Launch Command"))
        and runner_daemon_alive()
    )


def chief_chat_ready() -> bool:
    try:
        runtime = json.loads(read_text(CHIEF_CHAT_RUNTIME_FILE) or "{}")
    except Exception:
        return False
    if str(runtime.get("status", "")).lower() != "active":
        return False
    try:
        pid = int(runtime.get("pid", 0) or 0)
    except Exception:
        pid = 0
    return process_alive(pid)


def chief_daemon_fallback_text() -> str:
    if not chief_chat_ready():
        return (
            "I got your message, but the fast ChiefChat service is not active right now, "
            "so I cannot produce the live Chief reply yet.\n\n"
            "On the computer, run:\n"
            "py service_manager.py start chief-chat\n\n"
            "Then verify with:\n"
            "py production_check.py"
        )
    return (
        "I got your message, but the Chief_of_Staff daemon handoff is not complete yet. "
        "Telegram is connected, but the background Chief responder is not armed.\n\n"
        "On the computer, run:\n"
        "py configure_role_daemon.py --role Chief_of_Staff --provider claude --model claude-haiku-4-5-20251001 --start-runner\n\n"
        "Then run:\n"
        "py production_check.py"
    )


def write_user_message(message: str, source: str = "telegram") -> dict[str, str]:
    return append_operator_message(HARNESS_ROOT, message, source=source, human_id=HUMAN_ID)


def trigger_chief_runner(reason: str = "telegram_message") -> bool:
    global LAST_RUNNER_TRIGGER_AT
    if not TRIGGER_RUNNER_ON_MESSAGE or not chief_daemon_ready():
        return False


def trigger_chief_chat(reason: str = "telegram_message") -> bool:
    if chief_chat_ready():
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] TRIGGER - ChiefChat already active for {reason or 'telegram_message'}")
        return True
    script = HARNESS_ROOT / "ChiefChat" / "chief_chat_service.py"
    if not script.exists():
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] WARN - Cannot trigger ChiefChat; missing {script}")
        return False
    command = [sys.executable, str(script), "--once", "--root", str(HARNESS_ROOT)]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        subprocess.Popen(
            command,
            cwd=str(HARNESS_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] TRIGGER - Started one-shot ChiefChat for {reason or 'telegram_message'}")
        return True
    except Exception as exc:
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] ERROR - Could not trigger ChiefChat: {sanitize_error(exc)}")
        return False
    script = HARNESS_ROOT / "Runner" / "scheduled_role_runner.py"
    if not script.exists():
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] WARN - Cannot trigger Chief; missing {script}")
        return False
    now = time.time()
    with RUNNER_TRIGGER_LOCK:
        if TRIGGER_RUNNER_MIN_SECONDS and now - LAST_RUNNER_TRIGGER_AT < TRIGGER_RUNNER_MIN_SECONDS:
            return False
        LAST_RUNNER_TRIGGER_AT = now
    command = [
        sys.executable,
        str(script),
        "--role",
        "Chief_of_Staff",
        "--reason",
        reason or "telegram_message",
    ]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        subprocess.Popen(
            command,
            cwd=str(HARNESS_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] TRIGGER - Started one-shot Chief_of_Staff runner for {reason or 'telegram_message'}")
        return True
    except Exception as exc:
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] ERROR - Could not trigger Chief runner: {sanitize_error(exc)}")
        return False


def write_wake_message() -> None:
    ts = iso_now()
    append_line(
        CHIEF_FILE,
        f"[{ts}] [telegram] [{HUMAN_ID}] Wake request received. Please review messages and continue orchestration.",
    )
    append_line(RUNNER_WAKE_FILE, f"[{ts}] Chief_of_Staff: wake_request")
    trigger_chief_chat("wake_request")
    log_event(f"[{ts}] [TELEGRAM_BRIDGE] NOTIFY - Wake request sent to Chief_of_Staff")


def parse_reminder_request(text: str) -> tuple[datetime, str] | None:
    match = re.search(
        r"\bremind\s+me\s+in\s+(\d+)\s+(second|seconds|minute|minutes|hour|hours)\s+(?:to\s+)?(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    reminder_text = match.group(3).strip(" .")
    if not reminder_text:
        return None
    if unit.startswith("second"):
        due_at = datetime.now().astimezone() + timedelta(seconds=amount)
    elif unit.startswith("minute"):
        due_at = datetime.now().astimezone() + timedelta(minutes=amount)
    else:
        due_at = datetime.now().astimezone() + timedelta(hours=amount)
    return due_at, reminder_text


def queue_reminder(text: str) -> str | None:
    parsed = parse_reminder_request(text)
    if not parsed:
        return None
    due_at, reminder_text = parsed
    try:
        reminders = json.loads(read_text(REMINDERS_FILE) or "[]")
        if not isinstance(reminders, list):
            reminders = []
    except Exception:
        reminders = []
    reminders.append(
        {
            "id": hashlib.sha256(f"{HUMAN_ID}|{due_at.isoformat()}|{reminder_text}".encode("utf-8")).hexdigest()[:16],
            "human_id": HUMAN_ID,
            "due_at": due_at.isoformat(timespec="seconds"),
            "text": reminder_text,
            "status": "pending",
            "created_at": iso_now(),
            "source": "telegram",
        }
    )
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(REMINDERS_FILE, json.dumps(reminders, indent=2))
    log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] REMINDER_QUEUED - Reminder due {due_at.isoformat(timespec='seconds')}")
    return f"Got it. I'll remind you in {format_relative_due(due_at)}."


def format_relative_due(due_at: datetime) -> str:
    seconds = max(1, int((due_at - datetime.now().astimezone()).total_seconds()))
    if seconds < 90:
        return f"{seconds} seconds"
    minutes = round(seconds / 60)
    if minutes < 90:
        return f"{minutes} minutes"
    hours = round(minutes / 60)
    return f"{hours} hours"


def help_text() -> str:
    return (
        f"Hello {OWNER_NAME}. I'm {BOT_NAME}.\n\n"
        "I bridge messages to the fast Chief_of_Staff chat service.\n\n"
        "Commands:\n"
        "/start\n"
        "/help\n"
        "/wake\n\n"
        "Any other message is sent directly to Chief_of_Staff."
    )


def handle_command(text: str) -> str | None:
    if text.startswith("/start") or text.startswith("/help"):
        return help_text()
    if text.startswith("/wake"):
        write_wake_message()
        return "Okay, I nudged the Chief_of_Staff."
    control_reply = maybe_handle_control_message(text)
    if control_reply:
        write_user_message(text)
        return control_reply
    reminder_reply = queue_reminder(text)
    if reminder_reply:
        write_user_message(text)
        return reminder_reply
    message = write_user_message(text)
    trigger_chief_chat(f"operator_message:{message.get('id', '')}:telegram")
    return None


def normalize_reply_text(text: str) -> str:
    lines: list[str] = []
    for raw in text.strip().splitlines():
        line = raw.rstrip()
        if line.strip() == "---":
            continue
        lines.append(line)
    return clean_operator_reply("\n".join(lines).strip())


def repair_mojibake(text: str) -> str:
    if not any(marker in text for marker in ("â", "ðŸ", "Ã")):
        return text
    try:
        repaired = text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if repaired.count("�") <= text.count("�") else text


def clean_legacy_reply_line(line: str) -> str:
    # Convert "[timestamp] [Chief_of_Staff] hello" into just "hello".
    # Human outbox files are operator-facing by definition, so bot aliases
    # should be stripped too.
    match = re.match(r"^\[[^\]]+\]\s+\[[^\]]+\]\s*(.*)$", line.strip())
    if match:
        return match.group(1).strip()
    return line.strip()


def extract_outbound_messages(content: str) -> list[str]:
    messages: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if not current:
            return
        text = normalize_reply_text("\n".join(current))
        current.clear()
        if text:
            messages.append(text)

    for raw in content.splitlines():
        line = raw.rstrip()
        if re.match(r"^\[[^\]]+\]\s+\[[^\]]+\]\s*", line.strip()):
            flush()
            cleaned = clean_legacy_reply_line(line)
            # Telegram should only emit operator-facing Chief_of_Staff replies.
            if cleaned != line.strip():
                current.append(cleaned)
            continue
        if current:
            current.append(line)
        elif line.strip() and not line.strip().startswith("#"):
            # Plain reply mode for harnesses that write only the clean body.
            current.append(line)

    flush()
    return messages


def extract_chief_replies(content: str) -> list[str]:
    messages: list[str] = []
    for raw in content.splitlines():
        line = raw.rstrip()
        if not re.match(r"^\[[^\]]+\]\s+\[Chief_of_Staff\]\s*", line.strip()):
            continue
        cleaned = clean_legacy_reply_line(line)
        text = normalize_reply_text(cleaned)
        if text:
            messages.append(text)
    return messages


def message_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def collect_outbound_messages() -> list[dict[str, str]]:
    return collect_telegram_feed(HARNESS_ROOT, HUMAN_ID)


def forward_new_outbound_messages() -> bool:
    with STATE_LOCK:
        seen = set(STATE.get("seen_human_message_hashes", []))
        changed = False
        sent_any = False
        for entry in collect_outbound_messages():
            text = entry.get("text", "").strip()
            if not text:
                continue
            digest = message_hash(f"{entry.get('timestamp', '')}|{entry.get('channel', '')}|{text}")
            if digest in seen:
                continue
            sent_to_anyone = False
            for user_id in ALLOWED_USER_IDS:
                sent_to_anyone = send(user_id, text) or sent_to_anyone
            if sent_to_anyone:
                seen.add(digest)
                changed = True
                sent_any = True
                log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] SEND - Forwarded Chief_of_Staff reply to Telegram")
            else:
                log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] ERROR - Could not forward reply to Telegram: {LAST_TELEGRAM_ERROR or 'unknown send failure'}")
        if changed:
            STATE["seen_human_message_hashes"] = list(seen)[-1000:]
            atomic_write_text(STATE_FILE, json.dumps(STATE, indent=2))
        return sent_any


def mark_existing_outbound_seen() -> None:
    with STATE_LOCK:
        seen = set(STATE.get("seen_human_message_hashes", []))
        for entry in collect_outbound_messages():
            text = entry.get("text", "").strip()
            if text:
                seen.add(message_hash(f"{entry.get('timestamp', '')}|{entry.get('channel', '')}|{text}"))
        STATE["seen_human_message_hashes"] = list(seen)[-1000:]
        atomic_write_text(STATE_FILE, json.dumps(STATE, indent=2))


def wait_for_chief_reply(chat_id: int | None = None) -> bool:
    if REPLY_WAIT_SECONDS <= 0:
        return False
    deadline = time.time() + REPLY_WAIT_SECONDS
    ack_deadline = time.time() + ACK_AFTER_SECONDS if ACK_AFTER_SECONDS else None
    ack_sent = False
    next_typing_at = 0.0
    while RUNNING and time.time() < deadline:
        if forward_new_outbound_messages():
            return True
        if chat_id and time.time() >= next_typing_at:
            send_typing(chat_id)
            next_typing_at = time.time() + TYPING_INTERVAL_SECONDS
        if chat_id and ack_deadline and not ack_sent and time.time() >= ack_deadline:
            send(chat_id, "I'm checking now.")
            ack_sent = True
        time.sleep(0.5)
    return False


def poll_human_replies() -> None:
    while RUNNING:
        update_runtime("active")
        forward_new_outbound_messages()
        time.sleep(POLL_INTERVAL)


def poll_updates() -> None:
    global RUNNING
    while RUNNING:
        update_runtime("active")
        response = tg("getUpdates", timeout=25, offset=STATE.get("last_update_id", 0) + 1)
        if not response.get("ok"):
            update_runtime("degraded", last_error="telegram_api_unavailable")
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
            send_typing(chat.get("id"))
            reply = handle_command(text)
            if reply:
                send(chat.get("id"), reply)
            elif not chief_chat_ready():
                send(chat.get("id"), chief_daemon_fallback_text())
            elif WAIT_FOR_REPLY_ON_MESSAGE:
                wait_for_chief_reply(chat.get("id"))
            save_state(STATE)


def shutdown(*_args) -> None:
    global RUNNING
    RUNNING = False
    save_state(STATE)
    update_runtime("stopped")
    release_single_instance_lock()
    sys.exit(0)


def main() -> None:
    ensure_dirs()
    acquire_single_instance_lock()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    print(f"Starting {BOT_NAME} for {HARNESS_ROOT}")
    me = tg("getMe")
    if not me.get("ok"):
        error = sanitize_error(me.get("description", LAST_TELEGRAM_ERROR or "getMe failed"))
        print(f"Telegram bot validation failed: {error}")
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] ERROR - Telegram bot validation failed: {error}")
        update_runtime("error", last_error=f"getMe failed: {error}")
        raise SystemExit(1)
    username = me.get("result", {}).get("username", BOT_NAME)
    print(f"Connected to Telegram bot @{username}")
    root_ok = validate_root()
    if not root_ok:
        print(f"Harness root not found or missing AGENTIC_HARNESS.md: {HARNESS_ROOT}")
        log_event(f"[{iso_now()}] [TELEGRAM_BRIDGE] ERROR - Invalid harness root: {HARNESS_ROOT}")
    if not CHIEF_FILE.exists():
        atomic_write_text(CHIEF_FILE, "")
    if not HUMAN_FILE.exists():
        atomic_write_text(HUMAN_FILE, "")
    mark_existing_outbound_seen()
    update_runtime("active")
    log_event(
        f"[{iso_now()}] [TELEGRAM_BRIDGE] START - Telegram bridge started for {BOT_NAME}. "
        f"Human file ready: {HUMAN_FILE.name}. Root valid: {'YES' if root_ok else 'NO'}."
    )
    threading.Thread(target=poll_human_replies, daemon=True).start()
    poll_updates()


if __name__ == "__main__":
    main()
