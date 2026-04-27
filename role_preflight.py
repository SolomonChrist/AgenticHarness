#!/usr/bin/env python3
"""Cheap local role-run preflight checks for Agentic Harness.

This module is intentionally file-first and provider-agnostic. It reads the
markdown control plane, runner state, and local task/message surfaces to decide
whether a role runner should spend inference at all.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping


ACTIONABLE_STATUSES = {"TODO", "IN_PROGRESS", "ACTIVE", "OPEN", "READY"}
NON_ACTIONABLE_STATUSES = {"DONE", "CANCELLED", "CANCELED", "BLOCKED", "WAITING_ON_HUMAN", "HUMAN_CHECKOUT"}
CHIEF_ROLE = "Chief_of_Staff"


@dataclass(frozen=True)
class RoleConfigView:
    role: str
    enabled: bool
    automation_ready: bool
    execution_mode: str
    harness_key: str
    harness_type: str
    launch_command: str
    working_directory: str
    model_profile: str
    bootstrap_file: str


def now_local() -> datetime:
    return datetime.now().astimezone()


def iso_now() -> str:
    return now_local().isoformat(timespec="seconds")


def parse_bool(value: Any, default: bool = False) -> bool:
    text = str(value or "").strip().upper()
    if text in {"YES", "TRUE", "1", "ON", "ACTIVE", "ENABLED"}:
        return True
    if text in {"NO", "FALSE", "0", "OFF", "DISABLED"}:
        return False
    return default


def parse_float(value: Any, default: float) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        return None


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return default


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def parse_key_values(path: Path) -> dict[str, str]:
    """Parse heartbeat/config style files in table, plain, or bullet form."""
    data: dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("|") and line.endswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 2 and parts[0] and parts[0] not in {"Field", "---"}:
                data[parts[0]] = parts[1]
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key:
            data[key] = value.strip()
    return data


def parse_markdown_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = read_text(path)
    if path.name == "ROLE_LAUNCH_REGISTRY.md" and "## Active Registrations" in text:
        text = text.split("## Active Registrations", 1)[1]
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None
    for raw in text.splitlines():
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
                if isinstance(current[current_list_key], list):
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


def markdown_scalar(value: Any) -> str:
    if isinstance(value, list):
        return ""
    return str(value or "").strip()


def role_record_ready(record: Mapping[str, Any]) -> bool:
    return parse_bool(record.get("Enabled", "")) or parse_bool(record.get("Automation Ready", ""))


def load_role_registry(root: Path) -> dict[str, dict[str, Any]]:
    by_role: dict[str, dict[str, Any]] = {}
    for record in parse_markdown_records(root / "Runner" / "ROLE_LAUNCH_REGISTRY.md"):
        if record.get("_type") != "role":
            continue
        role = markdown_scalar(record.get("Role", ""))
        if not role:
            continue
        existing = by_role.get(role)
        if existing is None or (role_record_ready(record) and not role_record_ready(existing)):
            by_role[role] = dict(record)
    return by_role


def collect_role_names(root: Path) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []

    def add(role: str) -> None:
        clean = role.strip()
        if clean and clean not in seen:
            seen.add(clean)
            names.append(clean)

    for raw in read_text(root / "ROLES.md").splitlines():
        line = raw.strip()
        if line.startswith("Name:"):
            add(line.split(":", 1)[1].strip())
    for role in load_role_registry(root):
        add(role)
    heartbeat_root = root / "_heartbeat"
    if heartbeat_root.exists():
        for path in sorted(heartbeat_root.glob("*.md")):
            add(path.stem)
    return names


def config_view(role: str, raw: Any) -> RoleConfigView:
    def get(name: str, default: Any = "") -> Any:
        if isinstance(raw, Mapping):
            return raw.get(name, default)
        attr = name.lower().replace(" / ", "_").replace(" ", "_")
        return getattr(raw, attr, default)

    return RoleConfigView(
        role=role,
        enabled=parse_bool(get("Enabled", get("enabled", ""))),
        automation_ready=parse_bool(get("Automation Ready", get("automation_ready", ""))),
        execution_mode=markdown_scalar(get("Execution Mode", get("execution_mode", "interval"))).lower() or "interval",
        harness_key=markdown_scalar(get("Harness Key", get("harness_key", ""))),
        harness_type=markdown_scalar(get("Harness Type", get("harness_type", ""))),
        launch_command=markdown_scalar(get("Launch Command", get("launch_command", ""))),
        working_directory=markdown_scalar(get("Working Directory", get("working_directory", ""))),
        model_profile=markdown_scalar(get("Model / Profile", get("model_profile", ""))),
        bootstrap_file=markdown_scalar(get("Bootstrap File", get("bootstrap_file", ""))),
    )


def read_lease(root: Path, role: str) -> dict[str, Any]:
    path = root / "_heartbeat" / f"{role}.md"
    data = parse_key_values(path)
    expiry = parse_iso(data.get("Lease Expires At", ""))
    status = data.get("Status", "").upper()
    stale = bool(expiry and expiry < now_local())
    active = status == "ACTIVE" and not stale
    return {
        "role": role,
        "exists": path.exists(),
        "status": "active" if active else "stale" if stale else "unclaimed" if not path.exists() else status.lower() or "unknown",
        "active": active,
        "stale": stale,
        "lease_expires_at": expiry.isoformat(timespec="seconds") if expiry else "",
        "claimed_by": data.get("Claimed By", ""),
        "task": data.get("Current Task", ""),
        "project": data.get("Current Project", ""),
        "last_renewal": data.get("Last Renewal", ""),
        "harness": data.get("Harness", ""),
        "provider": data.get("Provider", ""),
        "model": data.get("Model", ""),
    }


def task_paths(root: Path) -> list[Path]:
    paths = [root / "LAYER_TASK_LIST.md"]
    projects_root = root / "Projects"
    if projects_root.exists():
        paths.extend(sorted(projects_root.glob("*/TASKS.md")))
    return paths


def parse_task_file(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## TASK":
            if current:
                items.append(current)
            current = {"source_file": str(path)}
            continue
        if current is None or not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        current[key.strip().lower().replace(" ", "_")] = value.strip()
    if current:
        items.append(current)
    for item in items:
        if "task_id" not in item and "id" in item:
            item["task_id"] = item["id"]
        if "project" not in item and path.name == "TASKS.md":
            item["project"] = path.parent.name
    return items


def collect_tasks(root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for path in task_paths(root):
        items.extend(parse_task_file(path))
    return items


def task_is_actionable(task: Mapping[str, str]) -> bool:
    status = str(task.get("status", "")).strip().upper()
    if not status:
        return False
    if status in NON_ACTIONABLE_STATUSES:
        return False
    return status in ACTIONABLE_STATUSES


def tasks_for_role(root: Path, role: str) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for task in collect_tasks(root):
        owner = str(task.get("owner_role", "")).strip()
        if owner == role and task_is_actionable(task):
            matches.append(task)
    return matches


def file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def message_changed(root: Path, state: Mapping[str, Any], role: str) -> bool:
    path = root / "_messages" / f"{role}.md"
    mtime = file_mtime(path)
    if not mtime:
        return False
    files = state.get("files", {}) if isinstance(state.get("files", {}), Mapping) else {}
    last = float(files.get(f"message::{role}", 0.0) or 0.0)
    return mtime > last


def pending_wake_requests(root: Path, state: Mapping[str, Any], role: str) -> list[str]:
    wake_file = root / "Runner" / "_wake_requests.md"
    lines = [line.strip() for line in read_text(wake_file).splitlines() if line.strip()]
    seen = set(state.get("wake_requests_seen", [])) if isinstance(state.get("wake_requests_seen", []), list) else set()
    reasons: list[str] = []
    for line in lines:
        if line in seen:
            continue
        tail = line.split("]", 1)[1].strip() if "]" in line else line
        if ":" in tail:
            target, reason = tail.split(":", 1)
            if target.strip() == role:
                reasons.append(reason.strip() or "wake_request")
        elif tail.strip() == role:
            reasons.append("wake_request")
    return reasons


def role_state(state: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    roles = state.get("roles", {})
    if isinstance(roles, Mapping):
        found = roles.get(role, {})
        if isinstance(found, Mapping):
            return found
    return {}


def cooldown_state(state: Mapping[str, Any], role: str) -> dict[str, Any]:
    current = role_state(state, role)
    now = now_local()
    result: dict[str, Any] = {
        "provider_active": False,
        "provider_until": "",
        "stale_active": False,
        "stale_until": "",
        "launch_active": False,
        "launch_until": "",
        "last_error": str(current.get("last_launch_error", "")),
    }
    for source_key, output_prefix in [
        ("provider_cooldown_until", "provider"),
        ("stale_lease_cooldown_until", "stale"),
        ("cooldown_until", "launch"),
    ]:
        until = parse_iso(current.get(source_key, ""))
        if until:
            result[f"{output_prefix}_until"] = until.isoformat(timespec="seconds")
            result[f"{output_prefix}_active"] = until > now
    return result


def is_cheap_chief_config(role: str, cfg: RoleConfigView) -> bool:
    if role != CHIEF_ROLE:
        return False
    text = " ".join([cfg.harness_key, cfg.harness_type, cfg.launch_command]).lower()
    return "cheap-chief" in text or "chiefchat" in text or "cheap_chief_router" in text


def daily_all_hands_due(runner_cfg: Mapping[str, Any], state: Mapping[str, Any], role: str) -> bool:
    if not parse_bool(runner_cfg.get("Daily All Hands Enabled", "YES"), True):
        return False
    interval_hours = max(1.0, parse_float(runner_cfg.get("Daily All Hands Interval Hours", "24"), 24.0))
    last_at = parse_iso(role_state(state, role).get("last_daily_all_hands_at", ""))
    return last_at is None or now_local() >= last_at + timedelta(hours=interval_hours)


def scheduled_command(root: Path, role: str) -> str:
    python_cmd = "py" if os.name == "nt" else "python3"
    script = root / "Runner" / "scheduled_role_runner.py"
    if os.name == "nt":
        return f'{python_cmd} "{script}" --role "{role}"'
    try:
        import shlex

        return " ".join([python_cmd, shlex.quote(str(script)), "--role", shlex.quote(role)])
    except Exception:
        return f'{python_cmd} "{script}" --role "{role}"'


def task_summary(task: Mapping[str, str]) -> str:
    task_id = str(task.get("task_id", "") or task.get("id", "")).strip()
    title = str(task.get("title", "")).strip()
    project = str(task.get("project", "")).strip()
    parts = [part for part in [task_id, title, project] if part]
    return " / ".join(parts) if parts else "assigned task"


def provider_remediation_resolved(task: Mapping[str, str], role: str, cfg: RoleConfigView) -> bool:
    task_id = str(task.get("task_id", "") or task.get("id", "")).upper()
    if not task_id.startswith("TASK-HARNESS-"):
        return False
    # Provider remediation tasks are operator/ChiefChat context. They should
    # not keep waking the same failed role through Runner, especially for the
    # cheap Chief chat path where setup failures are reported directly in chat.
    return True
    failure_role = str(task.get("failure_role", "")).strip()
    if failure_role and failure_role != role:
        return False
    failed_provider = str(task.get("failed_provider", "")).strip().lower()
    current_provider = " ".join([cfg.harness_key, cfg.harness_type, cfg.launch_command]).lower()
    return bool(failed_provider and failed_provider not in current_provider)


def evaluate_role_preflight(
    root: Path,
    role: str,
    config: Any,
    runner_cfg: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    wake_requests: list[str] | None = None,
    force_reason: str = "",
) -> dict[str, Any]:
    runner_cfg = runner_cfg or parse_key_values(root / "Runner" / "RUNNER_CONFIG.md")
    state = state or load_json(root / "Runner" / ".runner_state.json")
    cfg = config_view(role, config)
    lease = read_lease(root, role)
    cooldown = cooldown_state(state, role)
    if is_cheap_chief_config(role, cfg):
        cooldown = {**cooldown, "provider_active": False, "provider_until": ""}
    reason = (force_reason or "").strip()
    forced_daily = reason.split(":", 1)[0] == "daily_all_hands"
    daily_due = daily_all_hands_due(runner_cfg, state, role)
    quota_retry = parse_bool(runner_cfg.get("Daily All Hands Quota Retry", "YES"), True)

    pending: list[dict[str, str]] = []
    wake_list = wake_requests if wake_requests is not None else pending_wake_requests(root, state, role)
    for wake in wake_list:
        pending.append({"kind": "wake_request", "summary": wake, "reason": wake})

    for task in tasks_for_role(root, role):
        if provider_remediation_resolved(task, role, cfg):
            continue
        pending.append({"kind": "assigned_task", "summary": task_summary(task), "reason": f"assigned_task:{task_summary(task)}"})

    if message_changed(root, state, role):
        pending.append({"kind": "role_message", "summary": f"_messages/{role}.md changed", "reason": "message_change"})

    if role == CHIEF_ROLE and message_changed(root, state, CHIEF_ROLE):
        if not any(item["kind"] == "role_message" for item in pending):
            pending.append({"kind": "operator_intake", "summary": "_messages/Chief_of_Staff.md changed", "reason": "operator_message"})

    if forced_daily or daily_due:
        pending.append({"kind": "daily_all_hands", "summary": "24-hour role check-in/recovery pass", "reason": "daily_all_hands"})

    base = {
        "role": role,
        "generated_at": iso_now(),
        "decision": "skip",
        "action": "",
        "status": "SKIPPED_NO_WORK",
        "reason": "no_actionable_work",
        "summary": "No actionable work was found for this role.",
        "pending_work": pending,
        "pending_count": len(pending),
        "lease": lease,
        "cooldown": cooldown,
        "schedule_enabled": cfg.enabled,
        "automation_ready": cfg.automation_ready,
        "execution_mode": cfg.execution_mode,
        "command_preview": scheduled_command(root, role),
        "daily_all_hands_due": daily_due,
    }

    if not cfg.enabled:
        return {**base, "status": "SKIPPED_DISABLED", "reason": "role_disabled", "summary": "Role schedule is disabled."}
    if not cfg.automation_ready:
        return {**base, "status": "SKIPPED_NOT_READY", "reason": "automation_not_ready", "summary": "Role is not marked automation-ready."}
    if cfg.execution_mode == "manual":
        return {**base, "status": "SKIPPED_MANUAL", "reason": "manual_role", "summary": "Manual roles are not launched by scheduled CLI runners."}
    if lease["active"]:
        return {**base, "status": "SKIPPED_LEASE_ACTIVE", "reason": "lease_active", "summary": "Role already has an active, unexpired lease."}
    if cooldown["stale_active"]:
        return {**base, "status": "PAUSED_STALE_LEASE", "reason": "stale_lease_cooldown", "summary": "Stale-lease recovery is cooling down."}
    if cooldown["provider_active"] and not ((forced_daily or daily_due) and quota_retry):
        return {**base, "status": "PAUSED_PROVIDER", "reason": "provider_cooldown", "summary": "Provider login/quota cooldown is active."}
    if not pending:
        return base

    first_reason = pending[0].get("reason", "pending_work")
    if (forced_daily or daily_due) and cooldown["provider_active"] and quota_retry:
        first_reason = "daily_all_hands_quota_retry"
    elif forced_daily or daily_due:
        first_reason = "daily_all_hands"
    return {
        **base,
        "decision": "run",
        "action": "launch",
        "status": "DAILY_ALL_HANDS" if first_reason.startswith("daily_all_hands") else "RUN_ALLOWED",
        "reason": first_reason,
        "summary": "Inference is allowed because the role is enabled, lease-free, and has pending work.",
    }
