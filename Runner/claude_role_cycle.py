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
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordination_io import append_line, read_text
from message_filters import clean_operator_reply
from operator_messaging import append_operator_reply


def reason_category(reason: str) -> str:
    return (reason or "").split(":", 1)[0].strip()


def build_cycle_prompt(role: str, bootstrap_file: str, prompt_text: str) -> str:
    lines: list[str] = []
    if bootstrap_file:
        if bootstrap_file == "AGENTIC_HARNESS.md":
            lines.append("Read AGENTIC_HARNESS_TINY.md first. Do not read the full protocol unless you are blocked.")
        else:
            lines.append(f"Read {bootstrap_file} first.")
    if prompt_text.strip():
        lines.append(prompt_text.strip())
    lines.extend(
        [
            "",
            f"This run was started by Agentic Harness Runner as a scheduled automation pass for the {role} role.",
            "Do one focused automation cycle only, then exit.",
            "This is a low-spend daemon cycle. Prefer direct action over planning.",
            "",
            "Required behavior for this cycle:",
            f"1. Before doing role work, re-check `_heartbeat/{role}.md`. If a different unexpired holder owns {role}, stand down and exit.",
            f"2. If the lease is free or stale, claim {role} by writing acquisition time, expiry time, holder, harness, provider, model, session id, current task, and ACTIVE status.",
            "3. While active, renew heartbeat/lease on meaningful writes. At the end, write final state, release/standby status when appropriate, and a concise event note.",
            "4. Use the generated Context Packet first. Open only the referenced role inbox, task IDs, project TASKS files, or memory files needed for this exact cycle.",
            "5. If you are Chief_of_Staff, treat `_messages/Chief_of_Staff.md` as the operator inbox, including Telegram and Visualizer messages. Do not treat `_messages/human_<HumanID>.md` as the inbox; that file is the human-facing outbox/history.",
            "6. If you are Chief_of_Staff, read `MEMORY/agents/Chief_of_Staff/ALWAYS.md` and the active human `ALWAYS.md` before any operator-facing reply.",
            "7. If you are Chief_of_Staff, reply like the named executive assistant described in memory. Be warm, specific, and conversational. Do not sound like a daemon, checklist, status bot, or generic support script.",
            "8. If the newest operator message is a simple chat, status, reminder, or factual request, answer it directly instead of creating a project or waiting for specialists.",
            "9. For weather, current-information, web, data, file, coding, or research requests, figure out the next concrete action yourself: use available browser/search/CLI tools, create a small local helper, delegate to a daemon-capable role, or give a short fallback only when blocked.",
            "10. Do not ask for Researcher/Engineer setup if a daemon-capable default is already known; configure/wake the needed role or proceed with the current role.",
            "11. If replying to the operator, use `py send_human_reply.py --channel all \"your clean reply\"` or append a clean human-facing reply to `_messages/human_<HumanID>.md`.",
            "12. Update only the relevant markdown files, project artifacts, and event/status notes as needed.",
            "13. If there is no actionable work after the second lease/task check, record a concise idle/standby status and exit cleanly.",
            "14. Do not wait for more input at the end of this run.",
            "",
            "Important constraints:",
            "- Stay in small-context mode. Do not read the full protocol, full chat ledger, full task board, full shared context, or entire memory folders unless blocked.",
            "- Prefer targeted searches around task IDs, owner role, recent messages, and current project names.",
            "- Prefer file reads/writes over shell commands unless a shell command is clearly necessary.",
            "- Keep changes local to the harness workspace.",
            "- Keep operator chat replies natural and short. No bootstrap checklists unless asked.",
            "- Never send daemon-cycle summaries, lease renewals, or internal maintenance notes to the operator chat unless the operator explicitly asks for diagnostics.",
        ]
    )
    return "\n".join(lines).strip()


def active_human_id(workdir: Path) -> str:
    humans = read_text(workdir / "HUMANS.md")
    for line in humans.splitlines():
        if line.startswith("ID:"):
            value = line.split(":", 1)[1].strip()
            if value:
                return value
    return ""


def clean_cli_output(text: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text or "")
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return clean_operator_reply("\n".join(lines).strip())


def append_stdout_reply_if_needed(role: str, workdir: Path, before_outbox: str, stdout: str, reason: str) -> None:
    if role != "Chief_of_Staff":
        return
    if reason_category(reason) not in {"operator_message", "telegram_message", "wake_request", "message_change"}:
        return
    human_id = active_human_id(workdir)
    if not human_id:
        return
    outbox = workdir / "_messages" / f"human_{human_id}.md"
    if read_text(outbox) != before_outbox:
        return
    clean = clean_cli_output(stdout)
    if clean:
        append_operator_reply(workdir, clean, human_id=human_id, from_role="Chief_of_Staff", channel="all")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one Claude Code automation cycle for an Agentic Harness role.")
    parser.add_argument("--role", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--bootstrap-file", default="AGENTIC_HARNESS.md")
    parser.add_argument("--model", default="")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve()
    prompt_file = Path(args.prompt_file).expanduser().resolve()
    prompt_text = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""
    cycle_prompt = build_cycle_prompt(args.role, args.bootstrap_file, prompt_text)
    human_id = active_human_id(workdir)
    outbox = workdir / "_messages" / f"human_{human_id}.md" if human_id else None
    before_outbox = read_text(outbox) if outbox else ""

    command = [
        "claude",
        "-p",
        cycle_prompt,
        "--permission-mode",
        "acceptEdits",
        "--chrome",
        "--max-turns",
        "50",
        "--allowedTools",
        "Read,Edit,Bash",
        "--add-dir",
        str(workdir),
    ]
    if args.model:
        command.extend(["--model", args.model])

    env = os.environ.copy()
    completed = subprocess.run(command, cwd=str(workdir), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if completed.stdout:
        sys.stdout.buffer.write(completed.stdout.encode("utf-8", errors="replace"))
    if completed.stderr:
        sys.stderr.buffer.write(completed.stderr.encode("utf-8", errors="replace"))
    append_stdout_reply_if_needed(args.role, workdir, before_outbox, completed.stdout, args.reason)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
