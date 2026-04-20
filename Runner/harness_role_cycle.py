#!/usr/bin/env python3
"""
Run one scheduled automation cycle for a supported harness family.

This keeps Runner cross-harness by translating a role cycle into the
best available non-interactive command shape for each CLI.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordination_io import append_line, read_text
from message_filters import clean_operator_reply


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
            f"1. Verify or repair your role state for {role} in the markdown control plane.",
            f"2. Check `_messages/{role}.md`, `LAYER_TASK_LIST.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and your current project/task context.",
            "3. If the newest operator message is a simple chat, status, reminder, or factual request, answer it directly instead of creating a project or waiting for specialists.",
            "4. For current-information, web, data, file, coding, or research requests, figure out the next concrete action yourself: use available CLI tools, create a small local helper, delegate to a daemon-capable role, or give a short fallback only when blocked.",
            "5. Do not ask for Researcher/Engineer setup if a daemon-capable default is already known; configure/wake the needed role or proceed with the current role.",
            "6. If replying to the operator, use `py send_human_reply.py \"your clean reply\"` or append to `_messages/human_<HumanID>.md`.",
            "7. Update only the relevant markdown files, project artifacts, and event/status notes as needed.",
            "8. If there is no actionable work, record a concise idle/standby status and exit cleanly.",
            "9. Do not wait for more input at the end of this run.",
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


def append_stdout_reply_if_needed(role: str, workdir: Path, before_outbox: str, stdout: str) -> None:
    if role != "Chief_of_Staff":
        return
    human_id = active_human_id(workdir)
    if not human_id:
        return
    outbox = workdir / "_messages" / f"human_{human_id}.md"
    if read_text(outbox) != before_outbox:
        return
    clean = clean_cli_output(stdout)
    if clean:
        append_line(outbox, clean)


def command_for_provider(provider: str, prompt: str, workdir: Path, model: str) -> list[str]:
    normalized = provider.strip().lower()
    if normalized == "claude":
        command = [
            "claude",
            "-p",
            prompt,
            "--permission-mode",
            "acceptEdits",
            "--add-dir",
            str(workdir),
        ]
        if model:
            command.extend(["--model", model])
        return command

    if normalized == "opencode":
        command = [
            "opencode",
            "run",
            prompt,
            "--dir",
            str(workdir),
            "--format",
            "default",
        ]
        if model:
            command.extend(["--model", model])
        return command

    if normalized == "goose":
        command = [
            "goose",
            "run",
            "--text",
            prompt,
            "--no-session",
            "--quiet",
        ]
        if model:
            command.extend(["--model", model])
        return command

    if normalized == "ollama":
        if not model:
            raise SystemExit("Ollama adapter requires a concrete model name.")
        return [
            "ollama",
            "run",
            model,
            prompt,
            "--keepalive",
            "5m",
        ]

    raise SystemExit(f"Unsupported provider: {provider}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one scheduled Agentic Harness role cycle for a supported harness CLI.")
    parser.add_argument("--provider", required=True, choices=["claude", "opencode", "goose", "ollama"])
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
    human_id = active_human_id(workdir)
    outbox = workdir / "_messages" / f"human_{human_id}.md" if human_id else None
    before_outbox = read_text(outbox) if outbox else ""

    command = command_for_provider(args.provider, cycle_prompt, workdir, args.model)
    completed = subprocess.run(command, cwd=str(workdir), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    append_stdout_reply_if_needed(args.role, workdir, before_outbox, completed.stdout)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
