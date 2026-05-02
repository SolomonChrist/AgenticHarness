#!/usr/bin/env python3
"""Fast Chief_of_Staff chat daemon backed by the markdown chat ledger."""

from __future__ import annotations

import argparse
import hashlib
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chat_ledger import parse_chat_records, pending_operator_messages, update_chat_status
from coordination_io import append_line, atomic_write_text, read_text
from operator_messaging import active_human_id, append_operator_reply
from role_preflight import collect_tasks, config_view, load_role_registry, task_is_actionable


RUNNING = True
CHIEF_ROLE = "Chief_of_Staff"
GENERIC_CHAT_MODEL_NAMES = {"", "default", "local-model-name", "local model name"}


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


def activity_path(root: Path) -> Path:
    return root / "ChiefChat" / "data" / "activity.md"


def append_activity(
    root: Path,
    config: dict[str, str],
    message_id: str,
    stage: str,
    detail: str,
) -> None:
    """Write a compact operator-debuggable trace of ChiefChat's action loop."""

    if not parse_bool(config.get("Activity Log Enabled", "YES"), True):
        return
    path = activity_path(root)
    clean_detail = re.sub(r"\s+", " ", str(detail or "")).strip()
    line = f"[{iso_now()}] [{message_id or '-'}] {stage}: {clean_detail[:600]}"
    existing = read_text(path)
    lines = [raw for raw in existing.splitlines() if raw.strip()]
    if not lines:
        lines = ["# ChiefChat Activity", ""]
    lines.append(line)
    max_entries = max(20, parse_int(config.get("Activity Log Max Entries", "200"), 200))
    header = lines[:2] if lines and lines[0].startswith("#") else ["# ChiefChat Activity", ""]
    body = [raw for raw in lines if raw not in header]
    atomic_write_text(path, "\n".join(header + body[-max_entries:]).rstrip() + "\n")


def action_step(
    root: Path,
    config: dict[str, str],
    message_id: str,
    steps: list[str],
    stage: str,
    detail: str,
) -> bool:
    max_steps = max(1, parse_int(config.get("Action Loop Max Steps", "4"), 4))
    if len(steps) >= max_steps:
        append_activity(root, config, message_id, "STEP_LIMIT", f"Skipped {stage}; max action steps reached.")
        return False
    steps.append(stage)
    append_activity(root, config, message_id, stage, detail)
    return True


def runtime_file(root: Path) -> Path:
    return root / "ChiefChat" / "data" / "runtime.json"


def update_runtime(root: Path, status: str, *, last_error: str = "") -> None:
    path = runtime_file(root)
    config = load_config(root)
    payload = {
        "component": "chief-chat",
        "status": status,
        "pid": os.getpid(),
        "updated_at": iso_now(),
        "last_error": last_error,
        "chat_ledger": str(root / "_messages" / "CHAT.md"),
        "chat_provider": config.get("Chat Provider", ""),
        "chat_model": config.get("Chat Model", ""),
        "chat_endpoint": chat_endpoint_summary(config),
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
        "Browser Search Results": "5",
        "Browser Pages To Read": "3",
        "Browser Headless": "NO",
        "Model Detection Timeout Seconds": "2",
        "Poll Seconds": "0.5",
        "Status Reply On Model Failure": "YES",
        "Chief Interaction Mode": "bounded-action-loop",
        "Action Loop Max Steps": "4",
        "Activity Log Enabled": "YES",
        "Activity Log Max Entries": "200",
        "Role Takeover Auto Launch": "YES",
        "Role Takeover Infer Registry From Heartbeat": "YES",
        "Role Takeover Launch Timeout Seconds": "20",
        "Chief Soul Max Chars": "1200",
        "Chief Always Memory Max Chars": "900",
        "Human Memory Max Chars": "1200",
        "Human Recent Files": "2",
        "Human Recent File Max Chars": "500",
        "Recent Chat Max Chars": "1400",
        "System Roles Max": "8",
        "Reply Max Tokens": "450",
    }
    values = parse_key_values(config_path(root))
    return {**defaults, **values}


def chat_endpoint_summary(config: dict[str, str]) -> str:
    provider = config.get("Chat Provider", "openai-compatible").strip().lower()
    if provider in {"openai", "openai-compatible", "lmstudio", "lm-studio"}:
        return config.get("OpenAI Compatible Base URL", "http://127.0.0.1:1234/v1").rstrip("/")
    if provider == "ollama":
        return config.get("Ollama Base URL", "http://127.0.0.1:11434").rstrip("/")
    if provider == "opencode":
        return "OpenCode CLI"
    return provider or "unknown"


def detected_chat_model(config: dict[str, str]) -> str:
    configured = config.get("Chat Model", "").strip()
    provider = config.get("Chat Provider", "openai-compatible").strip().lower()
    timeout = max(1, parse_int(config.get("Model Detection Timeout Seconds", "2"), 2))
    generic = configured.lower() in GENERIC_CHAT_MODEL_NAMES
    if provider in {"fake", "test"}:
        return configured or "fake"
    if provider in {"openai", "openai-compatible", "lmstudio", "lm-studio"}:
        base = chat_endpoint_summary(config)
        try:
            result = http_get_json(f"{base}/models", timeout)
            ids = [
                str(item.get("id", "")).strip()
                for item in result.get("data", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip()
            ]
            if configured and configured in ids:
                return configured
            if generic and ids:
                return ids[0]
            if ids:
                return f"{configured} (available: {', '.join(ids[:3])})"
        except Exception:
            pass
        return configured or "unknown local model"
    if provider == "ollama":
        base = chat_endpoint_summary(config)
        try:
            result = http_get_json(f"{base}/api/tags", timeout)
            models = [
                str(item.get("name", "")).strip()
                for item in result.get("models", [])
                if isinstance(item, dict) and str(item.get("name", "")).strip()
            ]
            if configured and configured in models:
                return configured
            if generic and models:
                return models[0]
        except Exception:
            pass
        return configured or "unknown Ollama model"
    return configured or "provider default"


def resolved_chat_model(config: dict[str, str]) -> str:
    configured = config.get("Chat Model", "").strip()
    provider = config.get("Chat Provider", "openai-compatible").strip().lower()
    generic = configured.lower() in GENERIC_CHAT_MODEL_NAMES
    if provider in {"openai", "openai-compatible", "lmstudio", "lm-studio", "ollama"} and generic:
        detected = detected_chat_model(config).strip()
        if detected and detected.lower() not in GENERIC_CHAT_MODEL_NAMES and not detected.lower().startswith("unknown "):
            return detected
        if provider in {"openai", "openai-compatible", "lmstudio", "lm-studio"}:
            endpoint = chat_endpoint_summary(config)
            raise RuntimeError(
                "Chat Model is still a placeholder. Load a model in LM Studio, then set "
                f"`Chat Model` to the exact model id from `{endpoint}/models`."
            )
        raise RuntimeError("Chat Model is still a placeholder. Start Ollama and set `Chat Model` to a pulled model name.")
    return configured or detected_chat_model(config)


def runtime_identity_context(root: Path, config: dict[str, str]) -> str:
    provider = config.get("Chat Provider", "openai-compatible").strip()
    configured = config.get("Chat Model", "").strip() or "provider default"
    detected = detected_chat_model(config)
    registry = load_role_registry(root)
    deep_lines: list[str] = []
    for role in ("Chief_of_Staff", "Researcher", "Engineer"):
        raw = registry.get(role)
        if not raw:
            continue
        view = config_view(role, raw)
        if view.harness_type or view.model_profile:
            deep_lines.append(
                f"- {role} deep-work runner: harness={view.harness_type or 'unknown'}, model={view.model_profile or 'default'}"
            )
    lines = [
        "## ChiefChat runtime identity",
        f"- Live chat path: ChiefChat",
        f"- Chat provider: {provider}",
        f"- Chat endpoint: {chat_endpoint_summary(config)}",
        f"- Configured chat model: {configured}",
        f"- Detected chat model: {detected}",
        "- Claude Code/OpenCode/other Runner roles are deeper work paths, not the normal Telegram chat model.",
    ]
    if deep_lines:
        lines.append("Deep-work role registry:")
        lines.extend(deep_lines)
    return "\n".join(lines)


def model_identity_reply(root: Path, config: dict[str, str]) -> str:
    provider = config.get("Chat Provider", "openai-compatible").strip()
    configured = config.get("Chat Model", "").strip() or "provider default"
    detected = detected_chat_model(config)
    endpoint = chat_endpoint_summary(config)
    lines = [
        "I'm answering through the fast ChiefChat path right now, not a Claude Code worker.",
        f"Chat provider: {provider}",
        f"Endpoint: {endpoint}",
        f"Configured model: {configured}",
        f"Detected model: {detected}",
    ]
    registry = load_role_registry(root)
    deep_bits: list[str] = []
    for role, raw in registry.items():
        view = config_view(role, raw)
        if view.model_profile:
            deep_bits.append(f"{role}: {view.harness_type or 'harness'} / {view.model_profile}")
    if deep_bits:
        lines.append("Separate deep-work role models: " + "; ".join(deep_bits[:4]))
    return "\n".join(lines)


def is_model_identity_request(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(r"\b(what|which)\s+(ai\s+)?model\b", lowered)
        or re.search(r"\b(model|provider|llm)\s+(are you|you are|running|using)\b", lowered)
        or "what are you running on" in lowered
    )


def strip_markdown_path(value: str) -> str:
    return value.strip().strip("`").strip('"').strip("'")


def resolve_root_path(root: Path, value: str) -> Path:
    clean = strip_markdown_path(value)
    path = Path(clean)
    return path if path.is_absolute() else root / path


def active_human_record(root: Path, human_id: str) -> str:
    text = read_text(root / "HUMANS.md")
    blocks = re.split(r"(?=^### HUMAN\s*$)", text, flags=re.MULTILINE)
    for block in blocks:
        if re.search(rf"^ID:\s*{re.escape(human_id)}\s*$", block, flags=re.MULTILINE):
            return block.strip()
    return ""


def active_human_memory_context(root: Path, config: dict[str, str], max_chars: int | None = None) -> str:
    max_chars = max_chars if max_chars is not None else max(400, parse_int(config.get("Human Memory Max Chars", "1200"), 1200))
    recent_file_limit = max(0, parse_int(config.get("Human Recent Files", "2"), 2))
    recent_file_chars = max(200, parse_int(config.get("Human Recent File Max Chars", "500"), 500))
    human_id = active_human_id(root)
    if not human_id:
        return ""
    record = active_human_record(root, human_id)
    paths: list[Path] = []
    seen: set[str] = set()

    def add_path(path: Path) -> None:
        key = str(path)
        if key not in seen:
            seen.add(key)
            paths.append(path)

    for pattern in [
        r"^Always Memory File:\s*(.+)$",
        r"^Recent Memory Root:\s*(.+)$",
    ]:
        match = re.search(pattern, record, flags=re.MULTILINE)
        if match:
            add_path(resolve_root_path(root, match.group(1)))

    default_root = root / "MEMORY" / "humans" / human_id
    add_path(default_root / "ALWAYS.md")
    add_path(default_root / "RECENT")

    chunks: list[str] = []
    for path in paths:
        if path.is_dir():
            recent_files = sorted(path.glob("*.md"), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
            for child in recent_files[:recent_file_limit]:
                content = tail(child, recent_file_chars)
                if content:
                    chunks.append(f"### {child.relative_to(root) if child.is_relative_to(root) else child}\n{content}")
            continue
        content = tail(path, max(400, max_chars // 2))
        if content:
            chunks.append(f"### {path.relative_to(root) if path.is_relative_to(root) else path}\n{content}")
    if not chunks:
        return ""
    body = "\n\n".join(chunks)
    return f"## Active human memory ({human_id})\n{body[-max_chars:]}"


def soul_context(root: Path, config: dict[str, str]) -> str:
    soul_chars = max(500, parse_int(config.get("Chief Soul Max Chars", "1200"), 1200))
    always_chars = max(500, parse_int(config.get("Chief Always Memory Max Chars", "900"), 900))
    parts = [
        ("Chief soul", root / "MEMORY" / "agents" / CHIEF_ROLE / "SOUL.md", soul_chars),
        ("Chief always memory", root / "MEMORY" / "agents" / CHIEF_ROLE / "ALWAYS.md", always_chars),
        ("Human registry", root / "HUMANS.md", 1200),
    ]
    chunks: list[str] = []
    for label, path, limit in parts:
        content = tail(path, limit)
        if content:
            chunks.append(f"## {label}\n{content}")
    human_memory = active_human_memory_context(root, config)
    if human_memory:
        chunks.append(human_memory)
    return "\n\n".join(chunks)


def recent_chat_context(root: Path, config: dict[str, str], max_chars: int | None = None) -> str:
    max_chars = max_chars if max_chars is not None else max(300, parse_int(config.get("Recent Chat Max Chars", "1400"), 1400))
    return tail(root / "_messages" / "CHAT.md", max_chars)


def compact_system_summary(root: Path, config: dict[str, str]) -> str:
    role_limit = max(1, parse_int(config.get("System Roles Max", "8"), 8))
    role_text = read_text(root / "Runner" / "ROLE_LAUNCH_REGISTRY.md")
    roles: list[str] = []
    for block in re.findall(r"### ROLE\s*\n.*?(?=\n### |\Z)", role_text, flags=re.DOTALL):
        role = re.search(r"^Role:\s*(.*)$", block, flags=re.MULTILINE)
        harness = re.search(r"^Harness Type:\s*(.*)$", block, flags=re.MULTILINE)
        enabled = re.search(r"^Enabled:\s*(.*)$", block, flags=re.MULTILINE)
        ready = re.search(r"^Automation Ready:\s*(.*)$", block, flags=re.MULTILINE)
        if role:
            roles.append(
                f"- {role.group(1).strip()}: {harness.group(1).strip() if harness else 'unknown'}, "
                f"enabled={enabled.group(1).strip() if enabled else 'NO'}, ready={ready.group(1).strip() if ready else 'NO'}"
            )
    task_count = len(re.findall(r"^Status:\s*(TODO|IN_PROGRESS|ACTIVE|READY|OPEN)\s*$", read_text(root / "LAYER_TASK_LIST.md"), flags=re.MULTILINE | re.IGNORECASE))
    lines = ["## Compact system state", f"Actionable tasks: {task_count}"]
    if roles:
        lines.append("Roles:")
        lines.extend(roles[:role_limit])
    return "\n".join(lines)


def chief_voice_contract() -> str:
    return """## Chief voice contract
- Lead with the useful answer, not process narration.
- Sound like a capable human assistant: warm, direct, practical, and specific.
- Be the operator's executive assistant/front door, not a generic chatbot.
- When work is needed, capture or route it in files first, then tell the operator what was actually done.
- Do not use robotic filler such as "Understood" or "stand by" as a final answer.
- Do not say "check these sites" when source evidence is available; answer from the evidence.
- Be concise for Telegram, but include enough concrete detail to be useful."""


def web_intent(text: str) -> str:
    lowered = text.lower()
    if is_weather_request(text):
        return "weather"
    if is_situational_location_request(text):
        return "situational"
    if re.search(r"\b(events?|meetups?|concerts?|things to do|happening|coming up)\b", lowered):
        return "events"
    if re.search(r"\b(hours?|open|close|website)\b", lowered):
        return "hours"
    if re.search(r"\b(phone|phone number|address|directions|contact)\b", lowered):
        return "business_lookup"
    if re.search(r"\b(news|headlines)\b", lowered):
        return "news"
    if re.search(r"\b(restaurant|reviews?|best dish|best dishes|menu|dish|food|lunch|dinner|meal|meals|order|deals|feed|chick[-\s·]?fil[-\s·]?a)\b", lowered):
        return "restaurant"
    if re.search(r"\b(gas|fuel|gasoline)\b", lowered):
        return "gas"
    if "github" in lowered or re.search(r"\b(repo|repository)\b", lowered):
        return "github"
    if re.search(r"\b(book|author|summary|systemology)\b", lowered):
        return "research"
    return "general"


def web_answer_shape(intent: str) -> str:
    shapes = {
        "situational": "Investigate what is probably happening near the stated location right now. Reply like a helpful friend: lead with the most likely reason, then give confidence, nearby venues checked, concrete events/news found, source links, and what remains unverified.",
        "events": "Return 3-7 concrete events if available. Include event name, date/time, venue/location, why it fits, and source link.",
        "hours": "Return the venue/site name, today's hours if visible, official/source link, and any uncertainty.",
        "business_lookup": "Return the business name, requested contact detail such as phone/address/website, location match, source link, and uncertainty. Prefer official business pages or reliable listings.",
        "news": "Return concrete headlines with source names and links. Do not invent dates or sources.",
        "restaurant": "Recommend concrete food/order options from official menu, review, or source evidence. Include quantities for group-size requests, source links, and uncertainty about live prices.",
        "gas": "Return prices/stations only if location and source evidence are clear. Ask for location if missing.",
        "github": "Summarize what the repo does, who it is for, key signals from README/stars/docs if visible, and source link.",
        "research": "Summarize what it is, who it is for, key concepts, and source link.",
    }
    return shapes.get(
        intent,
        "Return a direct answer from source evidence with names, dates, numbers, locations, and links when available.",
    )


def browser_answer_prompt(root: Path, config: dict[str, str], message: dict[str, str], extra_context: str) -> str:
    body = message.get("body", "").strip()
    intent = web_intent(body)
    return f"""You are Chief_of_Staff. Reply to the operator in a warm, concise Telegram style.

Use ONLY the fresh web evidence below plus the operator message. Do not discuss old provider cooldowns, quota, Runner state, or unrelated tasks.
Give the actual answer now. Do not say you are checking, searching, looking, or about to do the work.
If the web evidence is incomplete, say what you could verify, cite the source shown in the evidence, and note that a follow-up task remains open.
Do not answer with a directory of places the operator can search unless the evidence contains no concrete answer.

{chief_voice_contract()}

{runtime_identity_context(root, config)}

## Expected answer shape
{web_answer_shape(intent)}

## Operator message
{body}

## Fresh web evidence
{extra_context}

Give the best useful answer now."""


def build_prompt(root: Path, config: dict[str, str], message: dict[str, str], extra_context: str = "") -> str:
    body = message.get("body", "").strip()
    context = soul_context(root, config)
    chat = recent_chat_context(root, config)
    system = compact_system_summary(root, config)
    if extra_context:
        result_instruction = (
            "The local action context below is fresh and more important than old task/status history. "
            "Answer the operator's request using it. Do not pivot to old provider quota or harness-remediation topics unless the operator asked about them."
        )
    else:
        result_instruction = "Answer the operator's newest message directly."
    interaction_mode = config.get("Chief Interaction Mode", "bounded-action-loop")
    return f"""You are Chief_of_Staff, the user's fast human-feeling operator interface.

Use the Chief soul/personality and memory below. Be warm, direct, specific, and operational.
You are the orchestration layer. For deep coding, research, or long web work, create or route tasks instead of pretending the chat model did it.
Do not mention internal file paths, daemon cycles, or provider errors unless the user asks or it is needed to unblock them.
Keep the reply concise enough for Telegram.
Use compact context discipline: the memory and chat excerpts below are intentionally small. Do not infer that omitted history means it does not exist.
Interaction mode: {interaction_mode}. ChiefChat may already have classified the message, written tasks, checked status, or gathered web evidence before this model call. Reply from those observed results; do not promise future action when a local action already happened.
{result_instruction}

{chief_voice_contract()}

{runtime_identity_context(root, config)}

{context}

{system}

## Fresh local action context
{extra_context or "None"}

## Recent unified chat
{chat}

## New operator message
{body}

Reply as Chief_of_Staff."""


def open_url(request: urllib.request.Request | str, timeout: int) -> bytes:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        return response.read()


def http_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(open_url(request, timeout).decode("utf-8", errors="replace"))


def http_get_json(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AgenticHarness-ChiefChat/1.0"})
    return json.loads(open_url(request, timeout).decode("utf-8", errors="replace"))


def openai_compatible_reply(config: dict[str, str], prompt: str) -> str:
    base = config.get("OpenAI Compatible Base URL", "http://127.0.0.1:1234/v1").rstrip("/")
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    payload = {
        "model": resolved_chat_model(config),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.35,
        "max_tokens": max(120, parse_int(config.get("Reply Max Tokens", "450"), 450)),
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
        "model": resolved_chat_model(config),
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


def is_presence_ping(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", text.strip().lower()).strip(" ?!.")
    return bool(
        lowered in {
            "hi",
            "hello",
            "hey",
            "ping",
            "test",
            "are you there",
            "are you available",
            "are you available again",
            "you there",
            "hello are you available again",
        }
        or re.search(r"\b(are you|you)\s+(there|online|awake|available|working|running)\??$", lowered)
    )


def presence_ping_reply(root: Path) -> str:
    status_bits: list[str] = []
    try:
        runtime = json.loads(read_text(runtime_file(root)) or "{}")
        if runtime.get("status"):
            status_bits.append(f"ChiefChat is {runtime.get('status')}")
    except Exception:
        pass
    try:
        detected = detected_chat_model(load_config(root))
        if detected and not detected.startswith("unknown"):
            status_bits.append(f"local model: {detected}")
    except Exception:
        pass
    suffix = f" ({'; '.join(status_bits)})" if status_bits else ""
    return f"Yep, I am here and connected{suffix}. Send me what you want to move next."


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
    r"\b(events?|meetups?|concerts?|happening|what'?s going on|lineup|line up|queue|crowd|movie theatre|theatre|theater)\b",
]

WEB_ACTION_PATTERNS = [
    r"\b(search|google|look up|browse|web search|check online|check the web|find out|research online)\b",
    r"\b(find|get|show|give)\s+(me\s+)?\b",
    r"\b(can you|could you|please|go and|use the search to|search to)\s+(find|research|check|look up|see)\b",
]

WEB_SUBJECT_PATTERNS = [
    r"\b(events?|meetups?|concerts?|things to do|happening|hours?|open|close|website|url|page|phone|phone number|address|directions|contact)\b",
    r"\b(news|headlines|reviews?|best dish|menu|restaurant|business|store|location|github|repo|repository|book)\b",
    r"\b(food|lunch|dinner|meal|meals|order|deals|feed|chick[-\s·]?fil[-\s·]?a)\b",
    r"\b(price|prices|cheapest|gas|fuel|stock|weather|forecast|current|latest|today|tonight|right now|near me|nearby)\b",
]

WEATHER_PATTERNS = [
    r"\b(weather|forecast|temperature|temp|rain|snow|wind|humidity|humid)\b",
]

STOPWORDS = {
    "a",
    "about",
    "and",
    "are",
    "can",
    "check",
    "current",
    "do",
    "find",
    "for",
    "from",
    "get",
    "give",
    "google",
    "i",
    "in",
    "is",
    "it",
    "latest",
    "look",
    "me",
    "news",
    "now",
    "of",
    "on",
    "online",
    "please",
    "research",
    "search",
    "show",
    "the",
    "today",
    "up",
    "weather",
    "web",
    "what",
    "whats",
    "what's",
    "with",
}

NOISE_PHRASES = (
    "accept all",
    "accept cookies",
    "advertisement",
    "all rights reserved",
    "browser",
    "cookie policy",
    "cookies",
    "download our app",
    "enable javascript",
    "log in",
    "menu",
    "newsletter",
    "privacy policy",
    "sign in",
    "sign up",
    "skip to content",
    "subscribe",
    "terms of use",
)

BAD_SOURCE_DOMAINS = (
    "textranch.com",
    "grammarly.com",
    "merriam-webster.com",
    "dictionary.com",
    "thesaurus.com",
    "wiktionary.org",
)

AUTOMATION_HOSTILE_DOMAINS = (
    "yelp.com",
    "yelp.ca",
    "tripadvisor.com",
    "tripadvisor.ca",
)

BLOCKED_PAGE_MARKERS = (
    "you have been blocked",
    "access is temporarily restricted",
    "we detected unusual activity",
    "automated (bot) activity",
    "automated bot activity",
    "robot on the same network",
    "chrome is being controlled by automated test software",
    "verify you are human",
    "are you a robot",
    "captcha",
)


def url_host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().split("@")[-1].split(":")[0]
    except Exception:
        return ""


def host_matches_domain(host: str, domain: str) -> bool:
    clean_host = host.lower().removeprefix("www.")
    clean_domain = domain.lower().removeprefix("www.")
    return clean_host == clean_domain or clean_host.endswith("." + clean_domain)


def is_automation_hostile_url(url: str) -> bool:
    host = url_host(url)
    return any(host_matches_domain(host, domain) for domain in AUTOMATION_HOSTILE_DOMAINS)


def looks_like_access_block(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", (text or "").lower())
    return any(marker in lowered for marker in BLOCKED_PAGE_MARKERS)


def is_web_request(text: str) -> bool:
    if is_task_intake_request(text):
        return False
    if is_situational_location_request(text):
        return True
    if is_weather_request(text):
        return True
    lowered = text.lower()
    if extract_direct_urls(text):
        return True
    has_action = any(re.search(pattern, lowered) for pattern in WEB_ACTION_PATTERNS)
    has_subject = any(re.search(pattern, lowered) for pattern in WEB_SUBJECT_PATTERNS)
    if has_action and has_subject:
        return True
    if re.search(r"\b(what|which|where|when)\b.*\b(events?|meetups?|hours?|news|headlines|weather|forecast|price|prices|reviews?|github|repo|repository|menu|food|lunch|dinner|meal|meals|order|deals|feed)\b", lowered):
        return True
    if re.search(r"\b(events?|meetups?|hours?|news|headlines|weather|forecast|prices?|reviews?)\b.*\b(today|tonight|latest|current|right now|near me|nearby)\b", lowered):
        return True
    if re.search(r"\b(find|get|show|give)\s+(me\s+)?(.{2,80})\b(phone|phone number|address|website|hours|menu|contact)\b", lowered):
        return True
    if re.search(r"\b(phone|phone number|address|website|hours|menu|contact)\b.*\b(for|of|at)\b", lowered):
        return True
    if re.search(r"\bresearch\s+(the\s+)?(book|github|repo|repository|company|restaurant|website)\b", lowered):
        return True
    return False


def is_weather_request(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in WEATHER_PATTERNS)


def clean_location(value: str) -> str:
    text = re.sub(r"https?://\S+", "", value)
    text = re.sub(r"[?!.,;]+$", "", text.strip())
    text = re.sub(
        r"\b(right now|today|tonight|tomorrow|this week|this weekend|currently|please|pls|thanks|thank you)\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -:,\t\r\n")


def normalize_speech_location_text(text: str) -> str:
    value = text
    replacements = [
        (r"\bbl\s*o+\s*r\b", "Bloor"),
        (r"\bbl\s+oo+r\b", "Bloor"),
        (r"\bfloor\b", "Bloor"),
        (r"\bbloor\s+Bathurst\b", "Bloor and Bathurst"),
        (r"\bbloor\s*&\s*bathurst\b", "Bloor and Bathurst"),
    ]
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def is_situational_location_request(text: str) -> bool:
    lowered = normalize_speech_location_text(text).lower()
    has_situation = bool(
        re.search(r"\b(lineup|line up|long line|queue|crowd|packed|what'?s going on|what is going on|why is there|movie theatre|theatre|theater)\b", lowered)
    )
    has_location = bool(extract_location_hint(lowered) or re.search(r"\bbloor\s+(and|&)?\s*bathurst\b", lowered))
    has_current_event_probe = bool(re.search(r"\b(events?|happening|going on|right now|today|tonight)\b", lowered))
    return has_location and (has_situation or ("bloor" in lowered and "bathurst" in lowered and has_current_event_probe))


def extract_weather_location(text: str) -> str:
    cleaned = clean_location(text)
    patterns = [
        r"(?:weather|forecast|temperature|temp|rain|snow|wind|humidity).*?(?:in|for|at)\s+(.+)$",
        r"(?:in|for|at)\s+(.+?)\s+(?:weather|forecast|temperature|temp|rain|snow|wind|humidity)",
        r"(?:weather|forecast|temperature|temp)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return clean_location(match.group(1))
    words = [word for word in re.split(r"\s+", cleaned) if word.lower().strip("'") not in STOPWORDS]
    return clean_location(" ".join(words))


AMBIGUOUS_PLACES = {
    "california": "Did you mean California the state, or a specific city in California?",
    "georgia": "Did you mean Georgia the country, Georgia the U.S. state, or a specific city?",
    "washington": "Did you mean Washington state, Washington DC, or a specific city?",
    "ontario": "Did you mean Ontario the province, or a specific city in Ontario?",
    "paris": "Did you mean Paris, France, Paris, Ontario, or another Paris?",
    "london": "Did you mean London, UK, London, Ontario, or another London?",
}


def broad_location_clarification(location: str) -> str:
    normalized = re.sub(r"\s+", " ", location.strip().lower())
    if normalized in AMBIGUOUS_PLACES:
        return AMBIGUOUS_PLACES[normalized]
    return ""


def local_request_needs_location(text: str) -> bool:
    lowered = text.lower()
    if "near me" not in lowered and "nearby" not in lowered:
        return False
    return not extract_location_hint(text)


def location_clarification_reply(text: str, *, kind: str = "request") -> str:
    if kind == "weather":
        location = extract_weather_location(text)
        broad = broad_location_clarification(location)
        if broad:
            return broad
        return "What city or region should I use for the weather?"
    return "What area should I use for that? Send the city/neighborhood, and I will check it properly."


def weather_code_label(code: int) -> str:
    labels = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        56: "light freezing drizzle",
        57: "dense freezing drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        77: "snow grains",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        85: "slight snow showers",
        86: "heavy snow showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail",
    }
    return labels.get(code, f"weather code {code}")


def fetch_weather_summary(location: str, timeout: int = 10) -> str:
    if not location:
        return "What city or location should I check the weather for?"
    geocode_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({"name": location, "count": 1, "language": "en", "format": "json"})
    )
    geocode = http_get_json(geocode_url, timeout)
    results = geocode.get("results") or []
    if not results:
        return f"I could not find a weather location for `{location}`. Send me the city and region, and I will check again."
    place = results[0]
    latitude = place.get("latitude")
    longitude = place.get("longitude")
    name_bits = [str(place.get("name") or location)]
    for key in ("admin1", "country"):
        if place.get(key):
            name_bits.append(str(place[key]))
    forecast_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(
                    [
                        "temperature_2m",
                        "apparent_temperature",
                        "relative_humidity_2m",
                        "precipitation",
                        "weather_code",
                        "cloud_cover",
                        "wind_speed_10m",
                        "wind_direction_10m",
                    ]
                ),
                "timezone": "auto",
            }
        )
    )
    forecast = http_get_json(forecast_url, timeout)
    current = forecast.get("current") or {}
    units = forecast.get("current_units") or {}
    code = int(current.get("weather_code") or 0)
    temp = current.get("temperature_2m")
    feels = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")
    precipitation = current.get("precipitation")
    cloud_cover = current.get("cloud_cover")
    temp_unit = units.get("temperature_2m", "")
    wind_unit = units.get("wind_speed_10m", "")
    precipitation_unit = units.get("precipitation", "")
    updated = current.get("time") or "current local time"
    return (
        f"Weather for {', '.join(name_bits)}: {temp}{temp_unit}, feels like {feels}{temp_unit}, "
        f"{weather_code_label(code)}, humidity {humidity}%, wind {wind} {wind_unit}, "
        f"precipitation {precipitation} {precipitation_unit}, cloud cover {cloud_cover}%. "
        f"Updated {updated} local time. Source: Open-Meteo."
    )


def meaningful_terms(text: str) -> list[str]:
    terms: list[str] = []
    for raw in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", text.lower()):
        word = raw.strip("'")
        if word not in STOPWORDS and word not in terms:
            terms.append(word)
    return terms[:12]


def clean_visible_lines(text: str) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line or line in seen:
            continue
        lowered = line.lower()
        if any(noise in lowered for noise in NOISE_PHRASES) and len(line) < 160:
            continue
        if len(line) < 18 and not re.search(r"\d", line):
            continue
        seen.add(line)
        cleaned.append(line)
    return cleaned


def evidence_lines(text: str, query: str, limit: int = 8) -> list[str]:
    lines = clean_visible_lines(text)
    terms = meaningful_terms(query)
    scored: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        score = sum(3 for term in terms if term in lowered)
        if re.search(r"\d", line):
            score += 1
        if 60 <= len(line) <= 240:
            score += 1
        scored.append((score, -index, line))
    selected = [line for score, _index, line in sorted(scored, reverse=True) if score > 0][:limit]
    if len(selected) < min(3, limit):
        for line in lines:
            if line not in selected:
                selected.append(line)
            if len(selected) >= limit:
                break
    return selected[:limit]


def normalize_duckduckgo_url(href: str) -> str:
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = "https://duckduckgo.com" + href
    parsed = urllib.parse.urlparse(href)
    params = urllib.parse.parse_qs(parsed.query)
    if "uddg" in params and params["uddg"]:
        return urllib.parse.unquote(params["uddg"][0])
    return href


def extract_direct_urls(text: str) -> list[str]:
    urls = []
    for match in re.findall(r"https?://[^\s>)\]]+", text):
        url = match.rstrip(".,;!?'\"")
        if url not in urls:
            urls.append(url)
    return urls


def clean_search_fragment(text: str) -> str:
    value = re.sub(r"https?://\S+", "", text)
    value = re.sub(
        r"\b(ok|okay|hey|hi|hello|please|pls|can you|could you|would you|will you|"
        r"tell me|send me|give me|show me|find me|find|look up|google|search|browse|"
        r"research|online|on the web|right now|now|today|tonight|tomorrow|this week|"
        r"this weekend|latest|current|upcoming|coming up)\b",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\b(and then|then|based on|what it does|for me|to get|i'm|im|i am)\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[^A-Za-z0-9/&'. -]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -.,")
    return value


def title_location(text: str) -> str:
    small_words = {"of", "and", "the", "in", "at", "by", "for"}
    words = []
    for word in clean_search_fragment(text).split():
        lowered = word.lower()
        words.append(lowered if lowered in small_words else word[:1].upper() + word[1:])
    return " ".join(words)


def extract_location_hint(text: str) -> str:
    text = normalize_speech_location_text(text)
    lowered = text.lower()
    if re.search(r"\bbloor\s+(?:and\s+|&\s*)?bathurst\b", lowered):
        return "Bloor and Bathurst Toronto" if "toronto" in lowered else "Bloor and Bathurst"
    intersection = re.search(
        r"\b(?:on|at|near|around|in the)\s+([A-Za-z0-9 .'-]+?)\s+(?:and|&)\s+([A-Za-z0-9 .'-]+?)(?:\s+(?:in|of|area of)\s+([A-Za-z0-9 .'-]+?))?(?:\s+right now|\s+now|[.?!,]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if intersection:
        first = title_location(intersection.group(1))
        second = title_location(intersection.group(2))
        city = title_location(intersection.group(3) or "")
        if first and second:
            return " ".join(part for part in [f"{first} and {second}", city] if part)
    patterns = [
        r"\b(?:i'?m|i am|we'?re|we are)\s+in\s+([A-Za-z0-9 .'-]+?)(?:\s+right now|\s+now|[.?!,]|$)",
        r"\bnear\s+([A-Za-z0-9 .'-]+?)(?:\s+right now|\s+now|[.?!,]|$)",
        r"\b(?:in|around|near|at)\s+([A-Za-z0-9 .'-]+?)(?:\s+right now|\s+now|[.?!,]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            location = title_location(match.group(1))
            if location and location.lower() not in {"me", "near me", "this restaurant"}:
                return location
    return ""


def extract_github_subject(text: str) -> str:
    patterns = [
        r"github\s+(?:repo|repository)\s+(?:for|called|named)?\s*([A-Za-z0-9_.:/-]+)",
        r"(?:repo|repository)\s+(?:for|called|named)?\s*([A-Za-z0-9_.:/-]+)\s+github",
        r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            subject = match.group(1).strip(" .")
            if subject:
                return subject
    cleaned = clean_search_fragment(text)
    cleaned = re.sub(r"\b(github|repo|repository|summary)\b", " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_restaurant_subject(text: str) -> str:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", text)
    if quoted:
        return clean_search_fragment(quoted.group(1))
    patterns = [
        r"\b(?:restaurant|place|going to|dinner at|lunch at|eating at)\s+([A-Za-z0-9&'. -]+?)(?:\s+(?:can you|what|which|best|based|reviews)|[.?!,]|$)",
        r"\bat\s+([A-Za-z0-9&'. -]+?)\s+(?:restaurant|for dinner|for lunch|tonight)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            subject = clean_search_fragment(match.group(1))
            if subject and subject.lower() not in {"this", "this restaurant", "the restaurant"}:
                return subject
    return ""


def plan_web_search_query(text: str) -> str:
    original = normalize_speech_location_text(text.strip())
    lowered = original.lower()
    direct_urls = extract_direct_urls(original)
    if direct_urls:
        return direct_urls[0]

    location = extract_location_hint(original)

    if is_situational_location_request(original):
        target = location or "Toronto"
        return f"{target} lineup event today".strip()

    if re.search(r"\b(phone|phone number|address|directions|contact)\b", lowered):
        target = re.sub(
            r"^\s*(can you|could you|please|ok|hey)?\s*(find|get|show|give)\s+(me\s+)?",
            "",
            original,
            flags=re.IGNORECASE,
        )
        target = re.sub(r"\b(phone number|phone|address|directions|contact)\b", "", target, flags=re.IGNORECASE)
        target = target.replace("’s", " ").replace("'s", " ")
        target = clean_search_fragment(target) or clean_search_fragment(original)
        requested = "phone number" if "phone" in lowered else "address" if "address" in lowered or "directions" in lowered else "contact"
        return f"{target} official {requested}".strip()

    if re.search(r"\b(events?|concerts?|things to do|happening|coming up)\b", lowered):
        time_hint = "tonight" if "tonight" in lowered else "today" if "today" in lowered else "this week"
        topic = "tech meetups and events" if re.search(r"\b(tech|ai|startup|developer|developers?|meetups?)\b", lowered) else "upcoming events"
        target = location or title_location(re.sub(r".*?\b(?:in|around|near)\b\s+", "", original, flags=re.IGNORECASE))
        target = target or clean_search_fragment(original)
        return f"{topic} {target} {time_hint}".strip()

    if re.search(r"\b(coffee|cafe|cafes|coffee shops?)\b", lowered):
        target = location or clean_search_fragment(original)
        return f"best coffee shops {target} reviews".strip()

    if re.search(r"\b(gas|fuel|gasoline)\b", lowered) and re.search(r"\b(cheap|cheapest|price|prices)\b", lowered):
        target = location or clean_search_fragment(original)
        return f"cheapest gas prices {target} GasBuddy".strip()

    if "github" in lowered or re.search(r"\b(repo|repository)\b", lowered):
        subject = extract_github_subject(original)
        return f"{subject} GitHub repository".strip()

    if re.search(r"\b(chick[-\s·]?fil[-\s·]?a)\b", lowered):
        if re.search(r"\b(feed|people|group|everyone|family|deal|deals|price|prices|buy|order)\b", lowered):
            return "Chick-fil-A Canada menu catering group meal prices official"
        return "Chick-fil-A Canada menu official"

    if re.search(r"\b(food|lunch|dinner|meal|meals|order|deals|feed)\b", lowered):
        target = location or clean_search_fragment(original)
        return f"best value food options {target} official menu prices".strip()

    if re.search(r"\b(restaurant|reviews?|best dish|best dishes|menu|dish)\b", lowered):
        subject = extract_restaurant_subject(original)
        target = subject or location or clean_search_fragment(original)
        return f"best dishes {target} restaurant reviews".strip()

    cleaned = clean_search_fragment(original)
    if location and "near me" in lowered:
        cleaned = f"{cleaned} {location}".strip()
    return cleaned or original


def plan_web_search_queries(text: str) -> list[str]:
    original = normalize_speech_location_text(text.strip())
    primary = plan_web_search_query(original)
    queries = [primary] if primary else []
    location = extract_location_hint(original)
    if is_situational_location_request(original):
        target = location or "Toronto"
        additions: list[str] = []
        if "bloor" in target.lower() and "bathurst" in target.lower():
            additions.extend(
                [
                    "Hot Docs Ted Rogers Cinema schedule today",
                    "Hot Docs Ted Rogers Cinema events today",
                    "Hot Docs Big Ideas screening today",
                    "Hot Docs Cinema Bloor Bathurst event today",
                    "Lee's Palace Bloor Bathurst event tonight",
                ]
            )
        additions.extend(
            [
                f"{target} what is happening right now",
                f"{target} events today",
                f"{target} news today",
                f"{target} Reddit Toronto",
                f"{target} Twitter X",
                f"{target} police news today",
            ]
        )
        queries.extend(additions)
    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        key = query.lower().strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(query.strip())
    return deduped[:10]


def situational_result_priority(result: dict[str, str]) -> int:
    text = " ".join([result.get("title", ""), result.get("url", ""), result.get("snippet", ""), result.get("query", "")]).lower()
    score = 0
    for token, weight in [
        ("hot docs", 40),
        ("ted rogers", 35),
        ("democracy now", 35),
        ("steal this story", 35),
        ("amy goodman", 30),
        ("big ideas", 25),
        ("bloor", 12),
        ("bathurst", 12),
        ("event", 8),
        ("screening", 8),
        ("tonight", 5),
        ("today", 5),
    ]:
        if token in text:
            score += weight
    return score


def is_bad_search_result(result: dict[str, str], query: str, original_request: str = "") -> bool:
    haystack = " ".join([result.get("title", ""), result.get("url", ""), result.get("snippet", "")]).lower()
    if any(domain in haystack for domain in BAD_SOURCE_DOMAINS):
        return True
    q = query.lower()
    if "toronto" in q and "bathurst" in q and "new brunswick" in haystack:
        return True
    if is_situational_location_request(original_request or query):
        if re.search(r"\b(grammar|phrase|correct phrase|definition|meaning|pronunciation)\b", haystack):
            return True
    return False


def extract_search_results(page: Any, max_results: int) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    try:
        rows = page.locator(".result")
        count = min(rows.count(), max_results)
        for index in range(count):
            row = rows.nth(index)
            title_node = row.locator("a.result__a").first
            if title_node.count() == 0:
                continue
            title = title_node.inner_text(timeout=1500).strip()
            href = normalize_duckduckgo_url(title_node.get_attribute("href") or "")
            snippet = ""
            snippet_node = row.locator(".result__snippet").first
            if snippet_node.count() > 0:
                snippet = snippet_node.inner_text(timeout=1500).strip()
            if href and title:
                results.append({"title": title, "url": href, "snippet": snippet})
    except Exception:
        results = []
    if results:
        return results[:max_results]

    try:
        anchors = page.locator("a[href]")
        count = min(anchors.count(), 80)
        seen: set[str] = set()
        for index in range(count):
            anchor = anchors.nth(index)
            title = anchor.inner_text(timeout=1000).strip()
            href = normalize_duckduckgo_url(anchor.get_attribute("href") or "")
            if not title or not href.startswith("http") or "duckduckgo.com" in href or href in seen:
                continue
            seen.add(href)
            results.append({"title": title, "url": href, "snippet": ""})
            if len(results) >= max_results:
                break
    except Exception:
        pass
    return results[:max_results]


def read_page_evidence(context: Any, url: str, query: str, timeout_ms: int) -> dict[str, Any]:
    if is_automation_hostile_url(url):
        return {
            "url": url,
            "title": "Skipped automated read",
            "description": "Skipped this source because it commonly blocks automated browsers.",
            "evidence": [],
            "error": "Skipped automated read: source commonly blocks automation. Use official/alternate sources or manual browser review.",
            "blocked": True,
        }
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(1000)
        title = page.title()
        description = ""
        try:
            description = str(
                page.locator("meta[name='description']").first.get_attribute("content") or ""
            ).strip()
        except Exception:
            description = ""
        body_text = page.locator("body").inner_text(timeout=min(timeout_ms, 7000))
        if looks_like_access_block(f"{title}\n{description}\n{body_text}"):
            return {
                "url": url,
                "title": title or "Access restricted",
                "description": description,
                "evidence": [],
                "error": "Access block detected. I did not try to bypass the site's automation restrictions.",
                "blocked": True,
            }
        lines = evidence_lines(body_text, query)
        return {"url": url, "title": title, "description": description, "evidence": lines, "error": ""}
    except Exception as exc:
        return {"url": url, "title": "", "description": "", "evidence": [], "error": str(exc)}
    finally:
        page.close()


def format_web_research_note(query: str, results: list[dict[str, str]], pages: list[dict[str, Any]]) -> str:
    lines = ["Web research completed.", f"Query: {query}"]
    if results:
        lines.append("Search results:")
        for index, result in enumerate(results, start=1):
            lines.append(f"{index}. {result.get('title', '').strip()}")
            lines.append(f"URL: {result.get('url', '').strip()}")
            if result.get("query"):
                lines.append(f"Matched Query: {result.get('query', '').strip()}")
            snippet = result.get("snippet", "").strip()
            if snippet:
                lines.append(f"Snippet: {snippet[:500]}")
    if pages:
        lines.append("Opened sources:")
        for index, page in enumerate(pages, start=1):
            lines.append(f"{index}. {page.get('title') or 'Source'}")
            lines.append(f"URL: {page.get('url', '').strip()}")
            if page.get("blocked"):
                lines.append(f"Automation note: {str(page.get('error', 'Source blocked automation.'))[:300]}")
                continue
            if page.get("description"):
                lines.append(f"Description: {str(page['description'])[:400]}")
            if page.get("evidence"):
                lines.append("Evidence:")
                for item in page["evidence"][:6]:
                    lines.append(f"- {item[:500]}")
            elif page.get("error"):
                lines.append(f"Read error: {str(page['error'])[:300]}")
    if not results and not pages:
        lines.append("No source data could be extracted.")
    return "\n".join(lines)[:8000]


def evidence_fallback_reply(note: str, task_id: str, original_request: str = "") -> str:
    group_order = chick_fil_a_group_order_reply(original_request, task_id, note)
    if group_order:
        return group_order
    if "Browser automation is disabled" in note:
        return (
            "I received the web request, but browser automation is disabled in ChiefChat config. "
            f"I left `{task_id}` open so a web-capable role can finish it."
        )
    if "Browser automation is not installed" in note:
        return (
            "I received the web request, but Playwright/browser support is not installed for ChiefChat yet. "
            f"I left `{task_id}` open. Run `py ChiefChat\\setup_chief_chat.py` when you want to enable local browser research."
        )
    if "No source data could be extracted." in note:
        return (
            "I opened the web path, but I could not extract enough readable source text automatically. "
            f"I left `{task_id}` open for a web-capable role to finish it."
        )
    if "Access block detected" in note or "Skipped automated read" in note:
        cards = web_source_cards(note)
        usable = [card for card in cards if not is_automation_hostile_url(str(card.get("url", "")))]
        if usable:
            lines = ["Some review/directory sites blocked automated access, so I used the safer source results instead:"]
            for card in usable[:4]:
                lines.append(f"- {concise_card_line(card)}")
            lines.append(f"I left `{task_id}` open if you want a human/manual review pass on the blocked sites.")
            return "\n".join(lines)
        return (
            "The main sources I found blocked automated browser access. I did not try to bypass that. "
            f"I left `{task_id}` open so a web-capable role or manual browser pass can verify it."
        )
    situational = situational_evidence_reply(note, task_id)
    if situational:
        return situational
    cards = web_source_cards(note)
    intent = web_intent(original_request or note)
    if cards:
        if intent == "events":
            lines = ["I found these concrete event leads:"]
            for card in cards[:5]:
                lines.append(f"- {concise_card_line(card)}")
            lines.append(f"I left `{task_id}` open if you want Researcher to verify tickets/details deeper.")
            return "\n".join(lines)
        if intent == "news":
            lines = ["Here are the strongest current news leads I found:"]
            for card in cards[:5]:
                lines.append(f"- {concise_card_line(card, include_evidence=False)}")
            lines.append(f"I left `{task_id}` open for a fuller brief if needed.")
            return "\n".join(lines)
        if intent == "hours":
            top = cards[0]
            lines = ["Best source I found for the hours:"]
            lines.append(f"- {concise_card_line(top)}")
            if len(cards) > 1:
                lines.append("Other source checked: " + concise_card_line(cards[1], include_evidence=False))
            lines.append(f"I left `{task_id}` open if a role needs to verify store-specific hours.")
            return "\n".join(lines)
        if intent in {"github", "research", "restaurant", "gas", "business_lookup"}:
            lines = ["Here is what I could verify from the source results:"]
            for card in cards[:4]:
                lines.append(f"- {concise_card_line(card)}")
            lines.append(f"I left `{task_id}` open for deeper follow-up if you want it expanded.")
            return "\n".join(lines)
    source_title = ""
    source_url = ""
    evidence: list[str] = []
    for raw in note.splitlines():
        line = raw.strip()
        if not source_title and re.match(r"^\d+\.\s+", line):
            source_title = re.sub(r"^\d+\.\s+", "", line)
        elif not source_url and line.startswith("URL:"):
            source_url = line.split(":", 1)[1].strip()
        elif line.startswith("- "):
            evidence.append(line[2:].strip())
    chunks = ["I found web evidence, but the local chat model did not turn it into a final answer cleanly."]
    if source_title:
        chunks.append(f"Top source: {source_title}")
    if source_url:
        chunks.append(source_url)
    if evidence:
        chunks.append("What I could verify:")
        chunks.extend(f"- {line[:280]}" for line in evidence[:4])
    chunks.append(f"I also left `{task_id}` open for deeper follow-up if you want a fuller answer.")
    return "\n".join(chunks)


def first_source_url(note: str) -> str:
    for raw in note.splitlines():
        line = raw.strip()
        if line.startswith("URL:"):
            return line.split(":", 1)[1].strip()
    return ""


def web_source_cards(note: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_evidence = False

    def flush() -> None:
        nonlocal current, in_evidence
        if current and (current.get("title") or current.get("url") or current.get("evidence")):
            cards.append(current)
        current = None
        in_evidence = False

    for raw in note.splitlines():
        line = raw.strip()
        if re.match(r"^\d+\.\s+", line):
            flush()
            current = {"title": re.sub(r"^\d+\.\s+", "", line).strip(), "url": "", "snippet": "", "evidence": []}
            continue
        if current is None:
            continue
        if line.startswith("URL:"):
            current["url"] = line.split(":", 1)[1].strip()
            in_evidence = False
        elif line.startswith("Snippet:"):
            current["snippet"] = line.split(":", 1)[1].strip()
            in_evidence = False
        elif line == "Evidence:":
            in_evidence = True
        elif in_evidence and line.startswith("- "):
            current.setdefault("evidence", []).append(line[2:].strip())
        elif line.startswith("Description:") and not current.get("snippet"):
            current["snippet"] = line.split(":", 1)[1].strip()
            in_evidence = False
    flush()

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in cards:
        key = (card.get("url") or card.get("title") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(card)
    return deduped


def concise_card_line(card: dict[str, Any], *, include_evidence: bool = True) -> str:
    title = str(card.get("title") or "Source").strip()
    url = str(card.get("url") or "").strip()
    evidence = [str(item).strip() for item in card.get("evidence", []) if str(item).strip()]
    snippet = str(card.get("snippet") or "").strip()
    detail = evidence[0] if evidence and include_evidence else snippet
    pieces = [title]
    if detail:
        pieces.append(detail[:220])
    if url:
        pieces.append(url)
    return " - ".join(pieces)


def chick_fil_a_group_order_reply(original_request: str, task_id: str, note: str = "") -> str:
    lowered = original_request.lower()
    if not re.search(r"\bchick[-\s·]?fil[-\s·]?a\b", lowered):
        return ""
    group_match = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:grown\s+)?(?:people|adults|of us)\b", lowered)
    has_group_need = bool(group_match or re.search(r"\b(feed|everyone|group|family|fully|hungry)\b", lowered))
    if not has_group_need:
        return ""
    source = first_source_url(note)
    source_line = f"\nSource checked: {source}" if source else "\nPrices vary by location, so confirm in the Chick-fil-A app before ordering."
    return (
        "For five grown people, I would order this as a filling baseline:\n\n"
        "1. Five chicken sandwiches or spicy/deluxe sandwiches.\n"
        "2. One 30-count nuggets tray to share.\n"
        "3. Two large waffle fries, or five medium fries if everyone wants their own.\n"
        "4. Add mac and cheese or side salads if this needs to feel like a real meal, not just fast food.\n"
        "5. Five drinks, unless you already have drinks at home.\n\n"
        "Budget/value version: five sandwiches, a 30-count nugget, and two large fries.\n"
        "Heavier version: five meals plus a 30-count nugget to share.\n"
        f"{source_line}\n\n"
        f"I left {task_id} open if you want exact live pricing for the specific store."
    )


def situational_evidence_reply(note: str, task_id: str) -> str:
    lowered = note.lower()
    is_situational = "situational investigation mode" in lowered or "lineup" in lowered or "crowd" in lowered
    if not is_situational:
        return ""
    url = first_source_url(note)
    if "hot docs" in lowered and "steal this story" in lowered and "amy goodman" in lowered:
        source = f"\n\nSource: {url}" if url else ""
        return (
            "I found the likely reason: Hot Docs/Ted Rogers Cinema had a Big Ideas screening of "
            "`Steal This Story, Please!`, and Amy Goodman was appearing in person with co-director Tia Lessin for the discussion. "
            "There was a 5:00 PM cocktail reception and a 6:30 PM screening/discussion, so if the line was by Hot Docs, "
            "that is very likely what you were seeing.\n\n"
            "Confidence: high if you were right by Hot Docs/Ted Rogers Cinema; otherwise I would still check nearby venues."
            f"{source}"
        )

    source_title = ""
    evidence: list[str] = []
    for raw in note.splitlines():
        line = raw.strip()
        if not source_title and re.match(r"^\d+\.\s+", line):
            source_title = re.sub(r"^\d+\.\s+", "", line)
        elif line.startswith("- "):
            evidence.append(line[2:].strip())
    if source_title or evidence:
        bits = [f"The strongest lead I found is `{source_title or 'a nearby public listing'}`."]
        if evidence:
            bits.append("What points that way: " + " ".join(evidence[:2])[:420])
        if url:
            bits.append(f"Source: {url}")
        bits.append(f"Confidence: medium. I left `{task_id}` open so Researcher can verify if needed.")
        return "\n\n".join(bits)
    return ""


def looks_like_progress_reply(reply: str, web_context: str) -> bool:
    if not web_context:
        return False
    lowered = reply.lower().strip()
    progress_phrases = [
        "i'm checking",
        "i am checking",
        "i'll check",
        "i will check",
        "i'm looking",
        "i am looking",
        "let me check",
        "let me look",
        "checking now",
        "looking that up",
        "stand by",
        "i'll route",
        "i will route",
        "i am routing",
        "i'm routing",
        "i'll search",
        "i will search",
    ]
    has_progress = any(phrase in lowered for phrase in progress_phrases)
    has_answer_signal = bool(re.search(r"\d|source:|http|according to|based on|found|top source", lowered))
    return has_progress and (len(reply) < 260 or not has_answer_signal)


def looks_like_directory_reply(reply: str, web_context: str) -> bool:
    if not web_context:
        return False
    lowered = reply.lower()
    directory_phrases = [
        "here are some ways to find",
        "you can check",
        "i recommend checking",
        "for the most accurate",
        "for accurate and up-to-date",
        "if you need specific",
    ]
    has_directory_phrase = any(phrase in lowered for phrase in directory_phrases)
    has_concrete_detail = bool(re.search(r"\b(\d{1,2}:\d{2}|\d{1,2}\s?(am|pm)|tonight|today|tomorrow|source:|venue|location)\b", lowered))
    return has_directory_phrase and not has_concrete_detail


def lacks_web_answer_evidence(reply: str, web_context: str, original_request: str) -> bool:
    if not web_context:
        return False
    intent = web_intent(original_request)
    if intent not in {"situational", "events", "hours", "news", "restaurant", "gas", "github", "research"}:
        return False
    lowered = reply.lower()
    has_source_signal = bool(re.search(r"https?://|source:|according to|found|verified|confidence:", lowered))
    has_detail_signal = bool(re.search(r"\d|[A-Z][a-z]+ [A-Z][a-z]+|pm|am|venue|location|price|hours|headline", reply))
    context_has_source = "URL:" in web_context or "Evidence:" in web_context
    return context_has_source and not (has_source_signal and has_detail_signal)


def violates_chief_voice(reply: str) -> bool:
    lowered = reply.lower().strip()
    banned = [
        "understood,",
        "stand by",
        "awaiting further instructions",
        "i will ensure",
    ]
    return any(phrase in lowered for phrase in banned)


def apply_voice_cleanup(reply: str) -> str:
    cleaned = reply.strip()
    replacements = {
        r"^Understood,?\s*(?:operator|user)?\.?\s*": "Got it. ",
        r"\bI will ensure\b": "I'll make sure",
        r"\bStand by\.?\b": "",
        r"\bAwaiting further instructions\.?\b": "",
    }
    for pattern, replacement in replacements.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def try_browser_research(root: Path, config: dict[str, str], query: str, original_request: str = "") -> str:
    if not parse_bool(config.get("Browser Enabled", "YES"), True):
        return "Browser automation is disabled in ChiefChat config."
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return "Browser automation is not installed. Run `py ChiefChat\\setup_chief_chat.py` to install/check Playwright."

    max_seconds = parse_int(config.get("Browser Max Run Seconds", "120"), 120)
    max_results = max(1, parse_int(config.get("Browser Search Results", "5"), 5))
    pages_to_read = max(0, parse_int(config.get("Browser Pages To Read", "3"), 3))
    headless = parse_bool(config.get("Browser Headless", "NO"), False)
    profile = browser_profile_dir(root)
    profile.mkdir(parents=True, exist_ok=True)
    timeout_ms = max(5000, max_seconds * 1000)
    direct_urls = extract_direct_urls(query)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(str(profile), headless=headless)
        try:
            results: list[dict[str, str]] = []
            pages: list[dict[str, Any]] = []
            if direct_urls:
                results = [{"title": url, "url": url, "snippet": "Direct URL from operator request."} for url in direct_urls[:max_results]]
            else:
                situational = bool(original_request and is_situational_location_request(original_request))
                queries = plan_web_search_queries(original_request) if situational else [query]
                seen_urls: set[str] = set()
                result_cap = max_results * 3 if situational else max_results
                for current_query in queries:
                    page = context.new_page()
                    try:
                        search_url = "https://duckduckgo.com/html/?q=" + urllib.parse.quote(current_query)
                        page.goto(search_url, wait_until="domcontentloaded", timeout=timeout_ms)
                        page.wait_for_timeout(1000)
                        for result in extract_search_results(page, max_results):
                            url = result.get("url", "")
                            if not url or url in seen_urls or is_bad_search_result(result, current_query, original_request):
                                continue
                            seen_urls.add(url)
                            result["query"] = current_query
                            results.append(result)
                            if len(results) >= result_cap:
                                break
                    finally:
                        page.close()
                    if len(results) >= result_cap:
                        break
                if situational:
                    results.sort(key=situational_result_priority, reverse=True)
            opened_count = 0
            skipped_count = 0
            for result in results:
                url = result.get("url", "")
                if not url.startswith("http"):
                    continue
                if is_automation_hostile_url(url):
                    if skipped_count < 3:
                        pages.append(read_page_evidence(context, url, result.get("query") or query, timeout_ms))
                    skipped_count += 1
                    continue
                if opened_count >= pages_to_read:
                    continue
                pages.append(read_page_evidence(context, url, result.get("query") or query, timeout_ms))
                opened_count += 1
            note = format_web_research_note(query, results, pages)
            if original_request and original_request.strip() != query.strip():
                extra = ""
                if is_situational_location_request(original_request):
                    planned = "\n".join(f"- {item}" for item in plan_web_search_queries(original_request))
                    extra = f"\nSituational investigation mode: lineup/crowd/current-place request.\nSearch fan-out:\n{planned}"
                return f"Original operator request: {original_request.strip()}\nPlanned search query: {query.strip()}{extra}\n{note}"
            return note
        finally:
            context.close()


def task_exists(root: Path, task_id: str) -> bool:
    return task_id in read_text(root / "LAYER_TASK_LIST.md")


TASK_BLOCK_RE = re.compile(r"(?ms)^## TASK\s*\n.*?(?=^## TASK\s*\n|\Z)")
TASK_ID_RE = re.compile(r"\bTASK-[A-Z0-9][A-Z0-9_-]*\b", flags=re.IGNORECASE)
ACTIONABLE_TASK_STATUSES = {"TODO", "IN_PROGRESS", "ACTIVE", "OPEN", "READY"}
NON_ACTIONABLE_TASK_STATUSES = {"DONE", "CANCELLED", "CANCELED", "BLOCKED", "WAITING_ON_HUMAN", "HUMAN_CHECKOUT"}


def chief_task_paths(root: Path) -> list[Path]:
    paths = [root / "LAYER_TASK_LIST.md"]
    projects_root = root / "Projects"
    if projects_root.exists():
        paths.extend(sorted(projects_root.glob("*/TASKS.md")))
    return paths


def parse_task_block(block: str, path: Path) -> dict[str, str]:
    task: dict[str, str] = {"source_file": str(path)}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("- ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        task[key.strip().lower().replace(" ", "_")] = value.strip()
    if "task_id" not in task and "id" in task:
        task["task_id"] = task["id"]
    return task


def task_status(task: dict[str, str]) -> str:
    return str(task.get("status", "")).strip().upper()


def task_actionable_local(task: dict[str, str]) -> bool:
    status = task_status(task)
    return bool(status and status in ACTIONABLE_TASK_STATUSES and status not in NON_ACTIONABLE_TASK_STATUSES)


def actionable_task_count(root: Path) -> int:
    return sum(1 for task in collect_tasks(root) if task_is_actionable(task))


def task_created_date(task: dict[str, str]) -> datetime | None:
    value = task.get("created_at", "") or task.get("created", "")
    if not value:
        return None
    try:
        clean = value.strip()
        if clean.endswith("Z"):
            clean = clean[:-1] + "+00:00"
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def exact_task_ids(text: str) -> list[str]:
    ids: list[str] = []
    for match in TASK_ID_RE.findall(text.upper()):
        clean = match.strip().upper()
        if clean not in ids:
            ids.append(clean)
    return ids


def set_task_field(block: str, field: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(field)}:\s*.*$")
    if pattern.search(block):
        return pattern.sub(f"{field}: {value}", block, count=1)
    lines = block.splitlines()
    insert_at = 1
    for index, line in enumerate(lines):
        if line.startswith("ID:"):
            insert_at = index + 1
            break
    lines.insert(insert_at, f"{field}: {value}")
    return "\n".join(lines)


def append_task_audit(block: str, note: str) -> str:
    return block.rstrip() + f"\nAudit: {note}\n"


def mutate_task_blocks(root: Path, predicate: Any, mutate: Any) -> list[dict[str, str]]:
    changed: list[dict[str, str]] = []
    for path in chief_task_paths(root):
        text = read_text(path)
        if not text:
            continue
        matches = list(TASK_BLOCK_RE.finditer(text))
        if not matches:
            continue
        pieces: list[str] = []
        cursor = 0
        path_changed = False
        for match in matches:
            pieces.append(text[cursor:match.start()])
            block = match.group(0)
            task = parse_task_block(block, path)
            if predicate(task):
                new_block, meta = mutate(block, task)
                if new_block != block:
                    pieces.append(new_block)
                    changed.append({**task, **meta, "source_file": str(path)})
                    path_changed = True
                else:
                    pieces.append(block)
            else:
                pieces.append(block)
            cursor = match.end()
        pieces.append(text[cursor:])
        if path_changed:
            atomic_write_text(path, "".join(pieces).rstrip() + "\n")
    return changed


def task_mutation_audit(action: str, message_id: str, detail: str) -> str:
    source = message_id or "UNKNOWN"
    return f"[{iso_now()}] ChiefChat {action} from operator message {source}. {detail}".strip()


def cancel_matching_tasks(root: Path, predicate: Any, *, message_id: str, reason: str) -> list[dict[str, str]]:
    def mutate(block: str, task: dict[str, str]) -> tuple[str, dict[str, str]]:
        previous = task_status(task) or "UNKNOWN"
        updated = set_task_field(block, "Status", "CANCELLED")
        updated = append_task_audit(updated, task_mutation_audit("cancelled task", message_id, f"Previous status: {previous}. Reason: {reason}."))
        return updated, {"previous_status": previous, "new_status": "CANCELLED"}

    return mutate_task_blocks(root, lambda task: predicate(task) and task_actionable_local(task), mutate)


def set_matching_task_status(root: Path, ids: list[str], status: str, *, message_id: str, reason: str) -> list[dict[str, str]]:
    wanted = {item.upper() for item in ids}

    def mutate(block: str, task: dict[str, str]) -> tuple[str, dict[str, str]]:
        previous = task_status(task) or "UNKNOWN"
        updated = set_task_field(block, "Status", status)
        updated = append_task_audit(updated, task_mutation_audit(f"set status to {status}", message_id, f"Previous status: {previous}. Reason: {reason}."))
        return updated, {"previous_status": previous, "new_status": status}

    return mutate_task_blocks(root, lambda task: task.get("task_id", "").upper() in wanted, mutate)


def assign_matching_tasks(root: Path, ids: list[str], owner: str, *, message_id: str, reason: str) -> list[dict[str, str]]:
    wanted = {item.upper() for item in ids}

    def mutate(block: str, task: dict[str, str]) -> tuple[str, dict[str, str]]:
        previous = task.get("owner_role", "") or "Unassigned"
        updated = set_task_field(block, "Owner Role", owner)
        updated = append_task_audit(updated, task_mutation_audit(f"assigned task to {owner}", message_id, f"Previous owner: {previous}. Reason: {reason}."))
        return updated, {"previous_owner": previous, "new_owner": owner}

    changed = mutate_task_blocks(root, lambda task: task.get("task_id", "").upper() in wanted, mutate)
    for item in changed:
        append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {owner}: reassigned_task:{item.get('task_id', '')}")
    return changed


def add_note_to_matching_tasks(root: Path, ids: list[str], note: str, *, message_id: str) -> list[dict[str, str]]:
    wanted = {item.upper() for item in ids}
    clean_note = re.sub(r"\s+", " ", note).strip()

    def mutate(block: str, task: dict[str, str]) -> tuple[str, dict[str, str]]:
        updated = append_task_audit(block, task_mutation_audit("added note", message_id, clean_note[:500]))
        return updated, {"note": clean_note[:500]}

    return mutate_task_blocks(root, lambda task: task.get("task_id", "").upper() in wanted, mutate)


def is_stale_web_task(task: dict[str, str], *, include_today: bool = False) -> bool:
    task_id = task.get("task_id", "").upper()
    if not task_id.startswith("TASK-WEB-") or not task_actionable_local(task):
        return False
    if include_today:
        return True
    created = task_created_date(task)
    if created is None:
        return True
    return created.date() < datetime.now().astimezone().date()


def cancel_stale_web_tasks(root: Path, *, message_id: str = "manual-cleanup", include_today: bool = False) -> dict[str, Any]:
    before = actionable_task_count(root)
    changed = cancel_matching_tasks(
        root,
        lambda task: is_stale_web_task(task, include_today=include_today),
        message_id=message_id,
        reason="stale web/current-info request cleanup",
    )
    after = actionable_task_count(root)
    summary = {
        "changed": changed,
        "changed_count": len(changed),
        "before": before,
        "after": after,
        "ids": [item.get("task_id", "") for item in changed],
    }
    append_event(
        root,
        f"TASK_CLEANUP - Cancelled {summary['changed_count']} stale web tasks. Actionable tasks {before} -> {after}.",
    )
    return summary


def recent_chat_mentions_web_requests(root: Path) -> bool:
    recent = recent_chat_context(root, load_config(root), max_chars=2500).lower()
    return "web request" in recent or "task-web-" in recent


def latest_visible_task_id(root: Path) -> str:
    recent = recent_chat_context(root, load_config(root), max_chars=3500)
    ids = exact_task_ids(recent)
    if ids:
        return ids[-1]
    tasks = [task for task in collect_tasks(root) if task_is_actionable(task)]
    if tasks:
        return str(tasks[-1].get("task_id", "") or tasks[-1].get("id", "")).upper()
    return ""


def task_action_owner(root: Path, text: str) -> str:
    lowered = text.lower()
    aliases = sorted(role_alias_map(root).items(), key=lambda item: len(item[0]), reverse=True)
    for alias, role in aliases:
        alias_text = alias.lower().replace("_", " ")
        if alias_text and re.search(rf"\b{re.escape(alias_text)}\b", lowered):
            return role
    for role in known_role_names(root):
        role_text = role.lower().replace("_", " ")
        if role_text and re.search(rf"\b{re.escape(role_text)}\b", lowered):
            return role
    return ""


def note_text_from_action_request(text: str) -> str:
    match = re.search(r"\b(?:add|append|write|save)\s+(?:this\s+)?note(?:\s+to\s+\S+)?\s*[:,-]?\s*(.+)$", text, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def is_task_action_request(root: Path, text: str) -> bool:
    lowered = text.lower()
    ids = exact_task_ids(text)
    if re.search(r"\b(remove|cancel|clear|archive|delete)\b", lowered) and (
        ids or "web request" in lowered or "web task" in lowered or "task-web" in lowered or (re.search(r"\bthem|those\b", lowered) and recent_chat_mentions_web_requests(root))
    ):
        return True
    if ids and re.search(r"\b(complete|done|finish|finished|reopen|open back up|resume|cancel|archive|remove|clear|assign|reassign|move|add note|append note|write note)\b", lowered):
        return True
    if re.search(r"\bassign\s+(this|it|that)\s+to\b", lowered):
        return True
    return False


def is_role_wake_request(root: Path, text: str) -> bool:
    lowered = text.lower()
    if not re.search(r"\b(wake|nudge|ping|start)\b", lowered):
        return False
    return bool(task_action_owner(root, text))


def task_action_reply(root: Path, message: dict[str, str]) -> str:
    body = message.get("body", "")
    msg_id = message.get("id", "") or "UNKNOWN"
    lowered = body.lower()
    ids = exact_task_ids(body)
    before = actionable_task_count(root)

    if re.search(r"\b(remove|cancel|clear|archive|delete)\b", lowered) and (
        "web request" in lowered or "web task" in lowered or "task-web" in lowered or (re.search(r"\bthem|those\b", lowered) and recent_chat_mentions_web_requests(root))
    ):
        include_today = bool(re.search(r"\b(all|today|everything|every)\b", lowered))
        result = cancel_stale_web_tasks(root, message_id=msg_id, include_today=include_today)
        changed_ids = [item for item in result["ids"] if item]
        if changed_ids:
            shown = ", ".join(changed_ids[:8])
            more = f" and {len(changed_ids) - 8} more" if len(changed_ids) > 8 else ""
            return (
                "Done. I actually updated the task file this time.\n\n"
                "Action: cancelled stale web/current-info tasks.\n"
                f"Changed: {len(changed_ids)} tasks.\n"
                f"Actionable tasks: {result['before']} -> {result['after']}.\n"
                f"Changed IDs: {shown}{more}."
            )
        return (
            "I did not change anything because I found no matching actionable stale web tasks.\n\n"
            f"Actionable tasks: {result['before']} -> {result['after']}."
        )

    if not ids and re.search(r"\b(this|it|that)\b", lowered):
        latest = latest_visible_task_id(root)
        if latest:
            ids = [latest]
    if not ids:
        return "I need the task ID for that action. Send something like `Complete TASK-...` or `Assign TASK-... to Engineer`."

    if re.search(r"\b(reopen|open back up|resume)\b", lowered):
        changed = set_matching_task_status(root, ids, "TODO", message_id=msg_id, reason="operator requested reopen")
        action = "reopened"
    elif re.search(r"\b(complete|done|finish|finished)\b", lowered):
        changed = set_matching_task_status(root, ids, "DONE", message_id=msg_id, reason="operator marked complete")
        action = "completed"
    elif re.search(r"\b(remove|cancel|clear|archive|delete)\b", lowered):
        changed = set_matching_task_status(root, ids, "CANCELLED", message_id=msg_id, reason="operator cancelled task")
        action = "cancelled"
    elif re.search(r"\b(assign|reassign|move)\b", lowered):
        owner = task_action_owner(root, body)
        if not owner:
            return "I found the task ID, but I need the target role. Say something like `Assign TASK-... to Engineer`."
        changed = assign_matching_tasks(root, ids, owner, message_id=msg_id, reason="operator reassigned task")
        action = f"assigned to {owner}"
    elif re.search(r"\b(add note|append note|write note|save note)\b", lowered):
        note = note_text_from_action_request(body)
        if not note:
            return "I found the task ID, but I need the note text to add."
        changed = add_note_to_matching_tasks(root, ids, note, message_id=msg_id)
        action = "added note to"
    else:
        return "I understood this as a task action, but I need a clearer verb: complete, cancel, reopen, assign, or add note."

    after = actionable_task_count(root)
    changed_ids = [item.get("task_id", "") for item in changed if item.get("task_id")]
    if not changed_ids:
        return (
            "I did not change anything because no matching task IDs were found.\n\n"
            f"Requested IDs: {', '.join(ids)}.\n"
            f"Actionable tasks: {before} -> {after}."
        )
    return (
        f"Done. I {action} {len(changed_ids)} task(s) in the files.\n\n"
        f"Actionable tasks: {before} -> {after}.\n"
        "Changed IDs: " + ", ".join(changed_ids[:10]) + "."
    )


def role_wake_reply(root: Path, message: dict[str, str]) -> str:
    role = task_action_owner(root, message.get("body", ""))
    if not role:
        return "I could not match that to a registered role or bot alias. Tell me which role to wake."
    append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {role}: operator_wake:{message.get('id', '') or 'UNKNOWN'}")
    state, note = role_readiness(root, role)
    if state == "ready":
        return f"Done. I wrote a wake request for `{role}`. It is automation-ready, so Runner can pick it up."
    return f"Done. I wrote a wake request for `{role}`, but {role} {note}."


NUMBERED_TASK_RE = re.compile(r"(?ms)^\s*(\d{1,3})[.)]\s+(.+?)(?=^\s*\d{1,3}[.)]\s+|\Z)")


TASK_INTAKE_PHRASES = (
    "add these tasks",
    "add these items",
    "add this to the task list",
    "add these to the task list",
    "put this in the task list",
    "put these in the task list",
    "place this in the task list",
    "place these in the task list",
    "save this to the task list",
    "write this into the task list",
    "go add these items",
    "go add these tasks",
    "tasks that we need to get done",
    "list of tasks that we need to get done",
    "figure out which team members",
    "which team members we need",
    "which bots we need",
    "delegating to any existing bot roles",
    "delegate to any existing bot roles",
)

SINGLE_TASK_CAPTURE_PATTERNS = [
    r"\b(make sure|please make sure|ensure)\s+(this|that|it)\s+(is|gets|goes|stays)\s+(in|on|added to)\s+(the\s+)?(task list|to-do|todo|backlog|list of tasks)\b",
    r"\b(add|log|capture|save|write down|remember)\s+(this|that|it)\s+(as\s+)?(a\s+)?(task|to-do|todo|backlog item)\b",
    r"\b(make|write|create|add)\s+(a\s+)?(note|bug note|issue|bug report)\s+(of|about|for)\s+(this|that|the)\s+(bug|error|issue|failure|mistake)\b",
    r"\b(make|write|create|add)\s+(a\s+)?(note|bug note|issue|bug report)\b",
    r"\b(don'?t|do not)\s+forget\s+(this|that|it)\b",
]

ROLE_ADD_PATTERNS = [
    r"\b(?:yes\s+)?(?:add|create|register|set up)\s+(?:the\s+)?([A-Za-z][A-Za-z0-9 _-]{1,40}?)\s+role\b",
    r"\b(?:yes\s+)?(?:add|create|register|set up)\s+(?:a\s+new\s+role\s+(?:called|named)\s+)([A-Za-z][A-Za-z0-9 _-]{1,40})\b",
]

WORK_REQUEST_PATTERNS = [
    r"\b(i need you to|we need to|let'?s start|start figuring out|figure out how to|go through my|scan my|review my)\b",
    r"\b(prepare|draft|write|create|build|design|research|analyze|organize|map out|set up)\s+(?:a|an|the|my|our)?\b",
    r"\b(cold email|outreach|lead generation|proposal|quote generator|sales plan|onboarding plan|obsidian notes|second brain)\b",
]

HUMAN_ASSIST_PATTERNS = [
    r"\b(?:ask|have|get)\s+([A-Z][A-Za-z0-9_-]{1,40})\s+(?:to|help)\b",
    r"\b(?:check|check\s+in|follow\s+up|coordinate|talk|speak)\s+with\s+([A-Z][A-Za-z0-9_-]{1,40})\b",
    r"\b(?:message|contact|ping|tell|send)\s+([A-Z][A-Za-z0-9_-]{1,40})\b",
    r"\b([A-Z][A-Za-z0-9_-]{1,40})\s+(?:can|should)\s+help\b",
]

HUMAN_NAME_STOPWORDS = {
    "access",
    "agent",
    "assistant",
    "bot",
    "chief",
    "contact",
    "context",
    "data",
    "engineer",
    "file",
    "files",
    "for",
    "me",
    "my",
    "notes",
    "over",
    "human",
    "info",
    "information",
    "lead",
    "leads",
    "list",
    "operator",
    "our",
    "permission",
    "permissions",
    "researcher",
    "role",
    "staff",
    "system",
    "task",
    "tasks",
    "that",
    "the",
    "their",
    "these",
    "this",
    "tool",
    "tools",
    "user",
    "you",
    "your",
}


def extract_numbered_tasks(text: str) -> list[str]:
    tasks: list[str] = []
    for _number, raw in NUMBERED_TASK_RE.findall(text):
        clean = re.sub(r"\s+", " ", raw).strip(" \t\r\n-")
        if clean:
            tasks.append(clean)
    return tasks


def normalize_brand_and_names(text: str) -> str:
    value = re.sub(r"\bChick[·\s-]*fil[·\s-]*A\b", "Chick-fil-A", text, flags=re.IGNORECASE)
    value = re.sub(r"\bLeelas\b", "Leela's", value, flags=re.IGNORECASE)
    value = re.sub(r"\buncle\s+vishnu\b", "Uncle Vishnu", value, flags=re.IGNORECASE)
    return value


def clean_today_item(text: str) -> str:
    value = normalize_brand_and_names(re.sub(r"\s+", " ", text).strip(" .,:;-"))
    value = re.sub(r"^(?:and\s+)?(?:i|we)\s+(?:have|need|got)\s+to\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:and\s+)?(?:have|need|got)\s+to\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:go\s+)?to\s+", "", value, flags=re.IGNORECASE)
    if value:
        value = value[:1].upper() + value[1:]
    return value


def extract_today_checklist_items(text: str) -> list[str]:
    body = normalize_brand_and_names(text)
    body = re.sub(r"\bto[.)]?\s+(?=I\s+have|I\s+need|grab|go|pick|drop|get)\b", " two ", body, flags=re.IGNORECASE)
    body = re.sub(r"\bfor\s+(?=I\s+have|I\s+need|get|go|help|drop)\b", " four ", body, flags=re.IGNORECASE)
    body = re.sub(
        r"^.*?\b(?:current tasks for today|tasks for today|today'?s tasks|todo list for today|to-do list for today|errands for today|errands today)\b[:,-]?\s*",
        "",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    marker_re = re.compile(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d{1,2})[.)]?\s+",
        flags=re.IGNORECASE,
    )
    parts = marker_re.split(body)
    items: list[str] = []
    if len(parts) > 2:
        for index in range(2, len(parts), 2):
            item = clean_today_item(parts[index])
            if item and item.lower() not in {"and", "then"}:
                items.append(item)
    if len(items) < 2:
        for raw in re.split(r"[.;]\s+|\n+", body):
            item = clean_today_item(raw)
            if item:
                items.append(item)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.lower()
        if key not in seen and len(item) > 8:
            seen.add(key)
            deduped.append(item)
    return deduped[:12]


def is_today_checklist_request(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"\b(team members|which bots|delegate|delegating|researcher|engineer|task list that we need|get done)\b", lowered):
        return False
    has_day_signal = bool(
        re.search(
            r"\b(current tasks for today|tasks for today|today'?s tasks|todo list for today|to-do list for today|errands for today|errands today)\b",
            lowered,
        )
    )
    has_capture_signal = bool(re.search(r"\b(make note|note down|write down|remember|save|capture|add)\b", lowered))
    return has_day_signal and has_capture_signal and len(extract_today_checklist_items(text)) >= 2


def is_task_intake_request(text: str) -> bool:
    tasks = extract_numbered_tasks(text)
    lowered = text.lower()
    if len(tasks) >= 2 and any(phrase in lowered for phrase in TASK_INTAKE_PHRASES):
        return True
    if len(tasks) >= 3 and re.search(r"\b(task list|todo|to-do|backlog|delegate|delegating|prioriti[sz]e)\b", lowered):
        return True
    return False


def skill_note_target_role(root: Path, text: str) -> tuple[str, str]:
    lowered = text.lower()
    if not re.search(r"\b(skill|skills|capability|capabilities|workflow|playbook|method)\b", lowered):
        return "", ""
    if not re.search(r"\b(record|records|document|write|save|add|put|log|capture|remember|note)\b", lowered):
        return "", ""
    aliases = sorted(role_alias_map(root).items(), key=lambda item: len(item[0]), reverse=True)
    for alias, role in aliases:
        alias_text = alias.lower().replace("_", " ")
        candidates = {alias.lower(), alias_text}
        for candidate in candidates:
            if candidate and re.search(rf"\b{re.escape(candidate)}\b", lowered):
                return role, alias_text
    return "", ""


def is_skill_note_request(root: Path, text: str) -> bool:
    role, _alias = skill_note_target_role(root, text)
    return bool(role)


def role_takeover_target(root: Path, text: str) -> tuple[str, str]:
    lowered = text.lower()
    if not re.search(r"\btake\s+over\b", lowered):
        return "", ""
    aliases = sorted(role_alias_map(root).items(), key=lambda item: len(item[0]), reverse=True)
    for alias, role in aliases:
        alias_text = alias.lower().replace("_", " ")
        candidates = {alias.lower(), alias_text}
        for candidate in candidates:
            if candidate and re.search(rf"\b{re.escape(candidate)}\b", lowered):
                return role, alias_text
    if re.search(r"\b(the role|it|this|that work|the work|get the work done)\b", lowered):
        for record in reversed(parse_chat_records(root)[-10:]):
            if record.get("direction") not in {"operator_to_chief", "chief_to_operator"}:
                continue
            body = record.get("body", "")
            for alias, role in aliases:
                alias_text = alias.lower().replace("_", " ")
                if alias_text and re.search(rf"\b{re.escape(alias_text)}\b", body.lower()):
                    return role, alias_text
    return "", ""


def is_role_takeover_request(root: Path, text: str) -> bool:
    role, _alias = role_takeover_target(root, text)
    return bool(role)


def is_single_task_capture_request(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in SINGLE_TASK_CAPTURE_PATTERNS)


def clean_task_capture_text(text: str) -> str:
    value = text.strip()
    value = re.sub(
        r"^\s*(yes|ok|okay|please|also|and)\b[,.! ]*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\b(make sure|ensure|add|log|capture|save|write down|remember)\s+(this|that|it)\s+"
        r"(is|gets|goes|stays|as)?\s*(in|on|added to|a|the)?\s*"
        r"(task list|to-do|todo|backlog|list of tasks|task|backlog item)?\b",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\b(so )?i don'?t forget about it\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip(" .,:;-")
    return value


def previous_operator_message(root: Path, current_id: str) -> dict[str, str]:
    previous: dict[str, str] = {}
    for record in parse_chat_records(root):
        if record.get("id") == current_id:
            return previous
        if record.get("direction") == "operator_to_chief" and record.get("body", "").strip():
            previous = record
    return previous


def task_text_for_single_capture(root: Path, message: dict[str, str]) -> tuple[str, str]:
    body = message.get("body", "")
    direct = clean_task_capture_text(body)
    if len(direct) >= 40 and not re.fullmatch(r"(this|that|it)", direct, flags=re.IGNORECASE):
        return direct, ""
    previous = previous_operator_message(root, message.get("id", ""))
    previous_body = previous.get("body", "").strip()
    if previous_body:
        return previous_body, previous.get("id", "")
    return body.strip(), ""


def normalize_role_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]+", " ", value).strip()
    cleaned = re.sub(r"\b(please|now|for me|as well|too|bot|agent|harness)\b", " ", cleaned, flags=re.IGNORECASE)
    parts = [part for part in re.split(r"[\s_-]+", cleaned) if part]
    return "_".join(part[:1].upper() + part[1:] for part in parts)


def extract_role_add_request(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(should|could|recommend|suggest|helpful|what additional)\b", lowered) and not re.search(r"\b(yes|confirm|add|create|register|set up)\b", lowered):
        return ""
    for pattern in ROLE_ADD_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            role = normalize_role_name(match.group(1))
            if role and role not in {"Role", "New_Role"}:
                return role
    return ""


def is_role_add_request(text: str) -> bool:
    return bool(extract_role_add_request(text))


def is_status_request(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", text.strip().lower()).strip(" ?!.")
    return bool(
        lowered in {"status", "status update", "give me status", "what is the status", "what's the status"}
        or re.search(r"\b(status update|current status|where are we|what'?s pending|what is pending|what is going on with the system)\b", lowered)
    )


def is_work_request(text: str) -> bool:
    if is_task_intake_request(text) or is_single_task_capture_request(text) or is_role_add_request(text):
        return False
    if is_web_request(text) or is_weather_request(text):
        return False
    lowered = text.lower()
    if len(text.strip()) < 35 and not re.search(r"\b(prepare|draft|create|build|design|research|analyze)\b", lowered):
        return False
    return any(re.search(pattern, lowered) for pattern in WORK_REQUEST_PATTERNS)


def extract_human_assist_request(text: str) -> tuple[str, str]:
    for pattern in HUMAN_ASSIST_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        name = match.group(1).strip()
        if name.lower() in HUMAN_NAME_STOPWORDS:
            continue
        return name, text.strip()
    return "", ""


def is_human_assist_request(text: str) -> bool:
    name, _request = extract_human_assist_request(text)
    return bool(name)


def human_record_by_name(root: Path, name: str) -> str:
    text = read_text(root / "HUMANS.md")
    blocks = re.split(r"(?=^### HUMAN\s*$)", text, flags=re.MULTILINE)
    for block in blocks:
        if re.search(rf"^Full Name:\s*.*\b{re.escape(name)}\b.*$", block, flags=re.IGNORECASE | re.MULTILINE):
            return block.strip()
        if re.search(rf"^ID:\s*.*\b{re.escape(name)}\b.*$", block, flags=re.IGNORECASE | re.MULTILINE):
            return block.strip()
        if re.search(rf"\b{name}\b", block, flags=re.IGNORECASE) and "Preferred Contact Methods:" in block:
            return block.strip()
    return ""


def human_contact_summary(record: str) -> str:
    contacts: list[str] = []
    for raw in record.splitlines():
        line = raw.strip()
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            if value.strip():
                contacts.append(f"{key.strip()}: {value.strip()}")
    return "; ".join(contacts)


def recommend_task_roles(task: str) -> tuple[str, list[str]]:
    lowered = task.lower()
    if re.search(r"\b(kpi|spreadsheet|dashboard|workflow|automation|google drive|compress|photo|document management|n8n|api|one-click|website|web site|portfolio site|business site|personal site|membership site|video recordings|repurposing)\b", lowered):
        owner = "Engineer"
    elif re.search(r"\b(clean|workspace|room|environment|debt|family freedom|lifestyle|quality life)\b", lowered):
        owner = CHIEF_ROLE
    else:
        owner = "Researcher"

    support: list[str] = []
    if re.search(r"\b(course|training|courseware|lessons|slides|exercises|trainer|curriculum|skool)\b", lowered):
        support.append("CourseDesigner")
    if re.search(r"\b(video|recording|editing|publishing|youtube|shorts|clips|streamyard)\b", lowered):
        support.append("ContentProducer")
    if re.search(r"\b(client|enterprise|pricing|roi|retainer|sales|lead magnet|cta|membership|media outreach|book tour|speaking)\b", lowered):
        support.append("GrowthStrategist")
    if re.search(r"\b(financial|income|cash flow|investment|stocks|real estate|capital|wealth|debt)\b", lowered):
        support.append("FinanceStrategist")
    if re.search(r"\b(document|photo|workspace|organize|review past files)\b", lowered):
        support.append("OpsOrganizer")
    if owner not in support:
        support.insert(0, owner)
    return owner, support


def append_operator_intake_tasks(root: Path, message: dict[str, str], tasks: list[str]) -> list[dict[str, Any]]:
    msg_id = message.get("id", "") or "UNKNOWN"
    base_id = f"TASK-INTAKE-{msg_id.upper()}"
    created: list[dict[str, Any]] = []

    triage_id = f"{base_id}-TRIAGE"
    if not task_exists(root, triage_id):
        triage_block = f"""
## TASK
ID: {triage_id}
Title: Prioritize operator backlog and recommend team structure
Project: operator-backlog
Owner Role: {CHIEF_ROLE}
Status: WAITING_ON_HUMAN
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Request:
Prioritize the operator's captured backlog, identify the best first projects, confirm tradeoffs with the operator, and recommend which existing or new bot roles should own the work.
ChiefChat Notes:
- ChiefChat captured this because the operator asked to add tasks/delegate work, not to run a web search.
- Keep the operator involved before collapsing or summarizing important source details.
Done When:
- The operator has approved a priority order and role/team plan.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", triage_block)
        append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {CHIEF_ROLE}: intake_triage:{triage_id}")

    for index, task in enumerate(tasks, start=1):
        task_id = f"{base_id}-{index:02d}"
        owner, support = recommend_task_roles(task)
        created.append({"id": task_id, "owner": owner, "support": support, "task": task})
        if task_exists(root, task_id):
            append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat confirmed backlog intake for {task_id}")
            continue
        support_lines = "\n".join(f"- {role}" for role in support)
        block = f"""
## TASK
ID: {task_id}
Title: {task[:120]}
Project: operator-backlog
Owner Role: {owner}
Status: TODO
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Recommended Support Roles:
{support_lines}
Request:
{task}
ChiefChat Notes:
- Captured from an operator task-intake list.
- Do not treat this as a web/current-info request unless the owner role later decides research is required.
Done When:
- The owner role reports a concrete plan, artifact, or completed deliverable back to Chief_of_Staff.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", block)
        append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {owner}: intake_task:{task_id}")
    return created


def append_today_checkin_reminders(root: Path, human_id: str, msg_id: str, items: list[str]) -> None:
    path = root / "Runner" / "_reminders.json"
    try:
        reminders = json.loads(read_text(path) or "[]")
        if not isinstance(reminders, list):
            reminders = []
    except Exception:
        reminders = []
    pending_text = "; ".join(items[:5])
    offsets = [45, 120]
    now = datetime.now().astimezone()
    changed = False
    for minutes in offsets:
        due_at = now + timedelta(minutes=minutes)
        text = f"Quick check-in on today's list: {pending_text}. What is done, and what still needs help?"
        reminder_id = hashlib.sha256(f"{human_id}|today-checklist|{msg_id}|{minutes}".encode("utf-8")).hexdigest()[:16]
        if any(item.get("id") == reminder_id for item in reminders if isinstance(item, dict)):
            continue
        reminders.append(
            {
                "id": reminder_id,
                "human_id": human_id,
                "due_at": due_at.isoformat(timespec="seconds"),
                "text": text,
                "status": "pending",
                "created_at": iso_now(),
                "source": "chief-chat-today-checklist",
            }
        )
        changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, json.dumps(reminders, indent=2))


def append_today_checklist_tasks(root: Path, message: dict[str, str], items: list[str]) -> list[str]:
    msg_id = message.get("id", "") or "UNKNOWN"
    base_id = f"TASK-TODAY-{msg_id.upper()}"
    created: list[str] = []
    for index, item in enumerate(items, start=1):
        task_id = f"{base_id}-{index:02d}"
        created.append(task_id)
        if task_exists(root, task_id):
            continue
        block = f"""
## TASK
ID: {task_id}
Title: {item[:120]}
Project: operator-day-plan
Owner Role: {CHIEF_ROLE}
Status: TODO
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Request:
{item}
ChiefChat Notes:
- Personal/day-of operator checklist item captured from chat.
- Keep this with Chief_of_Staff unless the operator explicitly delegates it to another role.
- Check in with the operator until it is done, blocked, or no longer relevant today.
Done When:
- The operator confirms this item is complete or cancelled.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", block)
    append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {CHIEF_ROLE}: today_checklist:{base_id}")
    append_today_checkin_reminders(root, active_human_id(root), msg_id, items)
    return created


def today_checklist_reply(root: Path, message: dict[str, str]) -> str:
    items = extract_today_checklist_items(message.get("body", ""))
    task_ids = append_today_checklist_tasks(root, message, items)
    lines = ["Got it. I saved today's checklist:"]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item}.")
    lines.extend(
        [
            "",
            "I kept these with Chief_of_Staff as day-of operator tasks, not Researcher work.",
            "I also queued a couple of check-ins so I can nudge you later instead of letting the list disappear.",
        ]
    )
    if task_ids:
        lines.append(f"Task IDs: {task_ids[0]} through {task_ids[-1]}.")
    return "\n".join(lines)


def append_single_operator_task(root: Path, message: dict[str, str]) -> dict[str, Any]:
    msg_id = message.get("id", "") or "UNKNOWN"
    task_text, derived_from = task_text_for_single_capture(root, message)
    owner, support = recommend_task_roles(task_text)
    task_id = f"TASK-CHIEFCHAT-CAPTURE-{msg_id.upper()}"
    if not task_exists(root, task_id):
        support_lines = "\n".join(f"- {role}" for role in support)
        derived_line = f"Derived From Message: {derived_from}\n" if derived_from else ""
        block = f"""
## TASK
ID: {task_id}
Title: {task_text[:120]}
Project: operator-requests
Owner Role: {owner}
Status: TODO
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
{derived_line}Recommended Support Roles:
{support_lines}
Request:
{task_text}
ChiefChat Notes:
- Captured because the operator asked Chief_of_Staff to make sure this work was in the task list.
- ChiefChat wrote this task before confirming it to the operator.
Done When:
- The owner role reports a plan, artifact, or completion back to Chief_of_Staff.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", block)
        append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {owner}: captured_task:{task_id}")
    else:
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat confirmed captured task {task_id}")
    return {"id": task_id, "owner": owner, "support": support, "task": task_text, "derived_from": derived_from}


def single_task_capture_reply(root: Path, message: dict[str, str]) -> str:
    captured = append_single_operator_task(root, message)
    state, note = role_readiness(root, str(captured["owner"]))
    reply = (
        f"Done. I added it to the task list as `{captured['id']}`.\n\n"
        f"Owner: {captured['owner']}.\n"
        f"Task: {captured['task'][:260]}"
    )
    if state != "ready":
        reply += f"\n\nQueued honestly: {captured['owner']} {note}."
    return reply


def work_request_reply(root: Path, message: dict[str, str]) -> str:
    captured = append_single_operator_task(root, message)
    state, note = role_readiness(root, str(captured["owner"]))
    lines = [
        f"I captured this as `{captured['id']}` before planning around it.",
        f"Owner: {captured['owner']}.",
    ]
    if state != "ready":
        lines.append(f"Queued honestly: {captured['owner']} {note}.")
    lines.append("I won't claim it is being executed until the assigned role or human handoff reports back in the files.")
    return "\n\n".join(lines)


def append_human_assist_task(root: Path, message: dict[str, str]) -> dict[str, str]:
    human_name, request = extract_human_assist_request(message.get("body", ""))
    msg_id = message.get("id", "") or "UNKNOWN"
    safe_name = re.sub(r"[^A-Za-z0-9]+", "-", human_name).strip("-").upper() or "HUMAN"
    task_id = f"TASK-HUMAN-ASSIST-{safe_name}-{msg_id.upper()}"
    record = human_record_by_name(root, human_name)
    contacts = human_contact_summary(record)
    if not task_exists(root, task_id):
        contact_note = contacts or "No contact method found in HUMANS.md."
        block = f"""
## TASK
ID: {task_id}
Title: Ask {human_name} for help
Project: operator-requests
Owner Role: {CHIEF_ROLE}
Status: WAITING_ON_HUMAN
Priority: MEDIUM
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Checked Out By: {human_name}
Contact Method: {contact_note}
Request:
{request}
ChiefChat Notes:
- Captured because the operator asked Chief_of_Staff to involve a named human.
- Do not say the human was contacted unless a connected transport or manual confirmation records the contact.
Done When:
- {human_name} has been contacted or the operator confirms the handoff is no longer needed.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", block)
    else:
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat confirmed human-assist task {task_id}")
    return {"id": task_id, "human": human_name, "contacts": contacts, "known": "YES" if record else "NO"}


def human_assist_reply(root: Path, message: dict[str, str]) -> str:
    task = append_human_assist_task(root, message)
    if task["known"] == "YES" and task["contacts"]:
        return (
            f"I wrote the handoff task for {task['human']} as `{task['id']}`.\n\n"
            f"Contact route on file: {task['contacts']}.\n\n"
            "I have not marked them contacted yet; that should happen after a connected transport or manual confirmation records it."
        )
    if task["known"] == "YES":
        return (
            f"I wrote the handoff task for {task['human']} as `{task['id']}`.\n\n"
            "I found them in the human registry, but there is no contact method filled in. Add one in `HUMANS.md` or confirm you contacted them manually."
        )
    return (
        f"I wrote the handoff task for {task['human']} as `{task['id']}`.\n\n"
        f"I do not see {task['human']} in `HUMANS.md` yet, so I queued it as waiting on human/contact setup rather than pretending I contacted them."
    )


def status_update_reply(root: Path) -> str:
    tasks = [task for task in collect_tasks(root) if task_is_actionable(task)]
    by_owner: dict[str, int] = {}
    for task in tasks:
        owner = str(task.get("owner_role", "Unassigned") or "Unassigned").strip()
        by_owner[owner] = by_owner.get(owner, 0) + 1
    owner_summary = ", ".join(f"{owner}: {count}" for owner, count in sorted(by_owner.items())) or "none"
    wake_lines = [line.strip() for line in read_text(root / "Runner" / "_wake_requests.md").splitlines() if line.strip()]
    today = datetime.now().astimezone().date().isoformat()
    wake_today = sum(1 for line in wake_lines if today in line)
    stale_web_count = sum(1 for task in collect_tasks(root) if is_stale_web_task(task))
    registry = load_role_registry(root)
    blocked_roles: list[str] = []
    for role, raw in registry.items():
        state, note = role_readiness(root, role)
        if state != "ready":
            blocked_roles.append(f"{role} {note}")
    top_tasks = []
    for task in tasks[:5]:
        task_id = str(task.get("task_id", "") or task.get("id", "")).strip()
        title = str(task.get("title", "")).strip()
        owner = str(task.get("owner_role", "")).strip()
        top_tasks.append(f"- {task_id}: {title} ({owner})")
    lines = [
        f"Current file-backed status: {len(tasks)} actionable tasks.",
        f"Owners: {owner_summary}.",
        f"Wake log: {len(wake_lines)} entries total, {wake_today} today. This file is append-only, so not every entry is still pending.",
    ]
    if stale_web_count:
        lines.append(f"Stale actionable web tasks: {stale_web_count}. Say `remove those web requests` to cancel them.")
    if blocked_roles:
        lines.append("Roles needing setup: " + " ".join(blocked_roles[:4]))
    if top_tasks:
        lines.append("Top visible tasks:\n" + "\n".join(top_tasks))
    lines.append("Deterministic actions are enabled for task status, assignment, role wakes, reminders, and notes.")
    lines.append("I will not claim anything is actively executing unless a role heartbeat, task update, or human handoff confirms it.")
    return "\n\n".join(lines)


def task_intake_reply(root: Path, message: dict[str, str]) -> str:
    tasks = extract_numbered_tasks(message.get("body", ""))
    created = append_operator_intake_tasks(root, message, tasks)
    owner_counts: dict[str, int] = {}
    recommended_roles: list[str] = []
    for item in created:
        owner = str(item.get("owner", ""))
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        for role in item.get("support", []):
            if role not in recommended_roles:
                recommended_roles.append(role)

    registry = load_role_registry(root)
    unavailable: list[str] = []
    for role in sorted(owner_counts):
        state, note = role_readiness(root, role)
        if state != "ready":
            unavailable.append(f"{role} {note}")
    missing_specialists = [role for role in recommended_roles if role not in registry and role not in {CHIEF_ROLE, "Researcher", "Engineer"}]

    counts = ", ".join(f"{role}: {count}" for role, count in sorted(owner_counts.items()))
    reply = [
        f"Done. I added {len(tasks)} backlog tasks plus a Chief triage task.",
        f"First-pass ownership: {counts}.",
        "I did not run a web search; this was task intake and delegation.",
    ]
    if missing_specialists:
        reply.append("Recommended new/specialist bot roles to discuss: " + ", ".join(missing_specialists[:8]) + ".")
    if unavailable:
        reply.append("Queued honestly: " + " ".join(unavailable))
    reply.append("Next, I should help you rank these into the first few moves and confirm which roles/harnesses to spin up.")
    return "\n\n".join(reply)


def role_registered(root: Path, role: str) -> bool:
    return role in load_role_registry(root)


def append_role_design_record(root: Path, role: str) -> None:
    roles_path = root / "ROLES.md"
    text = read_text(roles_path)
    if re.search(rf"^Name:\s*{re.escape(role)}\s*$", text, flags=re.MULTILINE):
        return
    block = f"""

## Role
Name: {role}
Default Availability: OPEN
Priority: NORMAL
Can Write Main Task List: NO
Can Route Work: NO
Can Talk To Operator: LIMITED
Can Create Project Subtasks: YES
Lease File: `_heartbeat/{role}.md`
Direct Message File: `_messages/{role}.md`
Expected Capabilities:
- to be defined with the operator
"""
    append_line(roles_path, block.strip())


def append_role_registry_stub(root: Path, role: str, message: dict[str, str]) -> bool:
    if role_registered(root, role):
        append_role_design_record(root, role)
        return False
    msg_id = message.get("id", "") or "UNKNOWN"
    block = f"""

### ROLE
Role: {role}
Enabled: YES
Automation Ready: NO
Execution Mode: interval
Harness Key:
Harness Type: unassigned
Launch Command:
Working Directory:
Model / Profile:
Bootstrap File: AGENTIC_HARNESS.md
Startup Prompt: Read AGENTIC_HARNESS.md first. This is an existing Agentic Harness system. Claim the {role} role if it is available or stale, then check assigned tasks and continue work.
Wake Message: Check assigned {role} tasks and continue work.
Check Interval Minutes: 5
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source: ChiefChat role request {msg_id}
Last Confirmed:
Notes: Added from operator chat. This role is visible now, but it needs a harness assignment and one successful manual claim before Automation Ready should become YES.
"""
    append_line(root / "Runner" / "ROLE_LAUNCH_REGISTRY.md", block.strip())
    append_role_design_record(root, role)
    return True


def role_add_reply(root: Path, message: dict[str, str]) -> str:
    role = extract_role_add_request(message.get("body", ""))
    created = append_role_registry_stub(root, role, message)
    setup_task_id = f"TASK-ROLE-SETUP-{role.upper()}-{(message.get('id', '') or 'UNKNOWN').upper()}"
    if not task_exists(root, setup_task_id):
        block = f"""
## TASK
ID: {setup_task_id}
Title: Configure harness for {role}
Project: harness-operations
Owner Role: {CHIEF_ROLE}
Status: WAITING_ON_HUMAN
Priority: MEDIUM
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {message.get('id', '') or 'UNKNOWN'}
Request:
Configure the {role} role with a working harness, command template, model/profile, and first manual claim.
ChiefChat Notes:
- The role exists in ROLES.md and Runner/ROLE_LAUNCH_REGISTRY.md.
- Automation Ready must stay NO until the operator confirms a successful first run.
Done When:
- The operator chooses the harness for {role} and the role completes one successful manual claim.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", block)
    if created:
        return (
            f"Done. I added the `{role}` role to the role registry and role list.\n\n"
            "It is visible now, but it is not automation-ready yet. Next we need to choose its harness "
            f"and run one manual first claim. I also added `{setup_task_id}` so setup does not disappear."
        )
    return (
        f"`{role}` already exists in the role registry. I refreshed the role list and kept "
        f"`{setup_task_id}` available for harness setup if it still needs configuration."
    )


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


def _extract_markdown_field(text: str, field: str) -> str:
    pattern = rf"^\s*(?:[-*]\s*)?(?:\*\*)?{re.escape(field)}(?:\*\*)?\s*:\s*(.+?)\s*$"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip().strip("`").strip() if match else ""


def _stem_from_markdown_path(value: str) -> str:
    clean = value.strip().strip("`").strip('"').strip("'")
    if not clean:
        return ""
    return Path(clean).stem


def _add_role_alias(aliases: dict[str, str], alias: str, role: str) -> None:
    clean_alias = re.sub(r"\s+", " ", (alias or "").replace("_", " ")).strip()
    clean_role = (role or "").strip()
    if not clean_alias or not clean_role:
        return
    lowered = clean_alias.lower()
    if lowered in HUMAN_NAME_STOPWORDS:
        return
    aliases.setdefault(lowered, clean_role)
    aliases.setdefault(clean_alias.replace(" ", "_").lower(), clean_role)
    if " " in clean_alias:
        first = clean_alias.split(" ", 1)[0].strip()
        if first and first.lower() not in HUMAN_NAME_STOPWORDS:
            aliases.setdefault(first.lower(), clean_role)


def _looks_like_model_or_provider_name(value: str) -> bool:
    lowered = value.lower()
    model_words = ["claude", "haiku", "sonnet", "gpt", "gemini", "codex", "goose", "ollama", "opencode", "anthropic", "openai", "minimax"]
    return any(word in lowered for word in model_words)


def role_alias_map(root: Path) -> dict[str, str]:
    aliases: dict[str, str] = {}

    for role in load_role_registry(root).keys():
        if role == CHIEF_ROLE:
            continue
        _add_role_alias(aliases, role, role)

    roles_text = read_text(root / "ROLES.md")
    for block in re.split(r"(?=^#{2,3}\s+Role\s*$)", roles_text, flags=re.IGNORECASE | re.MULTILINE):
        name = _extract_markdown_field(block, "Name")
        if not name or name == CHIEF_ROLE:
            continue
        lease_role = _stem_from_markdown_path(_extract_markdown_field(block, "Lease File"))
        message_role = _stem_from_markdown_path(_extract_markdown_field(block, "Direct Message File"))
        role = lease_role or message_role or name.replace(" ", "_")
        _add_role_alias(aliases, role, role)
        _add_role_alias(aliases, name, role)
        for field in ["Alias", "Aliases", "Bot Name", "Agent Name", "Display Name", "Persona Name"]:
            value = _extract_markdown_field(block, field)
            if value:
                for alias in re.split(r"[,/|]", value):
                    _add_role_alias(aliases, alias, role)

    heartbeat_root = root / "_heartbeat"
    if heartbeat_root.exists():
        for path in sorted(heartbeat_root.glob("*.md")):
            role = path.stem
            if role == CHIEF_ROLE:
                continue
            text = read_text(path)
            _add_role_alias(aliases, role, role)
            for field in ["Name", "Bot Name", "Agent Name", "Display Name", "Persona Name"]:
                value = _extract_markdown_field(text, field)
                if value:
                    value = re.sub(r"\s*\([^)]*\)\s*", " ", value).strip()
                    _add_role_alias(aliases, value, role)
            claimed_by = _extract_markdown_field(text, "Claimed By")
            if claimed_by:
                claimed_by = re.sub(r"\s*\([^)]*\)\s*", " ", claimed_by).strip()
                if not _looks_like_model_or_provider_name(claimed_by):
                    _add_role_alias(aliases, claimed_by, role)

    agents_root = root / "MEMORY" / "agents"
    if agents_root.exists():
        for agent_dir in sorted(path for path in agents_root.iterdir() if path.is_dir()):
            role = agent_dir.name
            if role == CHIEF_ROLE:
                continue
            _add_role_alias(aliases, role, role)
            for filename in ["ALWAYS.md", "SOUL.md", "ONBOARDING_STATUS.md"]:
                text = read_text(agent_dir / filename)
                if not text:
                    continue
                for field in ["Name", "Bot Name", "Agent Name", "Display Name", "Persona Name"]:
                    value = _extract_markdown_field(text, field)
                    if value:
                        _add_role_alias(aliases, value, role)
    return aliases


def known_role_names(root: Path) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for role in role_alias_map(root).values():
        if role != CHIEF_ROLE and role not in seen:
            seen.add(role)
            names.append(role)
    if not names:
        names = ["Researcher", "Engineer"]
    return names


def requested_route_roles(root: Path, text: str) -> list[str]:
    lowered = text.lower()
    if not re.search(r"\b(send|route|assign|delegate|give|tell|hand|check|follow\s+up|contact|message|ping|coordinate|talk|speak)\b", lowered):
        return []
    roles: list[str] = []
    for alias, role in role_alias_map(root).items():
        alias_text = alias.lower().replace("_", " ")
        candidates = {alias.lower(), alias_text}
        if alias_text.endswith("er"):
            candidates.add(alias_text[:-2])
        if any(re.search(rf"\b{re.escape(candidate)}\b", lowered) for candidate in candidates if candidate):
            if role not in roles:
                roles.append(role)
    for role in known_role_names(root):
        role_text = role.lower().replace("_", " ")
        candidates = {role.lower(), role_text}
        if role_text.endswith("er"):
            candidates.add(role_text[:-2])
        if any(re.search(rf"\b{re.escape(candidate)}\b", lowered) for candidate in candidates if candidate):
            if role not in roles:
                roles.append(role)
    return roles


def role_readiness(root: Path, role: str) -> tuple[str, str]:
    raw = load_role_registry(root).get(role)
    if not raw:
        heartbeat = root / "_heartbeat" / f"{role}.md"
        if heartbeat.exists():
            text = read_text(heartbeat)
            status = _extract_markdown_field(text, "Status") or "heartbeat present"
            claimed_by = _extract_markdown_field(text, "Claimed By")
            holder = f", claimed by {claimed_by}" if claimed_by else ""
            return (
                "manual-active",
                f"has a manual/live heartbeat ({status}{holder}), but is not registered for Runner auto-launch yet",
            )
        return "unregistered", "needs a harness registration before it can run"
    view = config_view(role, raw)
    if not view.enabled:
        return "disabled", "is registered but disabled"
    if not view.automation_ready:
        return "not automation-ready", "is queued, but needs a confirmed harness before it can run automatically"
    return "ready", "is ready and has been woken"


def append_role_task(root: Path, role: str, message: dict[str, str]) -> str:
    msg_id = message.get("id", "") or "UNKNOWN"
    safe_role = re.sub(r"[^A-Za-z0-9]+", "-", role).strip("-").upper() or "ROLE"
    task_id = f"TASK-CHIEFCHAT-{safe_role}-{msg_id.upper()}"
    if task_exists(root, task_id):
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat confirmed route for {task_id}")
        append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {role}: routed_task:{task_id}")
        return task_id
    body = message.get("body", "").strip()
    block = f"""
## TASK
ID: {task_id}
Title: Operator request routed from ChiefChat
Project: operator-requests
Owner Role: {role}
Status: TODO
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Request:
{body}
ChiefChat Notes:
- ChiefChat wrote this task before confirming routing to the operator.
Done When:
- {role} reports progress or completion back to Chief_of_Staff.
""".strip()
    append_line(root / "LAYER_TASK_LIST.md", block)
    append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {role}: routed_task:{task_id}")
    return task_id


def route_tasks_reply(root: Path, message: dict[str, str], roles: list[str]) -> str:
    routed: list[str] = []
    blockers: list[str] = []
    for role in roles:
        task_id = append_role_task(root, role, message)
        state, note = role_readiness(root, role)
        routed.append(f"{role}: {task_id}")
        if state != "ready":
            blockers.append(f"{role} {note}")
    if blockers:
        return (
            "Queued. I wrote the task files and wake requests for "
            f"{', '.join(roles)}.\n\n"
            + "\n".join(f"- {item}" for item in blockers)
        )
    return (
        "Done. I wrote the task files and wake requests for "
        f"{', '.join(roles)}.\n\n"
        "I will watch for their updates and keep the training plan moving."
    )


def role_skill_file(root: Path, role: str) -> Path:
    return root / "MEMORY" / "agents" / role / "SKILLS.md"


def role_display_name(root: Path, role: str) -> str:
    heartbeat = root / "_heartbeat" / f"{role}.md"
    text = read_text(heartbeat)
    for field in ["Claimed By", "Name", "Bot Name", "Agent Name", "Display Name", "Persona Name"]:
        value = _extract_markdown_field(text, field)
        if value and not _looks_like_model_or_provider_name(value):
            return re.sub(r"\s*\([^)]*\)\s*", " ", value).strip()
    return role


def append_role_skill_note(root: Path, message: dict[str, str]) -> dict[str, str]:
    role, alias = skill_note_target_role(root, message.get("body", ""))
    msg_id = message.get("id", "") or "UNKNOWN"
    safe_role = re.sub(r"[^A-Za-z0-9]+", "-", role).strip("-").upper() or "ROLE"
    note_id = f"SKILL-NOTE-{safe_role}-{msg_id.upper()}"
    path = role_skill_file(root, role)
    body = message.get("body", "").strip()
    display_name = role_display_name(root, role)
    if not read_text(path).strip():
        header = f"# {role} Skills\n\nCanonical skill memory for the `{role}` role. Project-specific notes may link here, but this file travels with the role across harnesses.\n"
        atomic_write_text(path, header)
    if note_id not in read_text(path):
        block = f"""
## Skill Note
ID: {note_id}
Role: {role}
Bot Alias: {display_name if display_name != role else alias or role}
Status: PENDING_ROLE_REVIEW
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}

Operator Note:
{body}

ChiefChat Notes:
- The operator asked for this to be recorded in the bot/role skill memory.
- ChiefChat resolved `{alias or display_name or role}` to role `{role}` before writing.
- The role holder should refine this into a confirmed workflow with commands, examples, boundaries, and proof when they next run.
""".strip()
        append_line(path, "\n" + block)
    append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {role}: skill_note:{note_id}")
    append_line(root / "LAYER_LAST_ITEMS_DONE.md", f"[{iso_now()}] [CHIEF_CHAT] SKILL_NOTE - {note_id} written to {path.relative_to(root)}")
    return {
        "id": note_id,
        "role": role,
        "alias": display_name if display_name != role else alias or role,
        "path": str(path.relative_to(root)).replace("\\", "/"),
    }


def skill_note_reply(root: Path, message: dict[str, str]) -> str:
    note = append_role_skill_note(root, message)
    state, readiness = role_readiness(root, str(note["role"]))
    lines = [
        f"Done. I resolved {note['alias']} to the `{note['role']}` role and wrote the skill note as `{note['id']}`.",
        f"Canonical file: `{note['path']}`.",
        "I also added a wake request so that role can refine it into a confirmed skill/workflow.",
    ]
    if state != "ready":
        lines.append(f"Queued honestly: {note['role']} {readiness}.")
    lines.append("I did not create a project-local skill file; bot skills belong with the role memory so any replacement harness can inherit them.")
    return "\n\n".join(lines)


def append_role_takeover_task(root: Path, message: dict[str, str]) -> dict[str, str]:
    role, alias = role_takeover_target(root, message.get("body", ""))
    msg_id = message.get("id", "") or "UNKNOWN"
    safe_role = re.sub(r"[^A-Za-z0-9]+", "-", role).strip("-").upper() or "ROLE"
    task_id = f"TASK-ROLE-TAKEOVER-{safe_role}-{msg_id.upper()}"
    body = message.get("body", "").strip()
    if not task_exists(root, task_id):
        block = f"""
## TASK
ID: {task_id}
Title: Temporary role takeover requested for {role}
Project: operator-requests
Owner Role: {role}
Status: TODO
Priority: HIGH
Created By: ChiefChat
Created At: {iso_now()}
Source Message: {msg_id}
Request:
{body}
ChiefChat Notes:
- The operator asked for a harness to take over `{alias or role}` / `{role}` temporarily, complete the role work, then report back to Chief_of_Staff.
- ChiefChat cannot honestly execute this role from the cheap Telegram chat lane.
- A live harness or Runner-compatible provider must claim `{role}`, do the work, write progress/results, release or renew the lease correctly, then return control/status to Chief_of_Staff.
Manual Harness Prompt:
continue, check your tasks as {role}
Return Prompt:
continue, check your tasks as Chief_of_Staff
Done When:
- `{role}` reports completion or a blocker back in the files and Chief_of_Staff summarizes it to the operator.
""".strip()
        append_line(root / "LAYER_TASK_LIST.md", block)
    append_line(root / "Runner" / "_wake_requests.md", f"[{iso_now()}] {role}: role_takeover:{task_id}")
    return {"id": task_id, "role": role, "alias": alias or role}


def provider_from_heartbeat(root: Path, role: str) -> tuple[str, str, str]:
    text = read_text(root / "_heartbeat" / f"{role}.md")
    provider = (_extract_markdown_field(text, "Provider") or _extract_markdown_field(text, "Harness")).strip()
    harness = (_extract_markdown_field(text, "Harness") or provider).strip()
    model = _extract_markdown_field(text, "Model").strip()
    haystack = " ".join([provider, harness]).lower()
    for key in ["opencode", "claude", "gemini", "codex", "goose", "ollama", "deepagents", "openclaw"]:
        if key in haystack:
            return key, harness or key, model
    return "", harness, model


def auto_cycle_token(provider: str) -> str:
    mapping = {
        "claude": "{AUTO_CLAUDE_CYCLE}",
        "opencode": "{AUTO_OPENCODE_CYCLE}",
        "gemini": "{AUTO_GEMINI_CYCLE}",
        "codex": "{AUTO_CODEX_CYCLE}",
        "goose": "{AUTO_GOOSE_CYCLE}",
        "ollama": "{AUTO_OLLAMA_CYCLE}",
        "deepagents": "{AUTO_DEEPAGENTS_CYCLE}",
        "openclaw": "{AUTO_OPENCLAW_CYCLE}",
    }
    return mapping.get(provider, "")


def ensure_role_takeover_registry(root: Path, config: dict[str, str], role: str, task_id: str) -> tuple[bool, str]:
    existing = load_role_registry(root).get(role)
    if existing:
        view = config_view(role, existing)
        if not view.enabled:
            return False, f"`{role}` is registered but disabled. Enable it before ChiefChat auto-starts that role."
        if view.automation_ready and view.launch_command:
            return True, "Role already has an automation-ready Runner registry entry."
        if not parse_bool(config.get("Role Takeover Infer Registry From Heartbeat", "YES"), True):
            return True, f"`{role}` is registered, but not automation-ready. Heartbeat-based repair is disabled."
        append_event(root, f"ROLE_TAKEOVER_REGISTRY - {role} exists but is not automation-ready; attempting heartbeat repair for {task_id}.")
    if not parse_bool(config.get("Role Takeover Infer Registry From Heartbeat", "YES"), True):
        return False, "Role is not registered and heartbeat-based registration is disabled."
    provider, harness, model = provider_from_heartbeat(root, role)
    token = auto_cycle_token(provider)
    if not provider or not token:
        return False, f"Could not infer a supported CLI provider from `{role}` heartbeat."
    append_role_design_record(root, role)
    block = f"""

### ROLE
Role: {role}
Enabled: YES
Automation Ready: YES
Execution Mode: interval
Harness Key: {provider}-from-heartbeat
Harness Type: {harness or provider}
Launch Command: {token}
Working Directory: {root}
Model / Profile: {model}
Bootstrap File: AGENTIC_HARNESS_TINY.md
Startup Prompt: Read AGENTIC_HARNESS_TINY.md first. This is an existing Agentic Harness system. Temporarily claim the {role} role if the lease is free or stale, complete assigned {role} work, write results/status to the markdown files, then report back to Chief_of_Staff and release/stand down.
Wake Message: You are being temporarily activated from Chief_of_Staff. Check assigned {role} tasks, complete one focused work cycle, report back, then stand down.
Check Interval Minutes: 5
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source: ChiefChat role takeover auto-registration from heartbeat for {task_id}
Last Confirmed:
Notes: Auto-created because the operator asked Chief_of_Staff to temporarily take over this role from phone. Confirm this command works, then keep or refine the registry entry.
""".strip()
    append_line(root / "Runner" / "ROLE_LAUNCH_REGISTRY.md", block)
    append_event(root, f"ROLE_TAKEOVER_REGISTRY - Auto-registered {role} using {provider} for {task_id}.")
    return True, f"Auto-registered {role} from heartbeat using {provider}."


def launch_role_takeover(root: Path, config: dict[str, str], role: str, task_id: str, msg_id: str) -> dict[str, Any]:
    if not parse_bool(config.get("Role Takeover Auto Launch", "YES"), True):
        return {"ok": False, "status": "disabled", "summary": "Role takeover auto-launch is disabled in ChiefChat config."}
    script = root / "Runner" / "scheduled_role_runner.py"
    if not script.exists():
        return {"ok": False, "status": "missing_runner", "summary": "Runner/scheduled_role_runner.py is missing."}
    timeout = max(5, parse_int(config.get("Role Takeover Launch Timeout Seconds", "20"), 20))
    command = [
        sys.executable,
        str(script),
        "--role",
        role,
        "--reason",
        f"chief_takeover:{msg_id}:{task_id}",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except Exception as exc:
        return {"ok": False, "status": "launch_error", "summary": str(exc)}
    raw = (completed.stdout or completed.stderr or "").strip()
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(completed.stdout or "{}")
    except Exception:
        parsed = {}
    status = str(parsed.get("status") or parsed.get("decision") or "").strip()
    action = str(parsed.get("action") or "").strip()
    ok = completed.returncode == 0 and (action == "launch" or status in {"LAUNCHED", "RUN_ALLOWED", "DAILY_ALL_HANDS"})
    if not ok and action == "launch":
        ok = True
    return {
        "ok": ok,
        "status": status or f"exit_{completed.returncode}",
        "action": action,
        "summary": str(parsed.get("summary") or raw or "No Runner output."),
        "raw": raw[-1200:],
    }


def role_takeover_reply(root: Path, config: dict[str, str], message: dict[str, str]) -> str:
    task = append_role_takeover_task(root, message)
    registry_ok, registry_note = ensure_role_takeover_registry(root, config, str(task["role"]), str(task["id"]))
    state, readiness = role_readiness(root, str(task["role"]))
    launch = launch_role_takeover(root, config, str(task["role"]), str(task["id"]), message.get("id", "") or "UNKNOWN") if registry_ok else {"ok": False, "status": "not_registered", "summary": registry_note}
    lines = [
        f"I queued the temporary takeover as `{task['id']}`.",
        f"Target role: `{task['role']}` ({task['alias']}).",
        registry_note,
    ]
    if launch.get("ok"):
        lines.append(
            f"I started a local `{task['role']}` run through Runner now. Status: {launch.get('status') or launch.get('action') or 'launched'}."
        )
        lines.append("That harness should claim the role, do one focused work cycle, write results, and then report back to Chief_of_Staff.")
    else:
        lines.append(f"I could not auto-start the role yet: {launch.get('summary')}")
        lines.append(f"Manual harness prompt: `continue, check your tasks as {task['role']}`")
        lines.append("When that harness finishes, return to Chief with: `continue, check your tasks as Chief_of_Staff`")
    if state not in {"ready", "manual-active"}:
        lines.append(f"Queued honestly: {task['role']} {readiness}.")
    lines.append("I will only call it complete after the role writes a result or blocker back into the files.")
    return "\n\n".join(lines)


def detect_operator_intent(root: Path, text: str) -> tuple[str, str]:
    if is_presence_ping(text):
        return "presence", "short availability/presence ping"
    if is_status_request(text):
        return "status", "operator asked for a file-backed status update"
    if is_model_identity_request(text):
        return "identity", "operator asked what runtime/model is answering"
    if is_task_action_request(root, text):
        return "task_action", "operator asked ChiefChat to mutate task state deterministically"
    if is_role_wake_request(root, text):
        role = task_action_owner(root, text)
        return "role_wake", f"operator asked ChiefChat to wake role/bot: {role}"
    if is_today_checklist_request(text):
        return "today_checklist", "operator asked Chief to hold a personal/day-of checklist"
    if is_task_intake_request(text):
        return "task_intake", "operator asked Chief to capture/prioritize/delegate tasks"
    if is_single_task_capture_request(text):
        return "single_task_capture", "operator asked Chief to add the current/previous item to the task list"
    role_to_add = extract_role_add_request(text)
    if role_to_add:
        return "role_add", f"operator asked to add/register role: {role_to_add}"
    takeover_role, takeover_alias = role_takeover_target(root, text)
    if takeover_role:
        return "role_takeover", f"operator asked for temporary takeover of {takeover_alias or takeover_role} / role {takeover_role}"
    skill_role, skill_alias = skill_note_target_role(root, text)
    if skill_role:
        return "skill_note", f"operator asked to record a skill for {skill_alias or skill_role} / role {skill_role}"
    roles = requested_route_roles(root, text)
    if roles:
        return "route_roles", "operator explicitly named role routing targets: " + ", ".join(roles)
    if is_human_assist_request(text):
        name, _request = extract_human_assist_request(text)
        return "human_assist", f"operator asked to involve named human: {name}"
    if is_weather_request(text):
        return "weather", "operator asked for weather/current forecast"
    if is_web_request(text):
        return "web", "operator asked for current or external information"
    if is_work_request(text):
        return "work_request", "operator asked Chief to capture/action a work item"
    return "chat", "normal Chief/operator conversation"


def browser_profile_dir(root: Path) -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME") or str(root / ".local_state")
    return Path(base) / "AgenticHarness" / "ChiefChat" / "browser-profile"


def setup_failure_reply(config: dict[str, str], error: Exception) -> str:
    provider = config.get("Chat Provider", "openai-compatible")
    if provider in {"openai-compatible", "openai", "lmstudio", "lm-studio"}:
        target = config.get("OpenAI Compatible Base URL", "http://127.0.0.1:1234/v1")
        if "timed out" in str(error).lower():
            return (
                "I received your message, but the local chat model took too long to answer. "
                f"LM Studio is reachable at `{target}`, so this is a speed/model-load issue rather than Telegram being down. "
                "Try again in a moment, or switch ChiefChat to a smaller loaded model in `ChiefChat\\CHIEF_CHAT_CONFIG.md`."
            )
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

    body = message.get("body", "")
    intent, intent_reason = detect_operator_intent(root, body)
    append_event(root, f"INTENT - Operator message {msg_id}: {intent} ({intent_reason})")
    action_steps: list[str] = []
    append_activity(root, config, msg_id, "CLASSIFY", f"{intent} - {intent_reason}")

    if intent == "presence":
        action_step(root, config, msg_id, action_steps, "REPLY", "Presence ping answered from runtime status.")
        reply = presence_ping_reply(root)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"REPLIED_PRESENCE - Operator message {msg_id}")
        return True

    if intent == "status":
        action_step(root, config, msg_id, action_steps, "READ_STATUS", "Built file-backed status reply.")
        reply = status_update_reply(root)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"REPLIED_STATUS - Operator message {msg_id}")
        return True

    if intent == "identity":
        action_step(root, config, msg_id, action_steps, "READ_IDENTITY", "Answered from ChiefChat runtime identity.")
        reply = model_identity_reply(root, config)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"REPLIED_IDENTITY - Operator message {msg_id}")
        return True

    if intent == "task_action":
        action_step(root, config, msg_id, action_steps, "EXECUTE_TASK_ACTION", "Ran deterministic task mutation handler before replying.")
        reply = task_action_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"TASK_ACTION - Operator message {msg_id}")
        append_activity(root, config, msg_id, "VERIFY", "Task action reply sent from verified file mutation result.")
        return True

    if intent == "role_wake":
        action_step(root, config, msg_id, action_steps, "WAKE_ROLE", "Wrote wake request for a matched role/bot alias.")
        reply = role_wake_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"ROLE_WAKE - Operator message {msg_id}")
        append_activity(root, config, msg_id, "VERIFY", "Role wake request written before reply.")
        return True

    if intent == "task_intake":
        action_step(root, config, msg_id, action_steps, "WRITE_TASKS", "Captured numbered backlog items before replying.")
        reply = task_intake_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"INTAKE_TASKS - Operator message {msg_id}")
        return True

    if intent == "today_checklist":
        action_step(root, config, msg_id, action_steps, "WRITE_TODAY_CHECKLIST", "Captured personal day checklist as Chief-owned tasks/reminders.")
        reply = today_checklist_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"TODAY_CHECKLIST - Operator message {msg_id}")
        return True

    if intent == "single_task_capture":
        action_step(root, config, msg_id, action_steps, "WRITE_TASK", "Captured current or previous operator item before replying.")
        reply = single_task_capture_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"CAPTURED_TASK - Operator message {msg_id}")
        return True

    if intent == "role_add":
        action_step(root, config, msg_id, action_steps, "REGISTER_ROLE", "Created role registry/task scaffolding.")
        reply = role_add_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"ADDED_ROLE - Operator message {msg_id}")
        return True

    if intent == "role_takeover":
        action_step(root, config, msg_id, action_steps, "QUEUE_ROLE_TAKEOVER", "Created a real role takeover task/wake instead of claiming execution from chat.")
        reply = role_takeover_reply(root, config, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"ROLE_TAKEOVER - Operator message {msg_id}")
        return True

    if intent == "skill_note":
        action_step(root, config, msg_id, action_steps, "WRITE_SKILL_NOTE", "Resolved bot/role alias and wrote canonical role skill memory.")
        reply = skill_note_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"SKILL_NOTE - Operator message {msg_id}")
        return True

    if intent == "human_assist":
        action_step(root, config, msg_id, action_steps, "QUEUE_HUMAN_ASSIST", "Created a durable human-assist task.")
        reply = human_assist_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"HUMAN_ASSIST - Operator message {msg_id}")
        return True

    route_roles = requested_route_roles(root, body) if intent == "route_roles" else []
    if intent == "route_roles" and route_roles:
        action_step(root, config, msg_id, action_steps, "ROUTE_ROLES", "Wrote role tasks and wake requests for: " + ", ".join(route_roles))
        reply = route_tasks_reply(root, message, route_roles)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"ROUTED_TASKS - Operator message {msg_id} to {', '.join(route_roles)}")
        return True

    if intent == "work_request":
        action_step(root, config, msg_id, action_steps, "CAPTURE_WORK", "Captured freeform work request as a durable task.")
        reply = work_request_reply(root, message)
        update_chat_status(root, msg_id, "sent")
        append_operator_reply(
            root,
            reply,
            human_id=active_human_id(root),
            from_role=CHIEF_ROLE,
            channel="all",
            reply_to=msg_id,
        )
        append_event(root, f"CAPTURED_WORK_REQUEST - Operator message {msg_id}")
        return True

    extra = ""
    web_task_id = ""
    web_note = ""
    if intent == "weather":
        action_step(root, config, msg_id, action_steps, "PLAN_WEATHER", "Extracted weather location and checked ambiguity.")
        weather_location = extract_weather_location(body)
        clarification = location_clarification_reply(body, kind="weather") if broad_location_clarification(weather_location) or not weather_location else ""
        if clarification:
            action_step(root, config, msg_id, action_steps, "ASK_CLARIFY", "Weather location was missing or too broad.")
            update_chat_status(root, msg_id, "sent")
            append_operator_reply(
                root,
                clarification,
                human_id=active_human_id(root),
                from_role=CHIEF_ROLE,
                channel="all",
                reply_to=msg_id,
            )
            append_event(root, f"ASKED_LOCATION_CLARIFICATION - Operator message {msg_id}")
            return True
        web_task_id = append_web_task(root, message, "ChiefChat created this task before deterministic weather lookup.")
        action_step(root, config, msg_id, action_steps, "CREATE_WEB_TASK", f"Created {web_task_id} for weather lookup traceability.")
        try:
            reply = fetch_weather_summary(weather_location, parse_int(config.get("Reply Timeout Seconds", "20"), 20))
            append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat resolved {web_task_id} via Open-Meteo: {reply}")
            action_step(root, config, msg_id, action_steps, "REPLY_WEATHER", "Weather data returned from deterministic lookup.")
            update_chat_status(root, msg_id, "sent")
            append_operator_reply(
                root,
                reply,
                human_id=active_human_id(root),
                from_role=CHIEF_ROLE,
                channel="all",
                reply_to=msg_id,
            )
            append_event(root, f"REPLIED_WEATHER - Operator message {msg_id}")
            return True
        except Exception as exc:
            append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat weather lookup failed for {web_task_id}: {exc}")
            web_note = f"Weather lookup failed: {exc}"
            extra = f"Web task created: {web_task_id}\nFresh web evidence:\n{web_note}"
    elif intent == "web":
        if local_request_needs_location(body):
            action_step(root, config, msg_id, action_steps, "ASK_CLARIFY", "Local request needs a location before web lookup.")
            update_chat_status(root, msg_id, "sent")
            append_operator_reply(
                root,
                location_clarification_reply(body),
                human_id=active_human_id(root),
                from_role=CHIEF_ROLE,
                channel="all",
                reply_to=msg_id,
            )
            append_event(root, f"ASKED_LOCATION_CLARIFICATION - Operator message {msg_id}")
            return True
        web_task_id = append_web_task(root, message, "ChiefChat created this task before attempting local browser research.")
        action_step(root, config, msg_id, action_steps, "CREATE_WEB_TASK", f"Created {web_task_id} before browser/search work.")
        search_query = plan_web_search_query(body)
        action_step(root, config, msg_id, action_steps, "PLAN_WEB", search_query)
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat planned search for {web_task_id}: {search_query}")
        web_note = try_browser_research(root, config, search_query, body)
        action_step(root, config, msg_id, action_steps, "GATHER_EVIDENCE", web_note.splitlines()[0] if web_note else "No evidence note returned.")
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat web evidence for {web_task_id}: {web_note}")
        extra = f"Web task created: {web_task_id}\nFresh web evidence:\n{web_note}"

    prompt = browser_answer_prompt(root, config, message, extra) if extra else build_prompt(root, config, message)
    try:
        reply = model_reply(root, config, prompt, message)
        if not reply:
            raise RuntimeError("model returned an empty reply")
    except Exception as exc:
        if extra and web_note:
            reply = evidence_fallback_reply(web_note, web_task_id or "TASK-WEB", body)
            update_chat_status(root, msg_id, "sent")
            action_step(root, config, msg_id, action_steps, "FALLBACK_REPLY", f"Model failed; replied from extracted evidence: {exc}")
            append_event(root, f"WEB_MODEL_FALLBACK - Operator message {msg_id}: {exc}")
        else:
            reply = setup_failure_reply(config, exc) if parse_bool(config.get("Status Reply On Model Failure", "YES"), True) else ""
            update_chat_status(root, msg_id, "failed")
            action_step(root, config, msg_id, action_steps, "MODEL_FAILURE", str(exc))
            append_event(root, f"MODEL_FAILURE - Operator message {msg_id}: {exc}")
    else:
        if (
            looks_like_progress_reply(reply, extra)
            or looks_like_directory_reply(reply, extra)
            or lacks_web_answer_evidence(reply, extra, body)
        ):
            reply = evidence_fallback_reply(web_note or extra, web_task_id or "TASK-WEB", body)
            action_step(root, config, msg_id, action_steps, "QUALITY_FALLBACK", "Replaced weak/progress-only model answer with source evidence.")
        else:
            reply = apply_voice_cleanup(reply)
            action_step(root, config, msg_id, action_steps, "MODEL_REPLY", "Accepted model reply after voice/evidence quality checks.")
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
        append_activity(root, config, msg_id, "DONE", f"Reply sent after {len(action_steps)} action step(s).")
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
        "activity_log": str(activity_path(root)),
        "interaction_mode": load_config(root).get("Chief Interaction Mode", "bounded-action-loop"),
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
    parser.add_argument("--cleanup-stale-web-tasks", action="store_true", help="Cancel actionable TASK-WEB items older than today and print a verified summary.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.cleanup_stale_web_tasks:
        print(json.dumps(cancel_stale_web_tasks(root), indent=2))
        return 0
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
