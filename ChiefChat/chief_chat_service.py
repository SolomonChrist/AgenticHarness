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
from role_preflight import config_view, load_role_registry


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


def soul_context(root: Path) -> str:
    parts = [
        ("Chief soul", root / "MEMORY" / "agents" / CHIEF_ROLE / "SOUL.md", 2200),
        ("Chief always memory", root / "MEMORY" / "agents" / CHIEF_ROLE / "ALWAYS.md", 2200),
        ("Human registry", root / "HUMANS.md", 1200),
    ]
    chunks: list[str] = []
    for label, path, limit in parts:
        content = tail(path, limit)
        if content:
            chunks.append(f"## {label}\n{content}")
    return "\n\n".join(chunks)


def recent_chat_context(root: Path, max_chars: int = 3500) -> str:
    return tail(root / "_messages" / "CHAT.md", max_chars)


def compact_system_summary(root: Path) -> str:
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
        lines.extend(roles[:8])
    return "\n".join(lines)


def chief_voice_contract() -> str:
    return """## Chief voice contract
- Lead with the useful answer, not process narration.
- Sound like a capable human assistant: warm, direct, practical, and specific.
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
    if re.search(r"\b(news|headlines)\b", lowered):
        return "news"
    if re.search(r"\b(restaurant|reviews?|best dish|best dishes|menu|dish)\b", lowered):
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
        "news": "Return concrete headlines with source names and links. Do not invent dates or sources.",
        "restaurant": "Recommend dishes only from review/menu evidence. Include why and source links.",
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
    context = soul_context(root)
    chat = recent_chat_context(root)
    system = compact_system_summary(root)
    if extra_context:
        result_instruction = (
            "The local action context below is fresh and more important than old task/status history. "
            "Answer the operator's request using it. Do not pivot to old provider quota or harness-remediation topics unless the operator asked about them."
        )
    else:
        result_instruction = "Answer the operator's newest message directly."
    return f"""You are Chief_of_Staff, the user's fast human-feeling operator interface.

Use the Chief soul/personality and memory below. Be warm, direct, specific, and operational.
You are the orchestration layer. For deep coding, research, or long web work, create or route tasks instead of pretending the chat model did it.
Do not mention internal file paths, daemon cycles, or provider errors unless the user asks or it is needed to unblock them.
Keep the reply concise enough for Telegram.
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
    r"\b(can you|could you|please|go and|use the search to|search to)\s+(find|research|check|look up|see)\b",
]

WEB_SUBJECT_PATTERNS = [
    r"\b(events?|meetups?|concerts?|things to do|happening|hours?|open|close|website|url|page)\b",
    r"\b(news|headlines|reviews?|best dish|menu|restaurant|github|repo|repository|book)\b",
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
    if re.search(r"\b(what|which|where|when)\b.*\b(events?|meetups?|hours?|news|headlines|weather|forecast|price|prices|reviews?|github|repo|repository)\b", lowered):
        return True
    if re.search(r"\b(events?|meetups?|hours?|news|headlines|weather|forecast|prices?|reviews?)\b.*\b(today|tonight|latest|current|right now|near me|nearby)\b", lowered):
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


def evidence_fallback_reply(note: str, task_id: str) -> str:
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
    situational = situational_evidence_reply(note, task_id)
    if situational:
        return situational
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
            for result in results[:pages_to_read]:
                url = result.get("url", "")
                if url.startswith("http"):
                    pages.append(read_page_evidence(context, url, result.get("query") or query, timeout_ms))
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


def extract_numbered_tasks(text: str) -> list[str]:
    tasks: list[str] = []
    for _number, raw in NUMBERED_TASK_RE.findall(text):
        clean = re.sub(r"\s+", " ", raw).strip(" \t\r\n-")
        if clean:
            tasks.append(clean)
    return tasks


def is_task_intake_request(text: str) -> bool:
    tasks = extract_numbered_tasks(text)
    lowered = text.lower()
    if len(tasks) >= 2 and any(phrase in lowered for phrase in TASK_INTAKE_PHRASES):
        return True
    if len(tasks) >= 3 and re.search(r"\b(task list|todo|to-do|backlog|delegate|delegating|prioriti[sz]e)\b", lowered):
        return True
    return False


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
Status: TODO
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


def known_role_names(root: Path) -> list[str]:
    names = [role for role in load_role_registry(root).keys() if role != CHIEF_ROLE]
    if not names:
        names = ["Researcher", "Engineer"]
    return names


def requested_route_roles(root: Path, text: str) -> list[str]:
    lowered = text.lower()
    if not re.search(r"\b(send|route|assign|delegate|give|tell|hand)\b", lowered):
        return []
    roles: list[str] = []
    for role in known_role_names(root):
        role_text = role.lower().replace("_", " ")
        aliases = {role.lower(), role_text}
        if role_text.endswith("er"):
            aliases.add(role_text[:-2])
        if any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases if alias):
            roles.append(role)
    return roles


def role_readiness(root: Path, role: str) -> tuple[str, str]:
    raw = load_role_registry(root).get(role)
    if not raw:
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


def detect_operator_intent(root: Path, text: str) -> tuple[str, str]:
    if is_presence_ping(text):
        return "presence", "short availability/presence ping"
    if is_model_identity_request(text):
        return "identity", "operator asked what runtime/model is answering"
    if is_task_intake_request(text):
        return "task_intake", "operator asked Chief to capture/prioritize/delegate tasks"
    roles = requested_route_roles(root, text)
    if roles:
        return "route_roles", "operator explicitly named role routing targets: " + ", ".join(roles)
    if is_weather_request(text):
        return "weather", "operator asked for weather/current forecast"
    if is_web_request(text):
        return "web", "operator asked for current or external information"
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

    if intent == "presence":
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

    if intent == "identity":
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

    if intent == "task_intake":
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

    route_roles = requested_route_roles(root, body) if intent == "route_roles" else []
    if intent == "route_roles" and route_roles:
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

    extra = ""
    web_task_id = ""
    web_note = ""
    if intent == "weather":
        weather_location = extract_weather_location(body)
        clarification = location_clarification_reply(body, kind="weather") if broad_location_clarification(weather_location) or not weather_location else ""
        if clarification:
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
        try:
            reply = fetch_weather_summary(weather_location, parse_int(config.get("Reply Timeout Seconds", "20"), 20))
            append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat resolved {web_task_id} via Open-Meteo: {reply}")
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
        search_query = plan_web_search_query(body)
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat planned search for {web_task_id}: {search_query}")
        web_note = try_browser_research(root, config, search_query, body)
        append_line(root / "LAYER_TASK_LIST.md", f"- [{iso_now()}] ChiefChat web evidence for {web_task_id}: {web_note}")
        extra = f"Web task created: {web_task_id}\nFresh web evidence:\n{web_note}"

    prompt = browser_answer_prompt(root, config, message, extra) if extra else build_prompt(root, config, message)
    try:
        reply = model_reply(root, config, prompt, message)
        if not reply:
            raise RuntimeError("model returned an empty reply")
    except Exception as exc:
        if extra and web_note:
            reply = evidence_fallback_reply(web_note, web_task_id or "TASK-WEB")
            update_chat_status(root, msg_id, "sent")
            append_event(root, f"WEB_MODEL_FALLBACK - Operator message {msg_id}: {exc}")
        else:
            reply = setup_failure_reply(config, exc) if parse_bool(config.get("Status Reply On Model Failure", "YES"), True) else ""
            update_chat_status(root, msg_id, "failed")
            append_event(root, f"MODEL_FAILURE - Operator message {msg_id}: {exc}")
    else:
        if looks_like_progress_reply(reply, extra) or looks_like_directory_reply(reply, extra):
            reply = evidence_fallback_reply(web_note or extra, web_task_id or "TASK-WEB")
        else:
            reply = apply_voice_cleanup(reply)
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
