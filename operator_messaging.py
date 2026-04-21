#!/usr/bin/env python3
"""Shared operator chat routing for Telegram and Visualizer.

The operator should experience one clean conversation with Chief_of_Staff,
even when messages arrive from multiple transports. This module keeps the
transport-specific code thin and centralizes message IDs, channel targeting,
deduping inputs, and human-facing reply cleanup.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

from coordination_io import append_line, read_text
from message_filters import clean_operator_reply


DEFAULT_CHIEF_ROLE = "Chief_of_Staff"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def active_human_id(root: Path) -> str:
    text = read_text(root / "HUMANS.md")
    for line in text.splitlines():
        if line.startswith("ID:"):
            value = line.split(":", 1)[1].strip()
            if value:
                return value
    return "operator"


def message_id(timestamp: str, source: str, human_id: str, message: str) -> str:
    seed = f"{timestamp}|{source}|{human_id}|{message}".encode("utf-8", errors="replace")
    return hashlib.sha256(seed).hexdigest()[:12]


def append_operator_message(
    root: Path,
    message: str,
    *,
    source: str,
    human_id: str | None = None,
    role: str = DEFAULT_CHIEF_ROLE,
) -> dict[str, str]:
    clean = message.strip()
    if not clean:
        raise ValueError("Operator message cannot be empty.")
    resolved_human_id = human_id or active_human_id(root)
    timestamp = iso_now()
    msg_id = message_id(timestamp, source, resolved_human_id, clean)
    messages_dir = root / "_messages"
    append_line(
        messages_dir / f"{role}.md",
        f"[{timestamp}] [operator:{source}] [{resolved_human_id}] [msg:{msg_id}] {clean}",
    )
    append_line(root / "Runner" / "_wake_requests.md", f"[{timestamp}] {role}: operator_message:{msg_id}:{source}")
    append_line(
        root / "LAYER_LAST_ITEMS_DONE.md",
        f"[{timestamp}] [{source.upper()}_CHAT] NOTIFY - Operator message {msg_id} routed to {role}",
    )
    return {"id": msg_id, "timestamp": timestamp, "source": source, "human_id": resolved_human_id}


def append_operator_reply(
    root: Path,
    message: str,
    *,
    human_id: str | None = None,
    from_role: str = DEFAULT_CHIEF_ROLE,
    channel: str = "all",
    reply_to: str = "",
) -> dict[str, str]:
    clean = clean_operator_reply(message.strip())
    if not clean:
        raise ValueError("Reply cannot be empty after filtering.")
    resolved_human_id = human_id or active_human_id(root)
    timestamp = iso_now()
    msg_id = message_id(timestamp, channel, resolved_human_id, clean)
    tags = [f"[channel:{channel}]", f"[msg:{msg_id}]"]
    if reply_to:
        tags.append(f"[reply_to:{reply_to}]")
    append_line(
        root / "_messages" / f"human_{resolved_human_id}.md",
        f"[{timestamp}] [{from_role}] {' '.join(tags)} {clean}",
    )
    return {"id": msg_id, "timestamp": timestamp, "channel": channel, "human_id": resolved_human_id}


def _timestamp(line: str) -> str:
    match = re.match(r"^\[([^\]]+)\]", line.strip())
    return match.group(1).strip() if match else ""


def _strip_known_tags(text: str) -> tuple[str, dict[str, str]]:
    tags: dict[str, str] = {}
    rest = text.strip()
    while True:
        match = re.match(r"^\[([a-zA-Z_]+):([^\]]*)\]\s*(.*)$", rest)
        if not match:
            break
        tags[match.group(1).lower()] = match.group(2).strip()
        rest = match.group(3).strip()
    return rest, tags


def _parse_header_line(line: str) -> tuple[str, str, str] | None:
    match = re.match(r"^\[([^\]]+)\]\s+\[([^\]]+)\]\s*(.*)$", line.strip())
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()


def parse_operator_messages(content: str, human_id: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw in content.splitlines():
        parsed = _parse_header_line(raw)
        if not parsed:
            continue
        timestamp, actor, rest = parsed
        source = ""
        if actor.startswith("operator:"):
            source = actor.split(":", 1)[1].strip() or "unknown"
        elif actor in {"telegram", "visualizer", "desktop"}:
            source = actor
        if not source or f"[{human_id}]" not in rest:
            continue
        rest = rest.replace(f"[{human_id}]", "", 1).strip()
        text, tags = _strip_known_tags(rest)
        if text:
            items.append(
                {
                    "from": "operator",
                    "source": source,
                    "text": text,
                    "timestamp": timestamp,
                    "id": tags.get("msg", ""),
                    "channel": source,
                }
            )
    return items


def parse_reply_messages(content: str, *, default_channel: str = "all") -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: list[str] = []
    current_meta: dict[str, str] = {}

    def flush() -> None:
        if not current:
            return
        text = clean_operator_reply("\n".join(current).strip())
        if text:
            items.append({**current_meta, "text": text})
        current.clear()
        current_meta.clear()

    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parsed = _parse_header_line(line)
        if parsed:
            flush()
            timestamp, actor, rest = parsed
            text, tags = _strip_known_tags(rest)
            current_meta.update(
                {
                    "from": "chief",
                    "source": actor,
                    "timestamp": timestamp,
                    "channel": tags.get("channel", default_channel) or default_channel,
                    "id": tags.get("msg", ""),
                    "reply_to": tags.get("reply_to", ""),
                }
            )
            current.append(text)
            continue
        if current:
            current.append(line)
        elif line.strip():
            current_meta.update(
                {
                    "from": "chief",
                    "source": DEFAULT_CHIEF_ROLE,
                    "timestamp": "",
                    "channel": default_channel,
                    "id": "",
                    "reply_to": "",
                }
            )
            current.append(line)
    flush()
    return items


def collect_replies(root: Path, human_id: str, *, channels: Iterable[str] = ("all",)) -> list[dict[str, str]]:
    allowed = {channel.lower() for channel in channels}
    replies = parse_reply_messages(read_text(root / "_messages" / f"human_{human_id}.md"))
    chief_replies = [
        reply
        for reply in parse_reply_messages(read_text(root / "_messages" / f"{DEFAULT_CHIEF_ROLE}.md"))
        if reply.get("source") == DEFAULT_CHIEF_ROLE
    ]
    replies.extend(chief_replies)
    filtered: list[dict[str, str]] = []
    seen: set[str] = set()
    for reply in replies:
        channel = (reply.get("channel") or "all").lower()
        if channel != "all" and channel not in allowed:
            continue
        digest = hashlib.sha256(
            f"{reply.get('timestamp')}|{channel}|{reply.get('text')}".encode("utf-8", errors="replace")
        ).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        filtered.append(reply)
    filtered.sort(key=lambda item: item.get("timestamp", ""))
    return filtered


def collect_telegram_feed(root: Path, human_id: str) -> list[dict[str, str]]:
    """Return clean messages Telegram should display.

    Telegram already shows messages the operator typed inside Telegram, so this
    feed mirrors non-Telegram operator messages plus Chief replies. That makes
    Visualizer and Telegram feel like the same conversation without echoing the
    user's own Telegram input back at them.
    """

    inbox = read_text(root / "_messages" / f"{DEFAULT_CHIEF_ROLE}.md")
    items: list[dict[str, str]] = []
    for item in parse_operator_messages(inbox, human_id):
        if item.get("source") == "telegram":
            continue
        source = item.get("source", "visualizer").title()
        text = item.get("text", "").strip()
        if text:
            items.append({**item, "text": f"{source}: {text}", "channel": "telegram"})
    items.extend(collect_replies(root, human_id, channels=("all", "telegram")))
    items.sort(key=lambda item: item.get("timestamp", ""))
    return items


def collect_conversation(root: Path, human_id: str, *, limit: int = 40) -> list[dict[str, str]]:
    inbox = read_text(root / "_messages" / f"{DEFAULT_CHIEF_ROLE}.md")
    items = parse_operator_messages(inbox, human_id)
    items.extend(parse_reply_messages(read_text(root / "_messages" / f"human_{human_id}.md")))
    items.extend(
        reply
        for reply in parse_reply_messages(inbox)
        if reply.get("source") == DEFAULT_CHIEF_ROLE
    )
    items.sort(key=lambda item: item.get("timestamp", ""))
    return items[-limit:]
