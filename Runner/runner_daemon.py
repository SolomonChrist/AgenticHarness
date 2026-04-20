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

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordination_io import append_line as append_line_safe, atomic_write_text


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
    append_line_safe(path, line)


def quote_command_arg(value: str) -> str:
    text = str(value)
    if os.name == "nt":
        if not text:
            return '""'
        if any(ch in text for ch in ' \t"&()[]{}^=;!+,`~'):
            return '"' + text.replace('"', '""') + '"'
        return text
    try:
        import shlex

        return shlex.quote(text)
    except Exception:
        return text


def escape_template_value(value: str) -> str:
    text = str(value)
    if os.name == "nt":
        return text.replace('"', '\\"')
    try:
        import shlex

        return shlex.quote(text)
    except Exception:
        return text.replace('"', '\\"')


def cli_model_arg(provider: str, model_profile: str) -> str:
    text = (model_profile or "").strip()
    if not text:
        return ""

    normalized_provider = provider.strip().lower()

    # Claude Code wants a concrete model id such as
    # `claude-haiku-4-5-20251001`, not a human-facing label like
    # `Haiku 4.5`. If the registry only has a display label, let the CLI
    # use its current default model instead of failing every cycle.
    if normalized_provider == "claude":
        return text if text.startswith("claude-") else ""

    return text


def log_event(event_file: Path, message: str) -> None:
    append_line(event_file, f"[{iso_now()}] [RUNNER] {message}")


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


def markdown_scalar(value: object) -> str:
    if isinstance(value, list):
        return ""
    return str(value or "").strip()


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
    automation_ready: bool
    execution_mode: str
    harness_key: str
    harness_type: str
    launch_command: str
    working_directory: str
    model_profile: str
    bootstrap_file: str
    startup_prompt: str
    wake_message: str
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
        self.wake_requests_file = self.runner_root / "_wake_requests.md"
        self.reminders_file = self.runner_root / "_reminders.json"
        self.state_path = self.runner_root / ".runner_state.json"
        self.runtime_path = self.runner_root / ".runner_runtime.json"
        self.generated_prompt_root = self.runner_root / "_generated_prompts"
        self.role_run_log_root = self.runner_root / "role_runs"
        self.started_at = iso_now()
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
        atomic_write_text(self.state_path, json.dumps(self.state, indent=2))

    def count_pending_wake_requests(self) -> int:
        if not self.wake_requests_file.exists():
            return 0
        lines = [line.strip() for line in self.wake_requests_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        seen = set(self.state.get("wake_requests_seen", []))
        return sum(1 for line in lines if line not in seen)

    def load_reminders(self) -> List[Dict[str, object]]:
        if not self.reminders_file.exists():
            return []
        try:
            data = json.loads(self.reminders_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_reminders(self, reminders: List[Dict[str, object]]) -> None:
        self.runner_root.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.reminders_file, json.dumps(reminders, indent=2))

    def process_due_reminders(self) -> None:
        reminders = self.load_reminders()
        if not reminders:
            return
        now = now_local()
        changed = False
        for reminder in reminders:
            if str(reminder.get("status", "")).lower() != "pending":
                continue
            due_at = parse_iso(str(reminder.get("due_at", "")))
            if not due_at or due_at > now:
                continue
            human_id = str(reminder.get("human_id", "")).strip()
            text = str(reminder.get("text", "")).strip()
            if not human_id or not text:
                reminder["status"] = "error"
                reminder["error"] = "missing human_id or text"
                changed = True
                continue
            human_file = self.messages_root / f"human_{human_id}.md"
            append_line(human_file, f"[{iso_now()}] [Chief_of_Staff] Reminder: {text}.")
            reminder["status"] = "sent"
            reminder["sent_at"] = iso_now()
            changed = True
            log_event(self.event_file, f"REMINDER_SENT - Sent reminder to {human_id}: {text}")
        if changed:
            self.save_reminders(reminders)

    def update_runtime_status(self, status: str, *, last_error: str = "", runner_cfg: Optional[Dict[str, str]] = None) -> None:
        cfg = runner_cfg or self.load_runner_config()
        payload = {
            "component": "runner",
            "status": status,
            "pid": os.getpid(),
            "started_at": self.started_at,
            "updated_at": iso_now(),
            "enabled": cfg.get("Runner Enabled", "NO"),
            "mode": cfg.get("Runner Mode", "DRY_RUN"),
            "pending_wake_requests": self.count_pending_wake_requests(),
            "last_error": last_error,
        }
        atomic_write_text(self.runtime_path, json.dumps(payload, indent=2))

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
                enabled=parse_bool(markdown_scalar(record.get("Enabled", "")), default=False),
                automation_ready=parse_bool(markdown_scalar(record.get("Automation Ready", "")), default=False),
                execution_mode=markdown_scalar(record.get("Execution Mode", "interval")).lower() or "interval",
                harness_key=markdown_scalar(record.get("Harness Key", "")),
                harness_type=markdown_scalar(record.get("Harness Type", "")),
                launch_command=markdown_scalar(record.get("Launch Command", "")),
                working_directory=markdown_scalar(record.get("Working Directory", "")),
                model_profile=markdown_scalar(record.get("Model / Profile", "")),
                bootstrap_file=markdown_scalar(record.get("Bootstrap File", "")),
                startup_prompt=markdown_scalar(record.get("Startup Prompt", "")),
                wake_message=markdown_scalar(record.get("Wake Message", "")),
                check_interval_minutes=parse_int(markdown_scalar(record.get("Check Interval Minutes", "5")), 5),
                wake_triggers=[trigger.strip() for trigger in wake_triggers if trigger.strip()],
                max_concurrent_sessions=parse_int(markdown_scalar(record.get("Max Concurrent Sessions", "1")), 1),
                registration_source=markdown_scalar(record.get("Registration Source", "")),
                last_confirmed=markdown_scalar(record.get("Last Confirmed", "")),
                notes=markdown_scalar(record.get("Notes", "")),
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

    def consume_wake_requests(self) -> Dict[str, List[str]]:
        requests: Dict[str, List[str]] = {}
        if not self.wake_requests_file.exists():
            return requests
        lines = self.wake_requests_file.read_text(encoding="utf-8").splitlines()
        seen = set(self.state.setdefault("wake_requests_seen", []))
        updated_seen = set(seen)
        for raw in lines:
            line = raw.strip()
            if not line or line in seen:
                continue
            updated_seen.add(line)
            if "]" in line:
                tail = line.split("]", 1)[1].strip()
            else:
                tail = line
            if ":" in tail:
                role, reason = tail.split(":", 1)
                role = role.strip()
                reason = reason.strip() or "wake_request"
            else:
                role = tail.strip()
                reason = "wake_request"
            if role:
                requests.setdefault(role, []).append(reason)
        self.state["wake_requests_seen"] = list(updated_seen)[-1000:]
        return requests

    def clear_launch_throttle_if_healthy(self, role: str, lease: LeaseStatus) -> None:
        if not lease.active:
            return
        state = self.role_state(role)
        for key in ["failure_count", "cooldown_until", "last_failed_attempt_at", "last_throttle_log", "last_launch_suppressed_until"]:
            state.pop(key, None)

    def role_state(self, role: str) -> Dict[str, object]:
        roles = self.state.setdefault("roles", {})
        return roles.setdefault(role, {})

    def log_unregistered_role_once(self, role: str) -> None:
        state = self.role_state(role)
        last_notice = parse_iso(str(state.get("last_unregistered_notice_at", "")))
        if last_notice and now_local() < last_notice + timedelta(minutes=10):
            return
        state["last_unregistered_notice_at"] = iso_now()
        log_event(self.event_file, f"RUNNER_NOTICE - Role {role} exists but is not registered in Runner/ROLE_LAUNCH_REGISTRY.md.")

    def interval_due(self, role: str, minutes: int) -> bool:
        state = self.role_state(role)
        last_launch = parse_iso(str(state.get("last_launch_at", "")))
        last_nudge = parse_iso(str(state.get("last_nudge_at", "")))
        last_activity = max(
            [value for value in [last_launch, last_nudge] if value is not None],
            default=None,
        )
        if last_activity is None:
            return True
        return now_local() >= last_activity + timedelta(minutes=minutes)

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
        command = self.effective_launch_command(config, prompt_file, cwd)
        replacements = {
            "{ROLE}": config.role,
            "{HARNESS_ROOT}": str(self.harness_root),
            "{WORKDIR}": str(cwd),
            "{BOOTSTRAP_FILE}": config.bootstrap_file or "",
            "{PROMPT_FILE}": str(prompt_file),
            "{PROMPT}": escape_template_value(prompt_text),
            "{PROMPT_TEXT}": escape_template_value(prompt_text),
            "{MODEL}": config.model_profile or "",
            "{HARNESS_KEY}": config.harness_key or "",
            "{HARNESS_TYPE}": config.harness_type or "",
            "{MODEL_PROFILE}": config.model_profile or "",
        }
        for placeholder, value in replacements.items():
            command = command.replace(placeholder, value)
        return command

    def command_looks_placeholder(self, command: str) -> bool:
        text = (command or "").strip().lower()
        if not text:
            return True
        if text in {"tbd", "todo", "unknown", "(blank)"}:
            return True
        if text.startswith("start new ") or text.startswith("start "):
            return True
        return False

    def prefers_claude_cycle(self, config: RoleLaunchConfig) -> bool:
        harness = " ".join(
            part for part in [config.harness_key, config.harness_type, config.model_profile] if part
        ).lower()
        return "claude" in harness

    def build_default_claude_cycle_command(self, config: RoleLaunchConfig, prompt_file: Path, cwd: Path) -> str:
        script = self.runner_root / "claude_role_cycle.py"
        python_cmd = "py" if os.name == "nt" else "python3"
        model_arg = cli_model_arg("claude", config.model_profile)
        parts = [
            python_cmd,
            str(script),
            "--role",
            config.role,
            "--workdir",
            str(cwd),
            "--prompt-file",
            str(prompt_file),
        ]
        if config.bootstrap_file:
            parts.extend(["--bootstrap-file", config.bootstrap_file])
        if model_arg:
            parts.extend(["--model", model_arg])
        return " ".join(quote_command_arg(part) for part in parts)

    def build_generic_cycle_command(self, provider: str, config: RoleLaunchConfig, prompt_file: Path, cwd: Path) -> str:
        script = self.runner_root / "harness_role_cycle.py"
        python_cmd = "py" if os.name == "nt" else "python3"
        model_arg = cli_model_arg(provider, config.model_profile)
        parts = [
            python_cmd,
            str(script),
            "--provider",
            provider,
            "--role",
            config.role,
            "--workdir",
            str(cwd),
            "--prompt-file",
            str(prompt_file),
        ]
        if config.bootstrap_file:
            parts.extend(["--bootstrap-file", config.bootstrap_file])
        if model_arg:
            parts.extend(["--model", model_arg])
        return " ".join(quote_command_arg(part) for part in parts)

    def effective_launch_command(self, config: RoleLaunchConfig, prompt_file: Path, cwd: Path) -> str:
        command = (config.launch_command or "").strip()
        if "{AUTO_CLAUDE_CYCLE}" in command:
            return command.replace("{AUTO_CLAUDE_CYCLE}", self.build_default_claude_cycle_command(config, prompt_file, cwd))
        if "{AUTO_OPENCODE_CYCLE}" in command:
            return command.replace("{AUTO_OPENCODE_CYCLE}", self.build_generic_cycle_command("opencode", config, prompt_file, cwd))
        if "{AUTO_GOOSE_CYCLE}" in command:
            return command.replace("{AUTO_GOOSE_CYCLE}", self.build_generic_cycle_command("goose", config, prompt_file, cwd))
        if "{AUTO_OLLAMA_CYCLE}" in command:
            return command.replace("{AUTO_OLLAMA_CYCLE}", self.build_generic_cycle_command("ollama", config, prompt_file, cwd))
        if self.command_looks_placeholder(command) and self.prefers_claude_cycle(config):
            return self.build_default_claude_cycle_command(config, prompt_file, cwd)
        return command

    def append_role_message(self, role: str, message: str) -> None:
        if not message.strip():
            return
        path = self.messages_root / f"{role}.md"
        append_line(path, f"[{iso_now()}] [Runner] {message}")
        # Prevent the Runner from interpreting its own nudge/write as a fresh
        # external message change on the next polling loop.
        self.state.setdefault("files", {})[f"message::{role}"] = self.file_mtime(path)

    def build_wake_message(self, config: RoleLaunchConfig, reason: str) -> str:
        if config.wake_message:
            return config.wake_message.replace("{ROLE}", config.role).replace("{REASON}", reason)
        if reason == "task_change":
            return "Check for newly assigned tasks and continue active work."
        if reason == "message_change":
            return "Check your direct messages and respond or continue work as needed."
        if reason in {"stale_lease", "unclaimed"}:
            return "Reclaim your role if needed, check status, then continue current work."
        if reason == "process_dead":
            return "Resume your role, check status, and continue the current workstream."
        return "Check status and continue current work."

    def nudge_role(self, config: RoleLaunchConfig, reason: str) -> None:
        self.append_role_message(config.role, self.build_wake_message(config, reason))
        state = self.role_state(config.role)
        state["last_nudge_at"] = iso_now()
        log_event(
            self.event_file,
            f"RUNNER_NUDGE - Nudged {config.role}. Reason: {reason}.",
        )

    def launch_role(self, config: RoleLaunchConfig, reason: str) -> None:
        if not config.launch_command:
            log_event(self.event_file, f"RUNNER_SKIP - Role {config.role} has no launch command configured.")
            return
        cwd = Path(config.working_directory).expanduser() if config.working_directory else self.harness_root
        prompt_file = self.write_prompt_file(config)
        command = self.render_launch_command(config, prompt_file)
        self.append_role_message(config.role, self.build_wake_message(config, reason))
        state = self.role_state(config.role)
        state["last_launch_at"] = iso_now()
        state["last_launch_attempt_at"] = state["last_launch_at"]
        self.role_run_log_root.mkdir(parents=True, exist_ok=True)
        role_log = self.role_run_log_root / f"{config.role}.log"
        log_handle = open(role_log, "a", encoding="utf-8", errors="replace")
        log_handle.write(f"\n[{state['last_launch_at']}] RUNNER launching {config.role}. Reason: {reason}\n")
        log_handle.write(f"Command: {command}\n\n")
        log_handle.flush()
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(cwd),
                shell=True,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
        except Exception as exc:
            log_handle.close()
            state["failure_count"] = int(state.get("failure_count", 0) or 0) + 1
            state["last_launch_error"] = str(exc)
            log_event(self.event_file, f"RUNNER_ERROR - Failed to launch {config.role}: {exc}")
            return
        finally:
            try:
                log_handle.close()
            except Exception:
                pass

        state["pid"] = proc.pid
        state["last_mode"] = config.execution_mode
        state["last_launch_error"] = ""
        state["last_launch_log"] = str(role_log)
        log_event(
            self.event_file,
            f"RUNNER_WAKE - Launched {config.role} in {config.execution_mode} mode via {config.harness_type or 'unknown harness'}. Reason: {reason}. Prompt file: {prompt_file.name}. Log: {role_log.name}.",
        )

    def allow_launch(self, config: RoleLaunchConfig, lease: LeaseStatus, runner_cfg: Dict[str, str], reason: str = "") -> bool:
        state = self.role_state(config.role)
        now = now_local()
        normal_backoff_seconds = max(5, parse_int(runner_cfg.get("Launch Retry Backoff Seconds", "60"), 60))
        urgent_backoff_seconds = max(2, parse_int(runner_cfg.get("Urgent Wake Backoff Seconds", "8"), 8))
        urgent_reasons = {"telegram_message", "operator_message", "wake_request"}
        backoff_seconds = urgent_backoff_seconds if reason in urgent_reasons else normal_backoff_seconds
        failure_threshold = max(1, parse_int(runner_cfg.get("Launch Failure Threshold", "3"), 3))
        cooldown_seconds = max(30, parse_int(runner_cfg.get("Launch Failure Cooldown Seconds", "300"), 300))

        cooldown_until = parse_iso(str(state.get("cooldown_until", "")))
        if cooldown_until and cooldown_until > now:
            marker = cooldown_until.isoformat(timespec="seconds")
            if state.get("last_throttle_log") != marker:
                log_event(
                    self.event_file,
                    f"RUNNER_SUPPRESS - Suppressed launch for {config.role} until {marker}. Reason: cooldown after repeated failed launches.",
                )
                state["last_throttle_log"] = marker
            return False

        last_launch = parse_iso(str(state.get("last_launch_attempt_at", "")))
        if last_launch:
            suppressed_until = last_launch + timedelta(seconds=backoff_seconds)
            if suppressed_until > now:
                marker = suppressed_until.isoformat(timespec="seconds")
                if state.get("last_launch_suppressed_until") != marker:
                    log_event(
                        self.event_file,
                        f"RUNNER_SUPPRESS - Suppressed launch for {config.role} until {marker}. Reason: retry backoff.",
                    )
                    state["last_launch_suppressed_until"] = marker
                return False

            # CLI harness cycles are intentionally short-lived: the process can
            # exit cleanly after writing a reply, renewing a lease, or deciding
            # there is nothing to do. Do not count "process exited" as failure.
            # Only concrete launch exceptions increment failure_count.

        return True

    def role_action(self, config: RoleLaunchConfig, lease: LeaseStatus, runner_cfg: Dict[str, str], task_changed: bool, wake_requests: Dict[str, List[str]]) -> tuple[str, str]:
        if not config.enabled:
            return "", ""
        if not config.automation_ready:
            return "", ""
        if config.execution_mode == "manual":
            return "", ""

        role_wake_requests = wake_requests.get(config.role, [])
        if role_wake_requests:
            reason = role_wake_requests[-1]
            if config.execution_mode == "interval" and reason in {"telegram_message", "wake_request", "operator_message"}:
                return "launch", reason
            return ("nudge", reason) if lease.active else ("launch", reason)

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
                return "launch", "stale_lease" if lease.exists else "unclaimed"
            if not self.tracked_process_alive(config.role):
                return "launch", "process_dead"
            if wake_on_message and message_changed and any(trigger == "message_change" for trigger in config.wake_triggers):
                return "nudge", "message_change"
            if wake_on_task and task_changed and any(trigger == "task_change" for trigger in config.wake_triggers):
                return "nudge", "task_change"
            return "", ""

        if config.execution_mode == "interval":
            if wake_on_stale and (lease.stale or not lease.exists):
                return "launch", "stale_lease" if lease.exists else "unclaimed"
            if wake_on_message and message_changed:
                return ("nudge", "message_change") if lease.active else ("launch", "message_change")
            if wake_on_task and task_changed and any(trigger == "task_change" for trigger in config.wake_triggers):
                return ("nudge", "task_change") if lease.active else ("launch", "task_change")
            if self.interval_due(config.role, interval):
                return ("nudge", "interval_due") if lease.active else ("launch", "interval_due")
            return "", ""

        return "", ""

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
        self.update_runtime_status("active", runner_cfg=runner_cfg)
        self.process_due_reminders()
        task_changed = self.task_changed()
        wake_requests = self.consume_wake_requests()

        role_names = role_names_from_roles_file(self.roles_path)
        registry = self.load_role_registry()

        for role in role_names:
            config = registry.get(role)
            if not config:
                self.log_unregistered_role_once(role)
                continue
            lease = self.read_lease(role)
            self.clear_launch_throttle_if_healthy(role, lease)
            if not enabled or mode == "DRY_RUN":
                self.dry_run(config, lease)
                continue
            action, reason = self.role_action(config, lease, runner_cfg, task_changed, wake_requests)
            if action == "launch":
                if self.allow_launch(config, lease, runner_cfg, reason):
                    self.launch_role(config, reason)
            elif action == "nudge":
                self.nudge_role(config, reason)

        self.save_state()

    def run_forever(self) -> None:
        while RUNNING:
            try:
                self.run_once()
            except Exception as exc:
                log_event(self.event_file, f"RUNNER_ERROR - {exc}")
                self.update_runtime_status("error", last_error=str(exc))
            cfg = self.load_runner_config()
            sleep_seconds = max(1, parse_int(cfg.get("Fast Wake Poll Seconds", "1"), 1))
            time.sleep(sleep_seconds)


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
    try:
        daemon.run_forever()
    finally:
        daemon.save_state()
        daemon.update_runtime_status("stopped", runner_cfg=cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
