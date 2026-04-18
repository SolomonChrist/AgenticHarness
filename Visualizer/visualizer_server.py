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
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
VIS_ROOT = Path(__file__).resolve().parent


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


def collect_roles() -> List[str]:
    roles: List[str] = []
    roles_text = read_text(ROOT / "ROLES.md")
    for raw in roles_text.splitlines():
        line = raw.strip()
        if line.startswith("Name:"):
            role = line.split(":", 1)[1].strip()
            if role:
                roles.append(role)
    return roles


def collect_lease_state() -> List[Dict[str, object]]:
    now = datetime.now().astimezone()
    leases: List[Dict[str, object]] = []
    for role in collect_roles():
        path = ROOT / "_heartbeat" / f"{role}.md"
        row = {
            "role": role,
            "exists": path.exists(),
            "status": "unclaimed",
            "claimed_by": "",
            "task": "",
            "project": "",
            "last_renewal": "",
            "lease_expires_at": "",
        }
        if path.exists():
            data = parse_markdown_table(path)
            expiry = parse_iso(data.get("Lease Expires At", ""))
            active = (data.get("Status", "") or "").upper() == "ACTIVE"
            stale = bool(expiry and expiry < now)
            row.update(
                {
                    "claimed_by": data.get("Claimed By", ""),
                    "task": data.get("Current Task", ""),
                    "project": data.get("Current Project", ""),
                    "last_renewal": data.get("Last Renewal", ""),
                    "lease_expires_at": data.get("Lease Expires At", ""),
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
    current: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Task ID:"):
            if current:
                items.append(current)
            current = {"task_id": line.split(":", 1)[1].strip()}
        elif current and ":" in line:
            key, value = line.split(":", 1)
            norm = key.strip().lower().replace(" ", "_")
            current[norm] = value.strip()
    if current:
        items.append(current)
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
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "roles": leases,
        "tasks": collect_task_summary(),
        "task_items": collect_task_items(),
        "projects": collect_projects(),
        "recent_events": tail_lines(ROOT / "LAYER_LAST_ITEMS_DONE.md", limit=25),
        "recent_context": tail_lines(ROOT / "LAYER_SHARED_TEAM_CONTEXT.md", limit=15),
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

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> int:
    port = int(os.environ.get("AH_VIS_PORT", "8787"))
    server = ThreadingHTTPServer(("127.0.0.1", port), VisualizerHandler)
    print(f"Agentic Harness Visualizer running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
