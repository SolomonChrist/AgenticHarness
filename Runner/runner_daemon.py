#!/usr/bin/env python3
"""
Agentic Harness Runner daemon.

One optional daemon that keeps the swarm alive by:
- reading the core markdown files
- checking role leases
- launching configured roles
- supervising persistent roles best-effort
- respecting manual/human-run roles
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


RUNNING = True


def now_local() -> datetime:
    return datetime.now().astimezone()


def iso_now() -> str:
    return now_local().isoformat(timespec="seconds")


def parse_bool(value: str, default: bool = False) -> bool:
    text = (value or "").strip().upper()
    if text in {"YES", "TRUE", "1", "ON", "ACTIVE"}:
        return True
    if text in {"NO", "FALSE", "0", "OFF", "DISABLED"}:
        return False
    return default


def parse_int(value: str, default: int) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


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


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(existing + prefix + line + "\n", encoding="utf-8")


def log_event(event_file: Path, message: str) -> None:
    append_line(event_file, f"[{iso_now()}] [RUNNER] {message}")


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_key_value_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("- "):
            continue
        if line.startswith("|") and line.endswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1]
                if key and key.lower() != "field" and key != "---":
                    data[key] = value
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def parse_markdown_records(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    records: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    current_list_key: Optional[str] = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
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
            clean_key = key.strip()
            clean_value = value.strip()
            if clean_value:
                current[clean_key] = clean_value
                current_list_key = None
            else:
                # Blank-valued keys like "Wake Triggers:" and "Contact Methods:"
                # become markdown list containers on the following lines.
                current[clean_key] = []
                current_list_key = clean_key
    if current:
        records.append(current)
    return records


def role_names_from_roles_file(path: Path) -> List[str]:
    names: List[str] = []
    if not path.exists():
        return names
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("Name:"):
            name = line.split(":", 1)[1].strip()
            if name:
                names.append(name)
    return names


@dataclass
class LeaseStatus:
    role: str
    exists: bool
    active: bool
    stale: bool
    lease_expires_at: Optional[datetime]
    claimed_by: str = ""


@dataclass
class RoleLaunchConfig:
    role: str
    enabled: bool
    execution_mode: str
    harness_key: str
    harness_type: str
    launch_command: str
    working_directory: str
    model_profile: str
    bootstrap_file: str
    startup_prompt: str
    check_interval_minutes: int
    wake_triggers: List[str] = field(default_factory=list)
    max_concurrent_sessions: int = 1
    registration_source: str = ""
    last_confirmed: str = ""
    notes: str = ""


class RunnerDaemon:
    def __init__(self, runner_root: Path) -> None:
        self.runner_root = runner_root.resolve()
        self.harness_root = self.runner_root.parent
        self.config_path = self.runner_root / "RUNNER_CONFIG.md"
        self.registry_path = self.runner_root / "ROLE_LAUNCH_REGISTRY.md"
        self.roles_path = self.harness_root / "ROLES.md"
        self.event_file = self.harness_root / "LAYER_LAST_ITEMS_DONE.md"
        self.heartbeat_root = self.harness_root / "_heartbeat"
        self.messages_root = self.harness_root / "_messages"
        self.task_file = self.harness_root / "LAYER_TASK_LIST.md"
        self.state_path = self.runner_root / ".runner_state.json"
        self.generated_prompt_root = self.runner_root / "_generated_prompts"
        self.state = self.load_state()

    def load_state(self) -> Dict[str, object]:
        if not self.state_path.exists():
            return {"roles": {}, "files": {}}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {"roles": {}, "files": {}}

    def save_state(self) -> None:
        self.runner_root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def load_runner_config(self) -> Dict[str, str]:
        return read_key_value_file(self.config_path)

    def load_role_registry(self) -> Dict[str, RoleLaunchConfig]:
        records = parse_markdown_records(self.registry_path)
        configs: Dict[str, RoleLaunchConfig] = {}
        for record in records:
            if record.get("_type") != "role":
                continue
            role = str(record.get("Role", "")).strip()
            if not role:
                continue
            wake_triggers = record.get("Wake Triggers", [])
            if not isinstance(wake_triggers, list):
                wake_triggers = []
            configs[role] = RoleLaunchConfig(
                role=role,
                enabled=parse_bool(str(record.get("Enabled", "")), default=False),
                execution_mode=str(record.get("Execution Mode", "interval")).strip().lower() or "interval",
                harness_key=str(record.get("Harness Key", "")).strip(),
                harness_type=str(record.get("Harness Type", "")).strip(),
                launch_command=str(record.get("Launch Command", "")).strip(),
                working_directory=str(record.get("Working Directory", "")).strip(),
                model_profile=str(record.get("Model / Profile", "")).strip(),
                bootstrap_file=str(record.get("Bootstrap File", "")).strip(),
                startup_prompt=str(record.get("Startup Prompt", "")).strip(),
                check_interval_minutes=parse_int(str(record.get("Check Interval Minutes", "5")), 5),
                wake_triggers=[trigger.strip() for trigger in wake_triggers if trigger.strip()],
                max_concurrent_sessions=parse_int(str(record.get("Max Concurrent Sessions", "1")), 1),
                registration_source=str(record.get("Registration Source", "")).strip(),
                last_confirmed=str(record.get("Last Confirmed", "")).strip(),
                notes=str(record.get("Notes", "")).strip(),
            )
        return configs

    def read_lease(self, role: str) -> LeaseStatus:
        path = self.heartbeat_root / f"{role}.md"
        if not path.exists():
            return LeaseStatus(role=role, exists=False, active=False, stale=False, lease_expires_at=None)
        data = read_key_value_file(path)
        expiry = parse_iso(data.get("Lease Expires At", ""))
        claimed_by = data.get("Claimed By", "")
        status = (data.get("Status", "") or "").upper()
        stale = bool(expiry and expiry < now_local())
        active = status == "ACTIVE" and not stale
        return LeaseStatus(
            role=role,
            exists=True,
            active=active,
            stale=stale,
            lease_expires_at=expiry,
            claimed_by=claimed_by,
        )

    def file_mtime(self, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    def message_changed(self, role: str) -> bool:
        path = self.messages_root / f"{role}.md"
        key = f"message::{role}"
        mtime = self.file_mtime(path)
        last = float(self.state.setdefault("files", {}).get(key, 0.0))
        changed = mtime > last
        self.state["files"][key] = mtime
        return changed

    def task_changed(self) -> bool:
        key = "task_board"
        mtime = self.file_mtime(self.task_file)
        last = float(self.state.setdefault("files", {}).get(key, 0.0))
        changed = mtime > last
        self.state["files"][key] = mtime
        return changed

    def role_state(self, role: str) -> Dict[str, object]:
        roles = self.state.setdefault("roles", {})
        return roles.setdefault(role, {})

    def interval_due(self, role: str, minutes: int) -> bool:
        state = self.role_state(role)
        last_launch = parse_iso(str(state.get("last_launch_at", "")))
        if last_launch is None:
            return True
        return now_local() >= last_launch + timedelta(minutes=minutes)

    def tracked_process_alive(self, role: str) -> bool:
        state = self.role_state(role)
        pid = int(state.get("pid", 0) or 0)
        return process_alive(pid)

    def build_prompt_text(self, config: RoleLaunchConfig) -> str:
        lines: List[str] = []
        if config.bootstrap_file:
            lines.append(f"Read {config.bootstrap_file} first.")
        if config.startup_prompt:
            lines.append(config.startup_prompt)
        return "\n".join(line for line in lines if line.strip()).strip()

    def write_prompt_file(self, config: RoleLaunchConfig) -> Path:
        self.generated_prompt_root.mkdir(parents=True, exist_ok=True)
        prompt_file = self.generated_prompt_root / f"{config.role}.txt"
        prompt_text = self.build_prompt_text(config)
        prompt_file.write_text(prompt_text + ("\n" if prompt_text else ""), encoding="utf-8")
        return prompt_file

    def render_launch_command(self, config: RoleLaunchConfig, prompt_file: Path) -> str:
        cwd = Path(config.working_directory).expanduser() if config.working_directory else self.harness_root
        prompt_text = self.build_prompt_text(config)
        replacements = {
            "{ROLE}": config.role,
            "{HARNESS_ROOT}": str(self.harness_root),
            "{WORKDIR}": str(cwd),
            "{BOOTSTRAP_FILE}": config.bootstrap_file or "",
            "{PROMPT_FILE}": str(prompt_file),
            "{PROMPT_TEXT}": prompt_text.replace('"', '\\"'),
            "{HARNESS_KEY}": config.harness_key or "",
            "{HARNESS_TYPE}": config.harness_type or "",
            "{MODEL_PROFILE}": config.model_profile or "",
        }
        command = config.launch_command
        for placeholder, value in replacements.items():
            command = command.replace(placeholder, value)
        return command

    def launch_role(self, config: RoleLaunchConfig) -> None:
        if not config.launch_command:
            log_event(self.event_file, f"RUNNER_SKIP - Role {config.role} has no launch command configured.")
            return
        cwd = Path(config.working_directory).expanduser() if config.working_directory else self.harness_root
        prompt_file = self.write_prompt_file(config)
        command = self.render_launch_command(config, prompt_file)
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(cwd),
                shell=True,
            )
        except Exception as exc:
            log_event(self.event_file, f"RUNNER_ERROR - Failed to launch {config.role}: {exc}")
            return

        state = self.role_state(config.role)
        state["last_launch_at"] = iso_now()
        state["pid"] = proc.pid
        state["last_mode"] = config.execution_mode
        log_event(
            self.event_file,
            f"RUNNER_WAKE - Launched {config.role} in {config.execution_mode} mode via {config.harness_type or 'unknown harness'}. Prompt file: {prompt_file.name}.",
        )

    def should_launch(self, config: RoleLaunchConfig, lease: LeaseStatus, runner_cfg: Dict[str, str], task_changed: bool) -> bool:
        if not config.enabled:
            return False
        if config.execution_mode == "manual":
            return False

        wake_on_stale = parse_bool(runner_cfg.get("Wake On Stale Lease", "YES"), True)
        wake_on_task = parse_bool(runner_cfg.get("Wake On Task Change", "YES"), True)
        wake_on_message = parse_bool(runner_cfg.get("Wake On Message Change", "YES"), True)
        interval = config.check_interval_minutes or parse_int(
            runner_cfg.get("Chief_of_Staff Interval Minutes", "2") if config.role == "Chief_of_Staff" else runner_cfg.get("Default Interval Minutes", "5"),
            5,
        )
        message_changed = self.message_changed(config.role) if wake_on_message else False

        if config.execution_mode == "persistent":
            if lease.stale or not lease.exists:
                return True
            return not self.tracked_process_alive(config.role)

        if config.execution_mode == "interval":
            if wake_on_stale and (lease.stale or not lease.exists):
                return True
            if wake_on_message and message_changed:
                return True
            if wake_on_task and task_changed and any(trigger == "task_change" for trigger in config.wake_triggers):
                return True
            return self.interval_due(config.role, interval)

        return False

    def dry_run(self, config: RoleLaunchConfig, lease: LeaseStatus) -> None:
        status = "stale" if lease.stale else "active" if lease.active else "unclaimed"
        state = self.role_state(config.role)
        marker = f"{status}:{config.execution_mode}"
        if state.get("last_dry_marker") != marker:
            prompt_file = self.generated_prompt_root / f"{config.role}.txt"
            rendered = self.render_launch_command(config, prompt_file) if config.launch_command else ""
            print(f"[DRY_RUN] {config.role}: {status} ({config.execution_mode})")
            if rendered and status in {"stale", "unclaimed"}:
                print(f"          would run: {rendered}")
            state["last_dry_marker"] = marker

    def validate_harness_root(self) -> None:
        required = [
            self.harness_root / "AGENTIC_HARNESS.md",
            self.harness_root / "LAYER_CONFIG.md",
            self.harness_root / "ROLES.md",
        ]
        missing = [str(path.name) for path in required if not path.exists()]
        if missing:
            raise RuntimeError(f"Missing required harness files: {', '.join(missing)}")

    def run_once(self) -> None:
        self.validate_harness_root()
        runner_cfg = self.load_runner_config()
        mode = runner_cfg.get("Runner Mode", "DRY_RUN").strip().upper() or "DRY_RUN"
        enabled = parse_bool(runner_cfg.get("Runner Enabled", "NO"), False)
        task_changed = self.task_changed()

        role_names = role_names_from_roles_file(self.roles_path)
        registry = self.load_role_registry()

        for role in role_names:
            config = registry.get(role)
            if not config:
                log_event(self.event_file, f"RUNNER_NOTICE - Role {role} exists but is not registered in Runner/ROLE_LAUNCH_REGISTRY.md.")
                continue
            lease = self.read_lease(role)
            if not enabled or mode == "DRY_RUN":
                self.dry_run(config, lease)
                continue
            if self.should_launch(config, lease, runner_cfg, task_changed):
                self.launch_role(config)

        self.save_state()

    def run_forever(self) -> None:
        while RUNNING:
            try:
                self.run_once()
            except Exception as exc:
                log_event(self.event_file, f"RUNNER_ERROR - {exc}")
            time.sleep(30)


def shutdown(*_args) -> None:
    global RUNNING
    RUNNING = False


def main() -> int:
    runner_root = Path(__file__).resolve().parent
    daemon = RunnerDaemon(runner_root)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    print(f"Starting Agentic Harness Runner for {daemon.harness_root}")
    cfg = daemon.load_runner_config()
    print(
        "Runner mode: {mode} | enabled: {enabled}".format(
            mode=cfg.get("Runner Mode", "DRY_RUN"),
            enabled=cfg.get("Runner Enabled", "NO"),
        )
    )
    daemon.run_forever()
    daemon.save_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
