"""
WorkerDaemon — Components E, C, L, V of H = (E, T, C, S, L, V)

E = Execution Loop (run_cycle, run_with_retry)
C = Context Manager (hook_context_overflow)
L = Lifecycle Hooks (retry, bad-output, blocked-recovery)
V = Evaluation (via Evaluator, called post-execution)
"""
import os
import json
import time
import hashlib
import argparse
import socket
import sys
import psutil
from pathlib import Path
from datetime import datetime, timedelta
import re
import subprocess
import signal

# V: Evaluation component
from evaluator import Evaluator
import threading

class HeartbeatThread(threading.Thread):
    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.bot = bot
        self.daemon = True
        self.stopped = threading.Event()

    def run(self):
        while not self.stopped.is_set():
            try:
                self.bot.sync_state()
            except Exception as e:
                print(f"[{self.bot.name}] Error in heartbeat thread: {e}")
            finally:
                for _ in range(self.bot.heartbeat_seconds):
                    if self.stopped.is_set():
                        break
                    time.sleep(1)

    def stop(self):
        self.stopped.set()

class WorkerDaemon:
    def __init__(self, workspace_path, bot_folder_name):
        self.workspace = Path(workspace_path).resolve()
        self.bot_dir = self.workspace / bot_folder_name
        if not self.bot_dir.exists():
            if (self.workspace / "Bots" / bot_folder_name).exists():
                self.bot_dir = self.workspace / "Bots" / bot_folder_name

        self.bot_def_dir = self.bot_dir / "bot_definition"
        self.bot_workspace_dir = self.bot_dir / "workspace"

        self.load_profiles()
        self.name = self.get_identity_field("Name", bot_folder_name.split('/')[-1])
        self.role = self.get_identity_field("Role", "specialist")
        self.harness = self.get_harness_profile().get("harness", "unknown")

        self.heartbeat_seconds = self.runtime_profile.get("heartbeat_seconds", 30)
        self.lease_seconds = self.runtime_profile.get("lease_seconds", 300)

        # S: Load lifecycle config from SystemProfile (Component S)
        self._load_lifecycle_config()

        # V: Evaluator
        self.evaluator = Evaluator(provider_profile=self.provider_profile_data)

        # L: In-memory duplicate guard (fast lock, session-scoped)
        self.claimed_this_session = set()

        # Priority 3: Meta-Harness Control Plane Registration check
        self._check_control_plane_registration()

    def _check_control_plane_registration(self):
        """Check if this worker is registered in System/ControlPlane.json."""
        cp_path = self.workspace / "System" / "ControlPlane.json"
        if not cp_path.exists():
            return # Skip if no control plane manifest exists yet
        
        try:
            cp = json.loads(cp_path.read_text(encoding="utf-8-sig"))
            registered_workers = cp.get("execution_harnesses", [])
            if registered_workers and self.name not in registered_workers:
                msg = f"WARNING: Worker '{self.name}' is not registered in ControlPlane.json. This bot may be ignored by MasterBot."
                print(f"[{self.get_iso_timestamp()}] {msg}")
                # Log to Status.md for dashboard awareness
                status_path = self.bot_def_dir / "Status.md"
                if status_path.exists():
                    current_status = status_path.read_text(encoding="utf-8")
                    if "Blockers: none" in current_status:
                        new_status = current_status.replace("Blockers: none", f"Blockers: Unregistered in ControlPlane.json")
                        status_path.write_text(new_status, encoding="utf-8")
        except Exception as e:
            print(f"[{self.get_iso_timestamp()}] Error checking registration: {e}")

    def _load_lifecycle_config(self):
        """Load lifecycle settings from System/SystemProfile.json (Component S)."""
        system_profile_path = self.workspace / "System" / "SystemProfile.json"
        config = {}
        if system_profile_path.exists():
            try:
                config = json.loads(system_profile_path.read_text(encoding="utf-8-sig"))
            except Exception:
                pass
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay_seconds = config.get("retry_delay_seconds", 30)
        self.evaluation_mode = config.get("evaluation_mode", "rule_based")
        self.context_threshold = config.get("context_compression_threshold_bytes", 51200)
        
        # Component S overrides
        self.heartbeat_threshold_seconds = config.get("heartbeat_threshold_seconds", 120)
        self.heartbeat_seconds = max(10, self.heartbeat_threshold_seconds // 3)
        self.lease_seconds = self.heartbeat_threshold_seconds + 60

    # ─────────────────────────────────────────────────────────────────────────
    # Core Utilities
    # ─────────────────────────────────────────────────────────────────────────

    def load_profiles(self):
        with open(self.bot_def_dir / "RuntimeProfile.json", 'r', encoding='utf-8-sig') as f:
            self.runtime_profile = json.load(f)
        # Load provider profile for evaluator strict mode
        self.provider_profile_data = {}
        pp_path = self.bot_def_dir / "ProviderProfile.json"
        if pp_path.exists():
            try:
                self.provider_profile_data = json.loads(pp_path.read_text(encoding="utf-8-sig"))
            except Exception:
                pass

    def get_harness_profile(self):
        try:
            with open(self.bot_def_dir / "HarnessProfile.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def get_identity_field(self, field, default):
        content = self.get_file_content(self.bot_def_dir / "Identity.md")
        match = re.search(f"{field}:\\s*(.*)", content)
        return match.group(1).strip() if match else default

    def get_file_content(self, path):
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    def update_file(self, path, content, append=False):
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        if append:
            current = self.get_file_content(path)
            if current and not current.endswith("\n"):
                current += "\n"
            path.write_text(current + content, encoding="utf-8", newline="\n")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")

    def _log(self, text):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{ts}] {text}"
        print(msg)
        try:
            if not self.bot_workspace_dir.exists():
                self.bot_workspace_dir.mkdir(parents=True, exist_ok=True)
            with open(self.bot_workspace_dir / "WORKING_NOTES.md", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            print(f" [!] Logging failed: {e}")

    def get_iso_timestamp(self):
        # V12.1 FIX 3: Always include timezone for accurate health comparisons
        return datetime.now().astimezone().isoformat(timespec='seconds')

    def _clean_instruction_text(self, text: str) -> str:
        if text is None:
            return ""
        cleaned = text.strip()
        cleaned = cleaned.replace("\\n", "\n")
        cleaned = re.sub(r"^```[\w-]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip("`").strip()
        return cleaned

    def _extract_expected_filename(self, task_body: str, output_artifacts=None):
        outputs = [o for o in (output_artifacts or []) if o and o.lower() != "none"]
        if outputs:
            return outputs[0]
        match = re.search(r"(?i)file named\s+([A-Za-z0-9_.-]+)", task_body or "")
        return match.group(1).strip() if match else None

    def _execute_deterministic_file_task(self, task_title, task_body, output_artifacts=None):
        body = (task_body or "").strip()
        lower = body.lower()
        filename = self._extract_expected_filename(body, output_artifacts)
        if not filename:
            return None

        write_match = re.search(r"(?is)write exactly:\s*(.+)$", body)
        create_match = re.search(r"(?is)containing exactly(?: the following text)?:\s*(.+)$", body)
        append_match = re.search(r"(?is)append(?: a new line)?(?: to (?:the )?(?:file )?[A-Za-z0-9_.-]+)?(?: containing exactly:| the following text:)\s*(.+)$", body)

        target_path = self.bot_workspace_dir / filename

        if "append" in lower and append_match:
            append_text = self._clean_instruction_text(append_match.group(1))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "a", encoding="utf-8", newline="\n") as f:
                if target_path.exists() and target_path.stat().st_size > 0 and not append_text.startswith("\n"):
                    f.write("\n")
                f.write(append_text)
            self._log(f"[EXEC:DETERMINISTIC] Appended to {target_path.name}")
            return True, f"deterministic_append: {target_path.name}"

        if ("create a file named" in lower or "write exactly:" in lower or "containing exactly" in lower):
            content_match = write_match or create_match
            if content_match:
                content = self._clean_instruction_text(content_match.group(1))
            elif "no initial content" in lower or "empty file" in lower:
                content = ""
            else:
                return None
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8", newline="\n")
            self._log(f"[EXEC:DETERMINISTIC] Wrote {target_path.name}")
            return True, f"deterministic_write: {target_path.name}"

        return None

    def is_process_alive(self, hostname, pid):
        if hostname != socket.gethostname():
            return True
        return psutil.pid_exists(pid)

    # ─────────────────────────────────────────────────────────────────────────
    # C: Context Manager Hook
    # ─────────────────────────────────────────────────────────────────────────

    def hook_context_overflow(self):
        """C: Compress WORKING_NOTES.md if it exceeds the configured threshold."""
        notes_path = self.bot_workspace_dir / "WORKING_NOTES.md"
        if not notes_path.exists():
            return
        if notes_path.stat().st_size <= self.context_threshold:
            return

        lines = notes_path.read_text(encoding="utf-8").splitlines()
        keep = lines[-50:]
        archive_lines = lines[:-50]

        archive_path = self.bot_workspace_dir / "WORKING_NOTES_ARCHIVE.md"
        self.update_file(archive_path, "\n".join(archive_lines) + "\n", append=True)

        ts = self.get_iso_timestamp()
        header = (
            f"# Working Notes\n"
            f"[C:COMPRESSED {ts} — {len(archive_lines)} lines archived to WORKING_NOTES_ARCHIVE.md]\n\n"
        )
        notes_path.write_text(header + "\n".join(keep), encoding="utf-8")
        print(f"[{self.name}] [C] Context compressed: {len(archive_lines)} lines → archive")

    # ─────────────────────────────────────────────────────────────────────────
    # Lease & State
    # ─────────────────────────────────────────────────────────────────────────

    def acquire_lease(self):
        lease_path = self.bot_def_dir / "Lease.json"
        now = datetime.now().astimezone()

        current_lease = {}
        if lease_path.exists():
            try:
                current_lease = json.loads(lease_path.read_text(encoding="utf-8-sig"))
            except Exception:
                pass

        my_id = f"{socket.gethostname()}:{os.getpid()}"
        owner_id = current_lease.get("lease_owner", "")
        is_stale = True
        expires_at_str = current_lease.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at > now:
                    is_stale = False
            except Exception:
                pass

        if not is_stale and owner_id != my_id:
            owner_hostname = owner_id.split(':')[0] if ':' in owner_id else ""
            owner_pid = current_lease.get("pid")
            if owner_pid and not self.is_process_alive(owner_hostname, owner_pid):
                print(f"[RECOVER] Lease owner {owner_id} dead. Recovering...")
                is_stale = True

        if not is_stale and owner_id != my_id:
            print(f"[REJECTED] Active lease held by {owner_id}")
            return False

        new_lease = {
            "bot_id": self.name.lower(),
            "lease_owner": my_id,
            "pid": os.getpid(),
            "started_at": current_lease.get("started_at", self.get_iso_timestamp()),
            "renewed_at": self.get_iso_timestamp(),
            "expires_at": (now + timedelta(seconds=self.lease_seconds)).isoformat(timespec='seconds'),
            "current_activity": "active"
        }
        self.update_file(lease_path, json.dumps(new_lease, indent=2))
        return True

    def renew_lease(self):
        lease_path = self.bot_def_dir / "Lease.json"
        now = datetime.now().astimezone()
        if not lease_path.exists():
            return
        
        try:
            lease = json.loads(lease_path.read_text(encoding="utf-8-sig"))
            my_id = f"{socket.gethostname()}:{os.getpid()}"
            if lease.get("lease_owner") == my_id:
                lease["renewed_at"] = self.get_iso_timestamp()
                lease["expires_at"] = (now + timedelta(seconds=self.lease_seconds)).isoformat(timespec='seconds')
                self.update_file(lease_path, json.dumps(lease, indent=2))
        except Exception:
            pass

    def sync_state(self, status_msg=None, current_focus=None):
        if status_msg is not None:
             self._last_status_msg = status_msg
        else:
             status_msg = getattr(self, '_last_status_msg', 'active')
             
        if current_focus is not None:
             self._last_focus = current_focus
        else:
             current_focus = getattr(self, '_last_focus', 'idle')

        ts = self.get_iso_timestamp()
        try:
            self.update_file(
                self.bot_def_dir / "Heartbeat.md",
                f"# Heartbeat\nLast Updated: {ts}\nMode: active\n"
                f"Current Activity: {status_msg}\nCurrent Focus: {current_focus}\n"
            )
            self.update_file(
                self.bot_def_dir / "Status.md",
                f"# Status\nCurrent State: active\nCurrent Focus: {current_focus}\n"
                f"Blockers: none\nLast Meaningful Action: {status_msg}\nLast Updated: {ts}\n"
            )
            self.renew_lease()
        except Exception as e:
            print(f"[{self.name}] Failed to write state/heartbeat: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Task State Machine
    # ─────────────────────────────────────────────────────────────────────────

    def claim_task(self, project_name, task_id, task_title):
        ts = self.get_iso_timestamp()
        print(f"[{self.name}] CLAIMING {task_id}: {task_title[:60]}")
        self._log(
            f"\n## Claim\nTimestamp: {ts}\nProject: {project_name}\nTask: {task_id}\n"
            f"Claimed: {task_title}\n"
        )
        # Write 'claimed' immediately to prevent race with other workers
        self.update_master_task(task_id, fields={"Status": "claimed", "Owner": self.name})
        self.sync_state(f"Claimed {task_id}", current_focus=task_id)

    def _is_task_cancelled(self, task_id: str) -> bool:
        """Check live MASTER_TASKS.md to see if operator cancelled this task before execution."""
        path = self.workspace / "MasterBot" / "workspace" / "MASTER_TASKS.md"
        if not path.exists():
            return False
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        # Find the task block and read its current status
        task_regex = rf"### Task\nID:\s*{re.escape(task_id)}(.*?)(?=\n### Task|\n## |\Z)"
        match = re.search(task_regex, content, re.DOTALL)
        if not match:
            return False
        stat_m = re.search(r"(?im)^Status:\s*(\w+)", match.group(1))
        if stat_m and stat_m.group(1).strip().lower() == "cancelled":
            return True
        return False

    def execute_harness_task(self, project_name, task_id, task_title, task_body, output_artifacts=None):

        """
        Executes the task harness.
        task_body = full instruction delivered via HARNESS_TASK env var (no shell truncation).
        Returns (success: bool, result_summary: str)
        """
        ts = self.get_iso_timestamp()

        # Cancellation gate: check if operator cancelled before we start
        if self._is_task_cancelled(task_id):
            self._log(f"[CANCEL] Task {task_id} cancelled by operator before execution.")
            self.sync_state("idle", current_focus="idle")
            return False, "cancelled: operator cancelled before execution"

        self.sync_state(f"Executing {task_id}", current_focus=task_id)
        self.update_master_task(task_id, fields={"Status": "in_progress", "Owner": self.name})

        deterministic_result = self._execute_deterministic_file_task(task_title, task_body, output_artifacts=output_artifacts)
        if deterministic_result is not None:
            return deterministic_result

        # MOCK MODE GATE (Component E)
        if self.provider_profile_data.get("provider") == "mock":
            mock_res = f"[MOCK_MODE] {self.name} simulated execution of '{task_title}'."
            print(f"[{self.name}] {mock_res}")
            # Simulate a small delay
            time.sleep(1)
            # Create a mock artifact
            mock_res_name = f"MOCK_{task_id}.txt"
            mock_res_path = self.bot_workspace_dir / mock_res_name
            mock_text = f"# Research Report: {task_title}\n\n## Abstract\nThis is a mock research result for task {task_id}.\n\n## Findings\n- Benefit 1: Efficiency\n- Benefit 2: Scalability\n- Benefit 3: Meta-orchestration\n\n## Conclusion\nMeta-harnesses are effective."
            mock_res_path.write_text(mock_text, encoding="utf-8")
            
            self._log(f" [MOCK_MODE] {self.name} simulated execution of '{task_title}'.")
            return True, f"MOCK execution successful. Artifact: {mock_res_name}"

        hp = self.get_harness_profile()
        cmd_base = hp.get("entry_command", "")
        harness_type = hp.get("harness", "unknown")

        # Build environment — deliver full payload via HARNESS_TASK (FIX 1 preserved)
        env = os.environ.copy()
        env["HARNESS_TASK"] = task_body
        env["HARNESS_TASK_ID"] = task_id
        env["HARNESS_TASK_TITLE"] = task_title
        env["HARNESS_WORKSPACE"] = str(self.bot_workspace_dir)
        env["HARNESS_BOT_NAME"] = self.name
        env["HARNESS_OUTPUT_ARTIFACTS"] = ",".join(output_artifacts or [])

        pp = self.provider_profile_data
        if pp.get("api_key"):
            if pp.get("provider") == "anthropic":
                env["ANTHROPIC_API_KEY"] = pp["api_key"]
            elif pp.get("provider") in ("openai", "lmstudio"):
                env["OPENAI_API_KEY"] = pp["api_key"]
        if pp.get("api_base"):
            env["OPENAI_BASE_URL"] = pp["api_base"]

        # LM Studio validation
        if pp.get("provider") == "lmstudio" and not pp.get("api_base"):
            msg = "LM Studio requires api_base. Configuration incomplete."
            self.update_file(
                self.bot_def_dir / "Status.md",
                f"# Status\nCurrent State: blocked\nBlockers: {msg}\n"
            )
            return False, f"blocked: {msg}"

        # Build command
        cmd_list = None
        cmd_shell_str = None

        if harness_type == "claude-code":
            if not env.get("ANTHROPIC_API_KEY"):
                msg = "missing key: ANTHROPIC_API_KEY"
                self._log(f" [ERROR] {msg}")
                return False, f"blocked: {msg}"

            if not cmd_base:
                cmd_base = "npx"
            
            # Approved baseline command: npx.cmd -y @anthropic-ai/claude-code -p "{task_body}" --dangerously-skip-permissions
            safe_body = task_body.replace('"', "'")
            if os.name == 'nt' and cmd_base == "npx":
                cmd_shell_str = f'npx.cmd -y @anthropic-ai/claude-code -p "{safe_body}" --dangerously-skip-permissions'
            else:
                cmd_shell_str = f'{cmd_base} -y @anthropic-ai/claude-code -p "{safe_body}" --dangerously-skip-permissions'

        elif harness_type == "base-python":
            script_path = self.bot_workspace_dir / "bot_main.py"
            if not script_path.exists():
                msg = f"Missing bot_main.py in {self.bot_workspace_dir}"
                return False, f"blocked: {msg}"
            python_exe = cmd_base if cmd_base else sys.executable
            cmd_list = [python_exe, str(script_path)]

        else:
            return False, f"blocked: Unknown harness type '{harness_type}'"

        print(f"[{self.name}] HARNESS [{harness_type}] task={task_id}")
        print(f"[{self.name}] CMD: {cmd_shell_str if cmd_shell_str else cmd_list}")
        print(f"[{self.name}] PAYLOAD: {task_body[:120]}...")

        try:
            run_kwargs = dict(
                cwd=str(self.bot_workspace_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='replace'
            )
            # Log the launch intent
            self._log(f"[EXEC] Launching {harness_type} for {task_id}")
            if cmd_list:
                process = subprocess.run(cmd_list, shell=False, **run_kwargs)
            else:
                process = subprocess.run(cmd_shell_str, shell=True, **run_kwargs)

            stdout = process.stdout or ""
            stderr = process.stderr or ""

            log_entry = (
                f"\n## Execution Results\nTimestamp: {ts}\nTask: {task_id}\n"
                f"Exit Code: {process.returncode}\n\n[STDOUT]\n{stdout}\n\n[STDERR]\n{stderr}\n"
            )
            self._log(log_entry)

            if process.returncode == 0:
                return True, f"exit_0: execution succeeded"
            else:
                return False, f"exit_{process.returncode}: non-zero exit"

        except subprocess.TimeoutExpired:
            return False, "blocked: execution timeout (300s)"
        except Exception as e:
            return False, f"blocked: {str(e)}"

    # ─────────────────────────────────────────────────────────────────────────
    # L: Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────────────────

    def run_with_retry(self, proj, tid, title, body, output_artifacts=None):
        """
        E + L: Execution loop with retry lifecycle hook.
        Retries up to max_retries times with retry_delay_seconds between attempts.
        """
        last_result = (False, "no attempts made")

        for attempt in range(1, self.max_retries + 1):
            # Cancellation check before every attempt
            if self._is_task_cancelled(tid):
                return False, "cancelled: operator cancelled during retry"

            if attempt > 1:
                msg = f"[L:RETRY] Attempt {attempt}/{self.max_retries} for task {tid}"
                print(f"[{self.name}] {msg}")
                self._log(f"\n{msg}\n")
                self.update_master_task(
                    tid,
                    fields={"RetryCount": str(attempt - 1), "Status": "in_progress"}
                )
                time.sleep(self.retry_delay_seconds)
                # Check again after the delay (operator may have cancelled while we waited)
                if self._is_task_cancelled(tid):
                    return False, "cancelled: operator cancelled during retry delay"

            success, summary = self.execute_harness_task(proj, tid, title, body, output_artifacts=output_artifacts)
            last_result = (success, summary)

            if success:
                return True, summary

            self._log(f"[L:RETRY] Attempt {attempt} failed: {summary}\n")

        return last_result


    def hook_bad_output(self, proj, tid, title, body, eval_reason, eval_attempt=0, output_artifacts=None):
        """
        L: Bad output hook — triggered when V evaluation fails post-execution.
        Retries up to max_retries times, then blocks.
        Preserves full accountability in task fields.
        """
        if eval_attempt >= self.max_retries:
            reason = f"Evaluation failed after {self.max_retries} eval attempts. Last: {eval_reason}"
            self.report_blocked(proj, tid, title, reason)
            return

        msg = (
            f"[L:BAD_OUTPUT] Eval failed (attempt {eval_attempt + 1}/{self.max_retries}) "
            f"for {tid}: {eval_reason}"
        )
        print(f"[{self.name}] {msg}")
        self._log(f"\n{msg}\n")

        self.update_master_task(
            tid,
            fields={
                "Status": "in_progress",
                "RetryCount": str(eval_attempt + 1),
                "EvalFailReason": eval_reason[:120]
            }
        )

        time.sleep(self.retry_delay_seconds)

        success, summary = self.execute_harness_task(proj, tid, title, body, output_artifacts=output_artifacts)
        if success:
            eval_ok, new_reason = self.evaluator.evaluate(
                tid, body, self.bot_workspace_dir, self.evaluation_mode
            )
            if eval_ok:
                self.complete_task(proj, tid, title, summary)
            else:
                self.hook_bad_output(proj, tid, title, body, new_reason, eval_attempt + 1, output_artifacts=output_artifacts)
        else:
            self.report_blocked(proj, tid, title, f"Re-execution failed on eval retry: {summary}")

    # ─────────────────────────────────────────────────────────────────────────
    # Task Completion & Reporting
    # ─────────────────────────────────────────────────────────────────────────

    def complete_task(self, project_name, task_id, task_title, result_summary):
        ts = self.get_iso_timestamp()

        # 1. Move task to Done section
        self.update_master_task(
            task_id,
            fields={"Status": "done", "Owner": self.name, "CompletedAt": ts},
            target_section="Done"
        )

        # 2. Operator loopback — write to MasterBot TEAM_COMMUNICATION (visible to operator)
        master_comms_path = self.workspace / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md"
        completion_msg = (
            f"\n## Message\nTimestamp: {ts}\nSender: {self.name}\nType: task_complete\n"
            f"Project: {project_name}\nTask: {task_id}\n\n"
            f"[OK] **Task Complete**\n"
            f"- **Task ID**: {task_id}\n"
            f"- **Title**: {task_title}\n"
            f"- **Bot**: {self.name}\n"
            f"- **Status**: done\n"
            f"- **Result**: {result_summary}\n"
            f"- **Artifact Path**: {self.bot_workspace_dir}\n"
        )
        self.update_file(master_comms_path, completion_msg, append=True)

        # 3. Worker state
        self.sync_state(f"Completed {task_id}", current_focus="idle")
        print(f"[{self.name}] [OK] Task {task_id} DONE. Loopback written.")

    def report_blocked(self, project_name, task_id, task_title, reason):
        ts = self.get_iso_timestamp()

        # Move to Blocked section with reason
        self.update_master_task(
            task_id,
            fields={"Status": "blocked", "Owner": self.name, "BlockedReason": reason[:150]},
            target_section="Blocked"
        )

        # Operator loopback
        master_comms_path = self.workspace / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md"
        blocked_msg = (
            f"\n## Message\nTimestamp: {ts}\nSender: {self.name}\nType: task_blocked\n"
            f"Project: {project_name}\nTask: {task_id}\n\n"
            f"[WARN] **Task Blocked**\n"
            f"- **Task ID**: {task_id}\n"
            f"- **Title**: {task_title}\n"
            f"- **Bot**: {self.name}\n"
            f"- **Status**: blocked\n"
            f"- **Reason**: {reason}\n"
        )
        self.update_file(master_comms_path, blocked_msg, append=True)
        self.sync_state(f"Blocked {task_id}", current_focus="idle")
        print(f"[{self.name}] [WARN] Task {task_id} BLOCKED: {reason}")

    # ─────────────────────────────────────────────────────────────────────────
    # MASTER_TASKS.md In-Place Update
    # ─────────────────────────────────────────────────────────────────────────

    def update_master_task(self, task_id, fields=None, target_section=None):
        path = self.workspace / "MasterBot" / "workspace" / "MASTER_TASKS.md"
        if not path.exists():
            return

        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")

        task_regex = rf"### Task\nID:\s*{re.escape(task_id)}(.*?)(?=\n### Task|\n## |\Z)"
        match = re.search(task_regex, content, re.DOTALL)
        if not match:
            print(f"[{self.name}] Warning: Task {task_id} not found in MASTER_TASKS.md")
            return

        block_full = "### Task\nID: " + task_id + match.group(1)
        new_block = block_full

        if fields:
            for k, v in fields.items():
                field_pattern = rf"(?im)^{re.escape(k)}:\s*(.*)$"
                if re.search(field_pattern, new_block):
                    new_block = re.sub(field_pattern, f"{k}: {v}", new_block, count=1)
                else:
                    new_block = new_block.strip() + f"\n{k}: {v}\n"

        if target_section:
            new_content = content.replace(block_full, "").strip()
            new_content = re.sub(r"\n\s*\n\s*\n", "\n\n", new_content)
            section_header = f"## {target_section}"
            lines = new_content.splitlines()
            s_idx = next(
                (i for i, l in enumerate(lines) if l.strip().lower() == section_header.lower()),
                -1
            )
            if s_idx != -1:
                lines.insert(s_idx + 1, "")
                lines.insert(s_idx + 2, new_block.strip())
                new_content = "\n".join(lines) + "\n"
            else:
                new_content += f"\n\n{section_header}\n\n" + new_block.strip() + "\n"
        else:
            new_content = content.replace(block_full, new_block)

        path.write_text(new_content, encoding="utf-8")
        print(f"[{self.name}] Updated task {task_id} -> {fields}")

    # ─────────────────────────────────────────────────────────────────────────
    # Main Execution Cycle
    # ─────────────────────────────────────────────────────────────────────────

    def run_cycle(self):
        # FIX 3: Pulse heartbeat early to reduce false OFFLINE signals in the UI
        self.sync_state("scanning tasks")
        
        # C: Context overflow check at start of every cycle
        self.hook_context_overflow()

        # Acquire lease
        if not self.acquire_lease():
            return

        master_tasks_path = self.workspace / "MasterBot" / "workspace" / "MASTER_TASKS.md"
        content = self.get_file_content(master_tasks_path)

        self._log(
            f"\n[CYCLE] {self.get_iso_timestamp()} | "
            f"MASTER_TASKS found: {master_tasks_path.exists()} | Size: {len(content)}"
        )

        if not content:
            return

        # Parse Claimable sections (New, Active)
        claimable_blocks = []
        for sec in re.split(r"\n##\s+", "\n" + content):
            sec_name = sec.strip().split("\n")[0].lower()
            if "active" in sec_name or "new" in sec_name:
                blocks = re.split(r"### Task", sec, flags=re.IGNORECASE)
                if len(blocks) > 1:
                    claimable_blocks.extend(blocks[1:])
        
        if not claimable_blocks:
            self._log(" [!] No claimable tasks found in New or Active sections.")
            return

        self._log(f" [DEBUG] Found {len(claimable_blocks)} potential task blocks.")

        for block in claimable_blocks:
            tid_m = re.search(r"(?im)^ID:\s*([^\s\r\n]*)", block)
            title_m = re.search(r"(?im)^Title:\s*(.*)", block)
            body_m = re.search(r"(?ims)^Body:\s*(.*?)(?=^\w[\w ]*:\s|\Z)", block)
            proj_m = re.search(r"(?im)^Project:\s*(.*)", block)
            stat_m = re.search(r"(?im)^Status:\s*(\w+)", block)
            owner_m = re.search(r"(?im)^Owner:\s*(.*)", block)
            pref_m = re.search(r"(?im)^Preferred Bot:\s*(.*)", block)
            inp_m = re.search(r"(?im)^InputArtifacts:\s*([^\n]*)", block)
            out_m = re.search(r"(?im)^OutputArtifacts:\s*([^\n]*)", block)
            retry_m = re.search(r"(?im)^RetryCount:\s*(\d+)", block)

            btid = tid_m.group(1).strip() if tid_m else "none"
            bstat = stat_m.group(1).strip().lower() if stat_m else "none"
            bowner = owner_m.group(1).strip().lower() if owner_m else "none"
            bpref = pref_m.group(1).strip().lower() if pref_m else "none"

            self._log(
                f" - Checking {btid} | Status: {bstat} | Owner: {bowner} | Pref: {bpref} (Me: {self.name.lower()})"
            )

            if not (tid_m and title_m and proj_m and stat_m):
                self._log(f" [!] Task {btid} missing required fields.")
                continue

            tid = tid_m.group(1).strip()
            title = title_m.group(1).strip()
            body = body_m.group(1).strip() if body_m else title
            proj = proj_m.group(1).strip()
            status = stat_m.group(1).strip().lower()
            pref_bot = pref_m.group(1).strip() if pref_m else "none"

            if tid in self.claimed_this_session:
                self._log(f" [SKIP] {tid} already claimed this session.")
                continue

            # L: Status guard — pick up new/active, or claimed/in_progress if owned by me
            is_me = (owner_m.group(1).strip().lower() == self.name.lower()) if owner_m else False
            if status not in ("new", "active") and not (status in ("claimed", "in_progress") and is_me):
                self._log(f" [SKIP] {tid} status='{status}' owner_me={is_me} not claimable.")
                continue

            # T: Tool registry check — am I allowed to do this task?
            if not self._can_handle(pref_bot):
                self._log(f" [SKIP] {tid} pref='{pref_bot}' not matching me.")
                continue

            # V4.6 Artifact Gate Cleansing (resilient to master-parser leakage)
            def cleanse_artifact_list(raw):
                if not raw: return []
                # Strip prefix 'ARTIFACTS:' or 'INPUTS:' if present
                clean = re.sub(r"^(ARTIFACTS|INPUTS):\s*", "", raw.strip(), flags=re.IGNORECASE)
                return [i.strip() for i in clean.split(",") if i.strip() and i.strip().lower() != "none"]

            inputs = cleanse_artifact_list(inp_m.group(1)) if inp_m else []
            outputs = cleanse_artifact_list(out_m.group(1)) if out_m else []
            missing_artifacts = []
            for art in inputs:
                if not (self.bot_workspace_dir / art).exists():
                    missing_artifacts.append(art)
            
            if missing_artifacts:
                msg = f"[WAIT] Task {tid} missing required input artifacts: {', '.join(missing_artifacts)}"
                print(f"[{self.name}] {msg}")
                self._log(f" - {msg}")
                # Don't claim, just skip for now. MasterBot orchestration cycle will handle copies.
                continue

            if proj.lower() == "none":
                proj = "ExampleProject"

            # Register in session memory
            self.claimed_this_session.add(tid)

            # State: claim
            self.claim_task(proj, tid, title)

            # E + L: Execute with retry loop
            retry_val = int(retry_m.group(1)) if retry_m else 0
            success, result_summary = self.run_with_retry(proj, tid, title, body, output_artifacts=outputs)

            if success:
                # V: Evaluate before marking done
                eval_ok, eval_reason = self.evaluator.evaluate(
                    tid, body, self.bot_workspace_dir, self.evaluation_mode
                )
                self._log(
                    f"[V:EVAL] Task {tid} | OK: {eval_ok} | Reason: {eval_reason}"
                )
                if eval_ok:
                    self.complete_task(proj, tid, title, result_summary)
                else:
                    # L: Bad output hook — retry evaluation
                    self.hook_bad_output(proj, tid, title, body, eval_reason, eval_attempt=retry_val, output_artifacts=outputs)
            else:
                # Exhausted execution retries
                self.report_blocked(proj, tid, title, result_summary)

            return  # One task per cycle

    def _can_handle(self, preferred_bot: str) -> bool:
        """T: Check if this worker is the right bot for the task (V12.1 Guarded Fuzzy)."""
        if not preferred_bot or preferred_bot.lower().strip() in ("none", ""):
            return True

        me = self.name.lower()
        pref = preferred_bot.strip()
        p_lower = pref.lower()
        
        # 1. Exact bot name match
        if p_lower == me: return True
        
        # 2. Normalized exact match (strip "Bot", lowercase, cleanup)
        # removes "MasterBot" -> "master", "ResearchBot" -> "research"
        me_norm = re.sub(r"bot$", "", me)
        p_norm = re.sub(r"bot$", "", p_lower)
        if me_norm == p_norm: return True

        # 3. Explicit role/capability alias match (checking Identity/Skills)
        # Check if preferred_bot name exists as a substring of our role or purpose
        ident_path = self.bot_def_dir / "Identity.md"
        ident_content = ""
        if ident_path.exists():
            ident_content = ident_path.read_text(encoding="utf-8").lower()
            
        if p_lower in ident_content:
            return True

        # 4. Cautious fuzzy fallback (e.g., 'researcher' matches 'researchbot')
        # Only if there is a clear prefix overlap
        if p_lower.startswith(me_norm) or me_norm.startswith(p_lower):
            # Guard: ensure we don't match short tokens like 'a' or 'the'
            if len(p_lower) > 3:
                return True
            
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Daemon Entry Point
    # ─────────────────────────────────────────────────────────────────────────

    def run(self):
        print(f"Worker Daemon [{self.name}] Active. Harness: {self.harness}")
        print(f"  Lifecycle: max_retries={self.max_retries}, "
              f"eval_mode={self.evaluation_mode}, "
              f"context_threshold={self.context_threshold}b")
        print(f"[{self.get_iso_timestamp()}] {self.name} starting registration...")
        # V12.1 FIX: Asynchronous heartbeats
        hb_thread = HeartbeatThread(self)
        hb_thread.start()
        
        try:
            while True:
                self.run_cycle()
                time.sleep(10)
        except KeyboardInterrupt:
            hb_thread.stop()
            print(f"\n[{self.get_iso_timestamp()}] Shutting down {self.name}.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", type=str, required=True)
    p.add_argument("--bot", type=str, required=True)
    a = p.parse_args()
    WorkerDaemon(a.workspace, a.bot).run()
