#!/usr/bin/env python3
"""Human-channel reply filters for Telegram and Visualizer.

Daemon cycles are allowed to write operational notes to logs, but the human
chat surfaces should only show intentional operator-facing replies.
"""

from __future__ import annotations

import re


INTERNAL_START_PATTERNS = [
    r"^\s*not logged in\s*[·\.\-:]",
    r"^\s*please run\s*/login\b",
    r"^\s*\*?\*?daemon cycle\b",
    r"^\s*\*?\*?cycle summary\b",
    r"^\s*\*?\*?cycle complete\b",
    r"^\s*\*?\*?automation checkpoint\b",
    r"^\s*\*?\*?automation cycle checkpoint\b",
    r"^\s*\*?\*?fresh cycle\b",
    r"^\s*\*?\*?lease renewed\b",
    r"^\s*\*?\*?no new operator messages\b",
    r"^\s*\*?\*?system idle/standby\b",
    r"^\s*\*?\*?exiting\b",
]

INTERNAL_TAIL_MARKERS = [
    "\n**Daemon cycle",
    "\nDaemon cycle",
    "\n**Cycle summary",
    "\nCycle summary",
    "\n**Cycle Summary",
    "\nCycle Summary",
    "\n**Cycle Complete",
    "\nCycle Complete",
    "\n**Automation checkpoint",
    "\nAutomation checkpoint",
    "\n**Automation cycle checkpoint",
    "\nAutomation cycle checkpoint",
    "\nLease renewed",
    "\nExiting daemon cycle",
]


def repair_mojibake(text: str) -> str:
    if not any(marker in text for marker in ("Ã¢", "Ã°Å¸", "Ãƒ")):
        return text
    try:
        repaired = text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if repaired.count("ï¿½") <= text.count("ï¿½") else text


def repair_mojibake(text: str) -> str:
    replacements = {
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "Â·": "·",
        "â˜•": "",
        "Ã©": "é",
        "Ä“": "ē",
    }
    repaired = text
    for bad, good in replacements.items():
        repaired = repaired.replace(bad, good)
    if any(marker in repaired for marker in ("ÃƒÂ¢", "ÃƒÂ°Ã…Â¸", "ÃƒÆ’")):
        try:
            repaired = repaired.encode("cp1252").decode("utf-8")
        except UnicodeError:
            pass
    return repaired if repaired.count("Ã¯Â¿Â½") <= text.count("Ã¯Â¿Â½") else text


def strip_internal_tail(text: str) -> str:
    cut_at: int | None = None
    lower = text.lower()
    for marker in INTERNAL_TAIL_MARKERS:
        index = lower.find(marker.lower())
        if index > 0 and (cut_at is None or index < cut_at):
            cut_at = index
    if cut_at is not None:
        text = text[:cut_at]
    return text.strip()


def is_internal_only(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    for pattern in INTERNAL_START_PATTERNS:
        if re.search(pattern, stripped, flags=re.IGNORECASE):
            return True
    operational_markers = [
        "no new operator messages",
        "lease renewed",
        "exiting daemon cycle",
        "task-0002",
        "awaiting researcher",
        "awaiting specialist",
        "system idle/standby",
    ]
    lowered = stripped.lower()
    if any(marker in lowered for marker in operational_markers):
        if not any(phrase in lowered for phrase in ("you asked", "here's", "what's running", "status on")):
            return True
    return False


def clean_operator_reply(text: str) -> str:
    lines: list[str] = []
    for raw in (text or "").strip().splitlines():
        line = raw.rstrip()
        if line.strip() in {"---", "```"}:
            continue
        lines.append(line)
    cleaned = repair_mojibake("\n".join(lines).strip())
    cleaned = re.sub(r"^\s*Reply to operator:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = strip_internal_tail(cleaned)
    if is_internal_only(cleaned):
        return ""
    return cleaned
