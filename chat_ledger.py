#!/usr/bin/env python3
"""Canonical markdown chat ledger for operator/Chief conversations."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

from coordination_io import atomic_write_text, file_lock, read_text
from message_filters import clean_operator_reply


CHAT_RELATIVE = Path("_messages") / "CHAT.md"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def make_message_id(timestamp: str, direction: str, speaker: str, channel: str, body: str) -> str:
    seed = f"{timestamp}|{direction}|{speaker}|{channel}|{body}".encode("utf-8", errors="replace")
    return hashlib.sha256(seed).hexdigest()[:12]


def chat_path(root: Path) -> Path:
    return root / CHAT_RELATIVE


def append_chat_record(
    root: Path,
    *,
    direction: str,
    speaker: str,
    channel: str,
    body: str,
    human_id: str = "",
    reply_to: str = "",
    status: str = "new",
    message_id: str = "",
    timestamp: str = "",
) -> dict[str, str]:
    clean_body = body.strip()
    if not clean_body:
        raise ValueError("Chat body cannot be empty.")
    ts = timestamp or iso_now()
    msg_id = message_id or make_message_id(ts, direction, speaker, channel, clean_body)
    path = chat_path(root)
    block = (
        "## MESSAGE\n"
        f"ID: {msg_id}\n"
        f"Timestamp: {ts}\n"
        f"Direction: {direction}\n"
        f"Speaker: {speaker}\n"
        f"Human ID: {human_id}\n"
        f"Channel: {channel}\n"
        f"Reply To: {reply_to}\n"
        f"Status: {status}\n"
        "Body:\n"
        f"{clean_body}\n"
    )
    with file_lock(path):
        existing = read_text(path)
        prefix = "# CHAT\n\n" if not existing.strip() else "\n"
        atomic_write_text(path, existing.rstrip() + prefix + block + "\n")
    return {
        "id": msg_id,
        "timestamp": ts,
        "direction": direction,
        "speaker": speaker,
        "human_id": human_id,
        "channel": channel,
        "reply_to": reply_to,
        "status": status,
        "body": clean_body,
    }


def _parse_block(block: str) -> dict[str, str] | None:
    lines = block.splitlines()
    if not lines or lines[0].strip() != "## MESSAGE":
        return None
    record: dict[str, str] = {"body": ""}
    body_lines: list[str] = []
    in_body = False
    for raw in lines[1:]:
        if in_body:
            body_lines.append(raw)
            continue
        if raw.strip() == "Body:":
            in_body = True
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        record[key.strip().lower().replace(" ", "_")] = value.strip()
    record["body"] = "\n".join(body_lines).strip()
    if not record.get("id"):
        return None
    return record


def parse_chat_records(root: Path) -> list[dict[str, str]]:
    text = read_text(chat_path(root))
    if not text.strip():
        return []
    parts = re.split(r"(?=^## MESSAGE$)", text, flags=re.MULTILINE)
    records: list[dict[str, str]] = []
    for part in parts:
        parsed = _parse_block(part.strip())
        if parsed:
            records.append(parsed)
    return records


def update_chat_status(root: Path, message_id: str, status: str) -> bool:
    path = chat_path(root)
    with file_lock(path):
        text = read_text(path)
        if not text.strip():
            return False
        blocks = re.split(r"(?=^## MESSAGE$)", text, flags=re.MULTILINE)
        changed = False
        new_blocks: list[str] = []
        for block in blocks:
            if not block.strip():
                continue
            parsed = _parse_block(block.strip())
            if parsed and parsed.get("id") == message_id:
                block = re.sub(r"^Status:\s*.*$", f"Status: {status}", block, flags=re.MULTILINE)
                changed = True
            new_blocks.append(block.strip())
        if changed:
            atomic_write_text(path, "# CHAT\n\n" + "\n\n".join(new_blocks).strip() + "\n")
        return changed


def pending_operator_messages(root: Path) -> list[dict[str, str]]:
    return [
        record
        for record in parse_chat_records(root)
        if record.get("direction") == "operator_to_chief" and record.get("status", "new") == "new"
    ]


def chat_conversation(root: Path, human_id: str, *, limit: int = 40) -> list[dict[str, str]]:
    records = [
        record
        for record in parse_chat_records(root)
        if not record.get("human_id") or record.get("human_id") == human_id
    ]
    return records[-limit:]


def telegram_feed(root: Path, human_id: str, *, channels: Iterable[str] = ("telegram", "all")) -> list[dict[str, str]]:
    allowed = {channel.lower() for channel in channels}
    items: list[dict[str, str]] = []
    for record in parse_chat_records(root):
        channel = (record.get("channel") or "all").lower()
        direction = record.get("direction", "")
        if direction in {"chief_to_operator", "system_to_operator"}:
            if channel == "all" or channel in allowed:
                text = clean_operator_reply(record.get("body", ""))
                if text:
                    items.append({**record, "text": text})
            continue
        if direction == "operator_to_chief" and channel != "telegram":
            text = record.get("body", "").strip()
            if text:
                source = (channel or "operator").title()
                items.append({**record, "text": f"{source}: {text}", "channel": "telegram"})
    return items
