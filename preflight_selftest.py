#!/usr/bin/env python3
"""Focused tests for Agentic Harness CLI-first preflight behavior."""

from __future__ import annotations

import tempfile
from datetime import timedelta
from pathlib import Path

from Runner.runner_daemon import RunnerDaemon
from role_preflight import evaluate_role_preflight, iso_now, now_local


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="agentic-preflight-"))
    write(root / "ROLES.md", "# ROLES\n\n## Role\nName: Chief_of_Staff\n\n## Role\nName: Engineer\n")
    write(root / "Runner" / "RUNNER_CONFIG.md", "Daily All Hands Enabled: NO\nDaily All Hands Interval Hours: 24\nDaily All Hands Quota Retry: YES\n")
    write(
        root / "Runner" / "ROLE_LAUNCH_REGISTRY.md",
        """# ROLE LAUNCH REGISTRY

### ROLE
Role: Chief_of_Staff
Enabled: YES
Automation Ready: YES
Execution Mode: interval
Harness Type: Claude Code
Launch Command: {AUTO_CLAUDE_CYCLE}

### ROLE
Role: Engineer
Enabled: YES
Automation Ready: YES
Execution Mode: interval
Harness Type: Claude Code
Launch Command: {AUTO_CLAUDE_CYCLE}
""",
    )
    write(root / "LAYER_TASK_LIST.md", "# LAYER TASK LIST\n")
    return root


def cfg(role: str) -> dict[str, str]:
    return {
        "Role": role,
        "Enabled": "YES",
        "Automation Ready": "YES",
        "Execution Mode": "interval",
        "Harness Type": "Claude Code",
        "Launch Command": "{AUTO_CLAUDE_CYCLE}",
    }


def assert_status(result: dict, expected: str) -> None:
    actual = result.get("status")
    if actual != expected:
        raise AssertionError(f"expected {expected}, got {actual}: {result}")


def main() -> int:
    root = make_root()

    assert_status(evaluate_role_preflight(root, "Engineer", cfg("Engineer")), "SKIPPED_NO_WORK")

    future = (now_local() + timedelta(minutes=10)).isoformat(timespec="seconds")
    write(
        root / "_heartbeat" / "Engineer.md",
        f"""# Engineer Lease

- Role: Engineer
- Status: ACTIVE
- Claimed By: Test Harness
- Lease Expires At: {future}
""",
    )
    assert_status(evaluate_role_preflight(root, "Engineer", cfg("Engineer")), "SKIPPED_LEASE_ACTIVE")

    past = (now_local() - timedelta(minutes=10)).isoformat(timespec="seconds")
    write(
        root / "_heartbeat" / "Engineer.md",
        f"""# Engineer Lease

| Field | Value |
| --- | --- |
| Role | Engineer |
| Status | ACTIVE |
| Claimed By | Test Harness |
| Lease Expires At | {past} |
""",
    )
    write(
        root / "LAYER_TASK_LIST.md",
        """# LAYER TASK LIST

## TASK
ID: TASK-1
Title: Implement feature
Owner Role: Engineer
Status: TODO
""",
    )
    assert_status(evaluate_role_preflight(root, "Engineer", cfg("Engineer")), "RUN_ALLOWED")

    write(root / "LAYER_TASK_LIST.md", "# LAYER TASK LIST\n")
    write(
        root / "Projects" / "ManualEdit" / "TASKS.md",
        f"""# TASKS

## TASK
ID: PROJECT-1
Title: Manual project task
Owner Role: Engineer
Status: TODO
Created At: {iso_now()}
""",
    )
    assert_status(evaluate_role_preflight(root, "Engineer", cfg("Engineer")), "RUN_ALLOWED")

    root2 = make_root()
    write(root2 / "_messages" / "Chief_of_Staff.md", f"[{iso_now()}] [operator:visualizer] [operator] hello\n")
    assert_status(evaluate_role_preflight(root2, "Chief_of_Staff", cfg("Chief_of_Staff")), "RUN_ALLOWED")

    root3 = make_root()
    runner_cfg = {"Daily All Hands Enabled": "YES", "Daily All Hands Interval Hours": "24", "Daily All Hands Quota Retry": "YES"}
    assert_status(evaluate_role_preflight(root3, "Engineer", cfg("Engineer"), runner_cfg=runner_cfg), "DAILY_ALL_HANDS")

    tomorrow = (now_local() + timedelta(hours=6)).isoformat(timespec="seconds")
    state = {"roles": {"Engineer": {"provider_cooldown_until": tomorrow}}}
    assert_status(evaluate_role_preflight(root3, "Engineer", cfg("Engineer"), runner_cfg={"Daily All Hands Enabled": "NO"}, state=state), "PAUSED_PROVIDER")
    assert_status(evaluate_role_preflight(root3, "Engineer", cfg("Engineer"), runner_cfg=runner_cfg, state=state), "DAILY_ALL_HANDS")

    root4 = make_root()
    daemon = RunnerDaemon(root4 / "Runner")
    config = daemon.load_role_registry()["Engineer"]
    log_path = root4 / "Runner" / "role_runs" / "Engineer.log"
    write(log_path, "quota")
    daemon.upsert_provider_remediation_task(config, "quota", now_local() + timedelta(hours=6), log_path)
    task_text = (root4 / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    if "TASK-HARNESS-ENGINEER" not in task_text or "Configure replacement harness for Engineer" not in task_text:
        raise AssertionError("provider remediation task was not created")

    print("PREFLIGHT SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
