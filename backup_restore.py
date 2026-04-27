#!/usr/bin/env python3
"""Create and restore Agentic Harness backups."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "_backups"

BOT_ONLY_FILES = [
    "AGENTIC_HARNESS.md",
    "AGENTIC_HARNESS_TINY.md",
    "COMMANDS.md",
    "README.md",
    "START_HERE.md",
    "ROLES.md",
    "HUMANS.md",
    "LAYER_CONFIG.md",
    "LAYER_MEMORY.md",
    "LAYER_SHARED_TEAM_CONTEXT.md",
    "LAYER_TASK_LIST.md",
    "role_preflight.py",
    "chat_ledger.py",
    "cheap_chief_router.py",
    "chief_chat_selftest.py",
    "role_jobs.py",
    "service_manager.py",
    "production_check.py",
    "swarm_status.py",
    "send_human_reply.py",
    "wake_role.py",
    "configure_role_daemon.py",
    "control_actions.py",
    "coordination_io.py",
]

BOT_PROJECTS_DIRS = [
    "MEMORY",
    "Projects",
    "Runner",
    "ChiefChat",
    "SKILLS",
]

FULL_SYSTEM_DIRS = BOT_PROJECTS_DIRS + [
    "TelegramBot",
    "Visualizer",
    "n8n_harness",
]


def collect_paths(mode: str) -> list[Path]:
    paths = [ROOT / relative for relative in BOT_ONLY_FILES]
    if mode in {"bots-projects", "full-system-git-history"}:
        paths.extend(ROOT / relative for relative in BOT_PROJECTS_DIRS)
    if mode == "full-system-git-history":
        paths.extend(ROOT / relative for relative in FULL_SYSTEM_DIRS if relative not in {"MEMORY", "Projects", "Runner", "SKILLS"})
        paths.extend([ROOT / "HUMANS.md", ROOT / "ROLES.md", ROOT / "AGENTIC_HARNESS.md", ROOT / "AGENTIC_HARNESS_TINY.md"])
    return [path for path in paths if path.exists()]


def backup_zip(mode: str, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    stamp = subprocess.check_output(["powershell", "-NoProfile", "-Command", "Get-Date -Format yyyyMMdd-HHmmss"], text=True).strip()
    archive = output / f"agentic_harness_{mode}_{stamp}.zip"
    paths = collect_paths(mode)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        zf.write(child, child.relative_to(ROOT))
            else:
                zf.write(path, path.relative_to(ROOT))
    return archive


def backup_full_git(output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    stamp = subprocess.check_output(["powershell", "-NoProfile", "-Command", "Get-Date -Format yyyyMMdd-HHmmss"], text=True).strip()
    bundle = output / f"agentic_harness_full_{stamp}.bundle"
    subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=str(ROOT), check=True)
    return bundle


def restore_from_zip(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as zf:
        zf.extractall(target)


def restore_from_bundle(source: Path, target: Path) -> None:
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"Target folder must be empty for git bundle restore: {target}")
    subprocess.run(["git", "clone", str(source), str(target)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup and restore Agentic Harness.")
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("--mode", required=True, choices=["bots-only", "bots-projects", "full-system-git-history"])
    backup.add_argument("--output", default=str(DEFAULT_OUT))
    restore = sub.add_parser("restore")
    restore.add_argument("--source", required=True)
    restore.add_argument("--target", required=True)
    args = parser.parse_args()

    if args.command == "backup":
        output = Path(args.output).expanduser().resolve()
        if args.mode == "full-system-git-history":
            archive = backup_full_git(output)
        else:
            archive = backup_zip(args.mode, output)
        print(str(archive))
        return 0

    source = Path(args.source).expanduser().resolve()
    target = Path(args.target).expanduser().resolve()
    if source.suffix == ".bundle":
        restore_from_bundle(source, target)
    else:
        restore_from_zip(source, target)
    print(f"restored to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
