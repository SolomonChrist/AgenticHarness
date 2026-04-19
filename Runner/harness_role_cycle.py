#!/usr/bin/env python3
"""
Run one scheduled automation cycle for a supported harness family.

This keeps Runner cross-harness by translating a role cycle into the
best available non-interactive command shape for each CLI.
"""

from __future__ import annotations

import argparse
import subprocess
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
        ]
    )
    return "\n".join(lines).strip()


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

    command = command_for_provider(args.provider, cycle_prompt, workdir, args.model)
    completed = subprocess.run(command, cwd=str(workdir))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
