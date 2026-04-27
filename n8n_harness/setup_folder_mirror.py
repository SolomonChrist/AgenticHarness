#!/usr/bin/env python3
"""Interactive setup for the optional n8n folder mirror add-on."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "mirror_config.local.json"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    default_text = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{default_text}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "true", "1"}


def write_config(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_initial_sync(config_path: Path) -> int:
    command = [
        sys.executable,
        str(HERE / "folder_mirror.py"),
        "--config",
        str(config_path),
        "--once",
    ]
    return subprocess.call(command, cwd=str(HERE.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure the optional n8n Agentic Harness folder mirror.")
    parser.add_argument("--source", default="", help="Main/source Agentic Harness folder.")
    parser.add_argument("--mirror", default="", help="Mirror folder, such as a Google Drive synced folder.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Where to write the local mirror config.")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--delete", action="store_true", help="Propagate deletions. Off by default.")
    parser.add_argument("--initial-sync", action="store_true", help="Run one mirror pass after writing config.")
    parser.add_argument("--create-mirror", action="store_true", help="Create the mirror folder if it does not exist.")
    args = parser.parse_args()

    interactive = not (args.source and args.mirror)
    source = args.source or ask("Source Agentic Harness folder")
    mirror = args.mirror or ask("Mirror folder for n8n / Google Drive")
    if not source or not mirror:
        raise SystemExit("Both source and mirror folders are required.")

    source_path = Path(source).expanduser().resolve()
    mirror_path = Path(mirror).expanduser().resolve()
    if source_path == mirror_path:
        raise SystemExit("Source and mirror folders must be different.")
    if not source_path.exists():
        raise SystemExit(f"Source folder does not exist: {source_path}")
    if not mirror_path.exists():
        create = args.create_mirror or ask_yes_no(f"Mirror folder does not exist. Create {mirror_path}?", default=True)
        if create:
            mirror_path.mkdir(parents=True, exist_ok=True)
        else:
            raise SystemExit(f"Mirror folder does not exist: {mirror_path}")

    delete_propagation = args.delete
    if not args.delete and interactive:
        delete_propagation = ask_yes_no("Propagate file deletions? Leave off for first setup", default=False)

    payload = {
        "source_folder": str(source_path),
        "mirror_folder": str(mirror_path),
        "interval_seconds": args.interval,
        "delete_propagation": delete_propagation,
        "exclude_names": [
            ".git",
            ".locks",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        ],
        "notes": "Local add-on config. Do not ship credentials or machine-specific paths in public templates.",
    }
    config_path = Path(args.config).expanduser().resolve()
    write_config(config_path, payload)
    print(f"Wrote mirror config: {config_path}")
    print("Start the mirror with:")
    print(f'py "{HERE / "folder_mirror.py"}" --config "{config_path}"')

    should_sync = args.initial_sync or ask_yes_no("Run one initial sync now?", default=True)
    if should_sync:
        return run_initial_sync(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
