#!/usr/bin/env python3
"""
Launch one scheduled Claude Code automation pass for a role.

The Runner uses this helper for cron-style role wakeups:
- start Claude in non-interactive print mode
- give it the role bootstrap prompt plus automation-cycle instructions
- let it do one focused work pass
- exit cleanly until the next wake interval
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def build_cycle_prompt(role: str, bootstrap_file: str, prompt_text: str) -> str:
    lines: list[str] = []
    if bootstrap_file:
        lines.append(f"Read {bootstrap_file} first.")
    if prompt_text.strip():
        lines.append(prompt_text.strip())
    lines.extend(
        [
            "",
            f"This run was started by Agentic Harness Runner as a scheduled automation pass for the {role} role.",
            "Do one focused automation cycle only, then exit.",
            "",
            "Required behavior for this cycle:",
            f"1. Verify or repair your role state for {role} in the markdown control plane.",
            f"2. Check `_messages/{role}.md`, `LAYER_TASK_LIST.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and your current project/task context.",
            "3. Continue or advance any assigned work you can responsibly complete in this pass.",
            "4. Update the relevant markdown files, project artifacts, and event/status notes as needed.",
            "5. If there is no actionable work, record a concise idle/standby status and exit cleanly.",
            "6. Do not wait for more input at the end of this run.",
            "",
            "Important constraints:",
            "- Prefer file reads/writes over shell commands unless a shell command is clearly necessary.",
            "- Keep changes local to the harness workspace.",
            "- Leave clear status updates for Chief_of_Staff or the operator when useful.",
        ]
    )
    return "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one Claude Code automation cycle for an Agentic Harness role.")
    parser.add_argument("--role", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--bootstrap-file", default="AGENTIC_HARNESS.md")
    parser.add_argument("--model", default="")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve()
    prompt_file = Path(args.prompt_file).expanduser().resolve()
    prompt_text = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""
    cycle_prompt = build_cycle_prompt(args.role, args.bootstrap_file, prompt_text)

    command = [
        "claude",
        "-p",
        cycle_prompt,
        "--permission-mode",
        "acceptEdits",
        "--add-dir",
        str(workdir),
    ]
    if args.model:
        command.extend(["--model", args.model])

    completed = subprocess.run(command, cwd=str(workdir))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
