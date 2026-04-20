#!/usr/bin/env python3
"""
Agentic Harness Visualizer server.

Serves a lightweight local visualizer and exposes live markdown-driven state
through a simple JSON API without adding external dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
VIS_ROOT = Path(__file__).resolve().parent
RUNNER_ROOT = ROOT / "Runner"
TELEGRAM_ROOT = ROOT / "TelegramBot"
VIS_RUNTIME_FILE = VIS_ROOT / ".visualizer_runtime.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordination_io import append_line, atomic_write_text
from control_actions import maybe_handle_control_message
from message_filters import clean_operator_reply


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def parse_markdown_table(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("|") and line.endswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0] not in {"Field", "---"}:
                data[parts[0]] = parts[1]
        elif ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            if key.strip():
                data[key.strip()] = value.strip()
    return data


def parse_markdown_records(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    records: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    current_list_key: Optional[str] = None

    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("### ROLE"):
            if current:
                records.append(current)
            current = {"_type": "role"}
            current_list_key = None
            continue
        if stripped.startswith("### HUMAN RUNNER"):
            if current:
                records.append(current)
            current = {"_type": "human"}
            current_list_key = None
            continue
        if stripped.startswith("### HARNESS"):
            if current:
                records.append(current)
            current = {"_type": "harness"}
            current_list_key = None
            continue
        if current is None:
            continue
        if not stripped:
            current_list_key = None
            continue
        if stripped.startswith("- "):
            if current_list_key:
                current.setdefault(current_list_key, [])
                assert isinstance(current[current_list_key], list)
                current[current_list_key].append(stripped[2:].strip())
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                current[key] = value
                current_list_key = None
            else:
                current[key] = []
                current_list_key = key
    if current:
        records.append(current)
    return records


def markdown_scalar(value: object) -> str:
    if isinstance(value, list):
        return ""
    return str(value or "").strip()


def parse_iso(value: str) -> Optional[datetime]:
    text = (value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        return None


def parse_registry_roles_from_layer_config() -> List[str]:
    roles: List[str] = []
    for raw in read_text(ROOT / "LAYER_CONFIG.md").splitlines():
        line = raw.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        role = parts[0]
        if role in {"Role", "---"} or not role:
            continue
        roles.append(role)
    return roles


def collect_roles() -> List[str]:
    seen = set()
    roles: List[str] = []

    def add(role: str) -> None:
        clean = role.strip()
        if not clean or clean in seen:
            return
        seen.add(clean)
        roles.append(clean)

    roles_text = read_text(ROOT / "ROLES.md")
    for raw in roles_text.splitlines():
        line = raw.strip()
        if line.startswith("Name:"):
            add(line.split(":", 1)[1].strip())

    for record in parse_markdown_records(RUNNER_ROOT / "ROLE_LAUNCH_REGISTRY.md"):
        if record.get("_type") == "role":
            add(str(record.get("Role", "")))

    for role in parse_registry_roles_from_layer_config():
        add(role)

    heartbeat_root = ROOT / "_heartbeat"
    if heartbeat_root.exists():
        for path in sorted(heartbeat_root.glob("*.md")):
            add(path.stem)

    return roles


def collect_role_registry() -> Dict[str, Dict[str, object]]:
    registry: Dict[str, Dict[str, object]] = {}
    for record in parse_markdown_records(RUNNER_ROOT / "ROLE_LAUNCH_REGISTRY.md"):
        if record.get("_type") != "role":
            continue
        role = str(record.get("Role", "")).strip()
        if not role:
            continue
        registry[role] = {
            "enabled": markdown_scalar(record.get("Enabled", "")),
            "automation_ready": markdown_scalar(record.get("Automation Ready", "")),
            "execution_mode": markdown_scalar(record.get("Execution Mode", "")).lower(),
            "harness_key": markdown_scalar(record.get("Harness Key", "")),
            "harness_type": markdown_scalar(record.get("Harness Type", "")),
            "launch_command": markdown_scalar(record.get("Launch Command", "")),
            "model_profile": markdown_scalar(record.get("Model / Profile", "")),
            "wake_message": markdown_scalar(record.get("Wake Message", "")),
            "last_confirmed": markdown_scalar(record.get("Last Confirmed", "")),
            "notes": markdown_scalar(record.get("Notes", "")),
        }
    return registry


def load_json(path: Path) -> Dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_json_list(path: Path) -> List[Dict[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def wake_queue_state() -> Dict[str, object]:
    wake_file = RUNNER_ROOT / "_wake_requests.md"
    state_file = RUNNER_ROOT / ".runner_state.json"
    lines = [line.strip() for line in read_text(wake_file).splitlines() if line.strip()]
    seen = set(load_json(state_file).get("wake_requests_seen", []))
    pending = [line for line in lines if line not in seen]
    return {
        "total": len(lines),
        "pending": len(pending),
        "last_request": pending[-1] if pending else (lines[-1] if lines else ""),
    }


def reminder_queue_state() -> Dict[str, object]:
    reminders = load_json_list(RUNNER_ROOT / "_reminders.json")
    pending = [item for item in reminders if str(item.get("status", "")).lower() == "pending"]
    pending.sort(key=lambda item: str(item.get("due_at", "")))
    return {
        "total": len(reminders),
        "pending": len(pending),
        "next_due_at": str(pending[0].get("due_at", "")) if pending else "",
        "next_text": str(pending[0].get("text", "")) if pending else "",
    }


def collect_daemon_statuses() -> Dict[str, Dict[str, object]]:
    daemons = {
        "runner": load_json(RUNNER_ROOT / ".runner_runtime.json"),
        "telegram": load_json(TELEGRAM_ROOT / "data" / "runtime.json"),
        "visualizer": load_json(VIS_RUNTIME_FILE),
    }
    for key, value in daemons.items():
        if not value:
            daemons[key] = {"component": key, "status": "inactive"}
    daemons["wake_queue"] = wake_queue_state()
    daemons["reminder_queue"] = reminder_queue_state()
    return daemons


def active_human_id() -> str:
    humans = read_text(ROOT / "HUMANS.md")
    match = re.search(r"^ID:[ \t]*(.+)$", humans, flags=re.MULTILINE)
    return match.group(1).strip() if match else "operator"


def write_operator_message(message: str, source: str = "visualizer") -> None:
    human_id = active_human_id()
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    append_line(ROOT / "_messages" / "Chief_of_Staff.md", f"[{ts}] [{source}] [{human_id}] {message}")
    append_line(RUNNER_ROOT / "_wake_requests.md", f"[{ts}] Chief_of_Staff: operator_message")
    append_line(ROOT / "LAYER_LAST_ITEMS_DONE.md", f"[{ts}] [VISUALIZER_CHAT] NOTIFY - Operator message routed to Chief_of_Staff")


def write_human_reply(message: str) -> None:
    human_id = active_human_id()
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    append_line(ROOT / "_messages" / f"human_{human_id}.md", f"[{ts}] [Chief_of_Staff] {message}")


def clean_chat_line(line: str) -> str:
    text = line.strip()
    match = re.match(r"^\[[^\]]+\]\s+\[[^\]]+\]\s+(?:\[[^\]]+\]\s+)?(.*)$", text)
    return match.group(1).strip() if match else text


def chat_timestamp(line: str) -> str:
    match = re.match(r"^\[([^\]]+)\]", line.strip())
    return match.group(1) if match else ""


def collect_operator_chat(limit: int = 30) -> List[Dict[str, str]]:
    human_id = active_human_id()
    items: List[Dict[str, str]] = []
    for raw in read_text(ROOT / "_messages" / "Chief_of_Staff.md").splitlines():
        if f"[{human_id}]" in raw:
            items.append({"from": "operator", "text": clean_chat_line(raw), "timestamp": chat_timestamp(raw)})
    current: List[str] = []
    current_timestamp = ""
    for raw in read_text(ROOT / "_messages" / f"human_{human_id}.md").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"^\[[^\]]+\]\s+\[[^\]]+\]", line):
            if current:
                text = clean_operator_reply("\n".join(current).strip())
                if text:
                    items.append({"from": "chief", "text": text, "timestamp": current_timestamp})
            current = [clean_chat_line(line)]
            current_timestamp = chat_timestamp(line)
        elif current:
            current.append(line)
        else:
            current = [line]
            current_timestamp = ""
    if current:
        text = clean_operator_reply("\n".join(current).strip())
        if text:
            items.append({"from": "chief", "text": text, "timestamp": current_timestamp})
    items.sort(key=lambda item: item.get("timestamp", ""))
    return items[-limit:]


def collect_lease_state() -> List[Dict[str, object]]:
    now = datetime.now().astimezone()
    registry = collect_role_registry()
    leases: List[Dict[str, object]] = []
    for role in collect_roles():
        path = ROOT / "_heartbeat" / f"{role}.md"
        reg = registry.get(role, {})
        row = {
            "role": role,
            "exists": path.exists(),
            "status": "unclaimed",
            "claimed_by": "",
            "task": "",
            "project": "",
            "last_renewal": "",
            "lease_expires_at": "",
            "automation_mode": reg.get("execution_mode", "") or "unregistered",
            "registered_enabled": reg.get("enabled", ""),
            "automation_ready": reg.get("automation_ready", ""),
            "registered_harness_type": reg.get("harness_type", ""),
            "registered_harness_key": reg.get("harness_key", ""),
            "registered_model_profile": reg.get("model_profile", ""),
            "registered_launch_command": reg.get("launch_command", ""),
            "bot_name": "",
            "harness_name": reg.get("harness_type", "") or reg.get("harness_key", ""),
            "provider_name": reg.get("harness_type", ""),
            "model_name": reg.get("model_profile", ""),
        }
        if path.exists():
            data = parse_markdown_table(path)
            expiry = parse_iso(data.get("Lease Expires At", ""))
            active = (data.get("Status", "") or "").upper() == "ACTIVE"
            stale = bool(expiry and expiry < now)
            file_fresh = False
            try:
                modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
                file_fresh = (now - modified_at).total_seconds() <= 600
            except Exception:
                modified_at = None
            # Some harnesses may write a fresh heartbeat file but leave an incorrect
            # absolute timestamp format behind. For visualization purposes, treat a
            # recently updated ACTIVE heartbeat as active even if the embedded expiry
            # appears stale.
            if active and stale and file_fresh:
                stale = False
            row.update(
                {
                    "claimed_by": data.get("Claimed By", ""),
                    "task": data.get("Current Task", ""),
                    "project": data.get("Current Project", ""),
                    "last_renewal": data.get("Last Renewal", ""),
                    "lease_expires_at": data.get("Lease Expires At", ""),
                    "heartbeat_modified_at": modified_at.isoformat(timespec="seconds") if modified_at else "",
                    "actual_harness": data.get("Harness", ""),
                    "actual_provider": data.get("Provider", ""),
                    "actual_model": data.get("Model", ""),
                    "bot_name": data.get("Claimed By", ""),
                    "harness_name": data.get("Harness", "") or reg.get("harness_type", "") or reg.get("harness_key", ""),
                    "provider_name": data.get("Provider", "") or reg.get("harness_type", ""),
                    "model_name": data.get("Model", "") or reg.get("model_profile", ""),
                    "status": "stale" if stale else "active" if active else "unknown",
                }
            )
        leases.append(row)
    return leases


def collect_task_summary() -> Dict[str, int]:
    text = read_text(ROOT / "LAYER_TASK_LIST.md")
    summary = {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0, "waiting_human": 0}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Status:"):
            status = line.split(":", 1)[1].strip().upper()
            if status == "TODO":
                summary["todo"] += 1
            elif status == "IN_PROGRESS":
                summary["in_progress"] += 1
            elif status == "DONE":
                summary["done"] += 1
            elif status == "BLOCKED":
                summary["blocked"] += 1
            elif status in {"WAITING_ON_HUMAN", "HUMAN_CHECKOUT"}:
                summary["waiting_human"] += 1
    return summary


def collect_task_items() -> List[Dict[str, str]]:
    text = read_text(ROOT / "LAYER_TASK_LIST.md")
    items: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## TASK":
            if current:
                items.append(current)
            current = {}
            continue
        if current is None:
            continue
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        norm = key.strip().lower().replace(" ", "_")
        current[norm] = value.strip()
    if current:
        items.append(current)
    for item in items:
        if "task_id" not in item and "id" in item:
            item["task_id"] = item["id"]
    return items


def tail_lines(path: Path, limit: int = 20) -> List[str]:
    lines = read_text(path).splitlines()
    return lines[-limit:]


def collect_projects() -> List[Dict[str, str]]:
    task_items = collect_task_items()
    projects: List[Dict[str, str]] = []
    projects_root = ROOT / "Projects"
    if not projects_root.exists():
        return projects
    for child in sorted(projects_root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        related = [item for item in task_items if item.get("project", "").strip() == child.name]
        summary = {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0}
        for item in related:
            status = item.get("status", "").upper()
            if status == "TODO":
                summary["todo"] += 1
            elif status == "IN_PROGRESS":
                summary["in_progress"] += 1
            elif status == "DONE":
                summary["done"] += 1
            elif status == "BLOCKED":
                summary["blocked"] += 1
        project_text = read_text(child / "PROJECT.md")
        title_match = re.search(r"^#\s+(.+)$", project_text, re.MULTILINE)
        projects.append(
            {
                "slug": child.name,
                "has_project": str((child / "PROJECT.md").exists()).lower(),
                "has_tasks": str((child / "TASKS.md").exists()).lower(),
                "has_context": str((child / "CONTEXT.md").exists()).lower(),
                "title": title_match.group(1).strip() if title_match else child.name,
                "task_summary": summary,
            }
        )
    return projects


def build_state() -> Dict[str, object]:
    leases = collect_lease_state()
    daemons = collect_daemon_statuses()
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "roles": leases,
        "tasks": collect_task_summary(),
        "task_items": collect_task_items(),
        "projects": collect_projects(),
        "daemons": daemons,
        "recent_events": tail_lines(ROOT / "LAYER_LAST_ITEMS_DONE.md", limit=25),
        "recent_context": tail_lines(ROOT / "LAYER_SHARED_TEAM_CONTEXT.md", limit=15),
        "operator_chat": collect_operator_chat(),
    }


class VisualizerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIS_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            payload = json.dumps(build_state()).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if parsed.path == "/":
            self.path = "/world2d.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(min(length, 65536))
            payload = json.loads(body.decode("utf-8"))
            message = str(payload.get("message", "")).strip()
        except Exception:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON body")
            return
        if not message:
            self.send_error(HTTPStatus.BAD_REQUEST, "Message cannot be empty")
            return
        write_operator_message(message)
        control_reply = maybe_handle_control_message(message)
        quick_reply = control_reply
        if quick_reply:
            write_human_reply(quick_reply)
        response = json.dumps({"ok": True, "handled": bool(quick_reply)}).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, fmt: str, *args) -> None:
        return


def update_runtime() -> None:
    payload = {
        "component": "visualizer",
        "status": "active",
        "pid": os.getpid(),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    atomic_write_text(VIS_RUNTIME_FILE, json.dumps(payload, indent=2))


def main() -> int:
    port = int(os.environ.get("AH_VIS_PORT", "8787"))
    update_runtime()
    server = ThreadingHTTPServer(("127.0.0.1", port), VisualizerHandler)
    print(f"Agentic Harness Visualizer running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        atomic_write_text(
            VIS_RUNTIME_FILE,
            json.dumps(
                {
                    "component": "visualizer",
                    "status": "stopped",
                    "pid": os.getpid(),
                    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                },
                indent=2,
            ),
        )
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
