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
            f"1. Verify or repair your role state for {role} in the markdown control plane.",
            f"2. Check `_messages/{role}.md`, `LAYER_TASK_LIST.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and your current project/task context.",
            "3. If you are Chief_of_Staff, read `MEMORY/agents/Chief_of_Staff/ALWAYS.md` and the active human `ALWAYS.md` before any operator-facing reply.",
            "4. If you are Chief_of_Staff, reply like the named executive assistant described in memory. Be warm, specific, and conversational. Do not sound like a daemon, checklist, status bot, or generic support script.",
            "5. If the newest operator message is a simple chat, status, reminder, or factual request, answer it directly instead of creating a project or waiting for specialists.",
            "6. For weather, current-information, web, data, file, coding, or research requests, figure out the next concrete action yourself: use available browser/search/CLI tools, create a small local helper, delegate to a daemon-capable role, or give a short fallback only when blocked.",
            "7. Do not ask for Researcher/Engineer setup if a daemon-capable default is already known; configure/wake the needed role or proceed with the current role.",
            "8. If replying to the operator, use `py send_human_reply.py --channel all \"your clean reply\"` or append a clean human-facing reply to `_messages/human_<HumanID>.md`.",
            "9. Update only the relevant markdown files, project artifacts, and event/status notes as needed.",
            "10. If there is no actionable work, record a concise idle/standby status and exit cleanly.",
            "11. Do not wait for more input at the end of this run.",
            "",
            "Important constraints:",
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


def command_for_provider(provider: str, prompt: str, workdir: Path, model: str) -> list[str]:
    normalized = provider.strip().lower()
    if normalized == "claude":
        command = [
            "claude",
            "-p",
            prompt,
            "--permission-mode",
            "acceptEdits",
            "--bare",
            "--chrome",
            "--max-turns",
            "4",
            "--allowedTools",
            "Read,Edit,Bash",
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

    if normalized == "gemini":
        command = [
            "gemini",
        ]
        if model:
            command.extend(["--model", model])
        command.extend(["-p", prompt])
        return command

    if normalized == "codex":
        command = [
            "codex",
            "exec",
            "--cd",
            str(workdir),
            "--full-auto",
            "--search",
            "--skip-git-repo-check",
            "--color",
            "never",
        ]
        if model:
            command.extend(["--model", model])
        command.append(prompt)
        return command

    if normalized == "goose":
        command = [
            "goose",
            "run",
            "--text",
            prompt,
            "--no-session",
            "--quiet",
            "--max-turns",
            "4",
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

    if normalized == "deepagents":
        command = [
            "deepagents",
            prompt,
        ]
        if model:
            command.extend(["--model", model])
        return command

    if normalized == "openclaw":
        command = [
            "openclaw",
            "agent",
            "--local",
            "--to",
            "agentic-harness",
            "-m",
            prompt,
            "--timeout",
            "180",
        ]
        if model:
            command.extend(["--agent", model])
        return command

    raise SystemExit(f"Unsupported provider: {provider}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one scheduled Agentic Harness role cycle for a supported harness CLI.")
    parser.add_argument(
        "--provider",
        required=True,
        choices=["claude", "opencode", "gemini", "codex", "goose", "ollama", "deepagents", "openclaw"],
    )
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

    command = command_for_provider(args.provider, cycle_prompt, workdir, args.model)
    completed = subprocess.run(command, cwd=str(workdir), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    append_stdout_reply_if_needed(args.role, workdir, before_outbox, completed.stdout, args.reason)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
