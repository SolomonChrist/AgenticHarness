#!/usr/bin/env python3
"""Bidirectional folder mirror for n8n Agentic Harness participation.

This tool lets a local Agentic Harness folder and a Google Drive-synced
folder stay synchronized so n8n can edit the same markdown control plane.
It uses polling and a small external state file, so it has no third-party
dependencies and does not write mirror bookkeeping into either mirrored root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable


DEFAULT_EXCLUDES = {
    ".git",
    ".locks",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}


@dataclass(frozen=True)
class FileInfo:
    mtime_ns: int
    size: int
    digest: str

    def to_json(self) -> dict[str, object]:
        return {"mtime_ns": self.mtime_ns, "size": self.size, "digest": self.digest}

    @classmethod
    def from_json(cls, data: object) -> "FileInfo | None":
        if not isinstance(data, dict):
            return None
        try:
            return cls(
                mtime_ns=int(data.get("mtime_ns", 0)),
                size=int(data.get("size", 0)),
                digest=str(data.get("digest", "")),
            )
        except Exception:
            return None


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_state_path(left: Path, right: Path) -> Path:
    seed = f"{left.resolve()}|{right.resolve()}".encode("utf-8", errors="replace")
    name = hashlib.sha256(seed).hexdigest()[:16]
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".agentic_harness" / "folder_mirror" / f"{name}.json"


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_info(path: Path) -> FileInfo:
    stat = path.stat()
    return FileInfo(mtime_ns=stat.st_mtime_ns, size=stat.st_size, digest=hash_file(path))


def should_skip(path: Path, root: Path, excludes: set[str]) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in excludes for part in parts)


def scan(root: Path, excludes: set[str]) -> Dict[str, FileInfo]:
    files: Dict[str, FileInfo] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if should_skip(path, root, excludes):
            if path.is_dir():
                continue
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        try:
            files[rel] = file_info(path)
        except OSError:
            continue
    return files


def load_state(path: Path) -> dict[str, dict[str, FileInfo]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    state: dict[str, dict[str, FileInfo]] = {}
    if not isinstance(raw, dict):
        return state
    for rel, sides in raw.get("files", {}).items() if isinstance(raw.get("files"), dict) else []:
        if not isinstance(sides, dict):
            continue
        left = FileInfo.from_json(sides.get("left"))
        right = FileInfo.from_json(sides.get("right"))
        state[str(rel)] = {}
        if left:
            state[str(rel)]["left"] = left
        if right:
            state[str(rel)]["right"] = right
    return state


def load_mirror_config(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Could not read mirror config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Mirror config must be a JSON object: {path}")
    return data


def save_state(path: Path, left: Dict[str, FileInfo], right: Dict[str, FileInfo]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        temp_root = Path(os.environ.get("TEMP") or str(Path.home()))
        path = temp_root / "AgenticHarness" / "folder_mirror" / path.name
        path.parent.mkdir(parents=True, exist_ok=True)
    rels = sorted(set(left) | set(right))
    payload = {
        "updated_at": iso_now(),
        "files": {
            rel: {
                "left": left[rel].to_json() if rel in left else None,
                "right": right[rel].to_json() if rel in right else None,
            }
            for rel in rels
        },
    }
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temp, path)


def same(info_a: FileInfo | None, info_b: FileInfo | None) -> bool:
    return bool(info_a and info_b and info_a.digest == info_b.digest and info_a.size == info_b.size)


def changed_from(previous: FileInfo | None, current: FileInfo | None) -> bool:
    if previous is None and current is None:
        return False
    if previous is None or current is None:
        return True
    return previous.digest != current.digest or previous.size != current.size


def newest_side(left: FileInfo | None, right: FileInfo | None) -> str:
    if left and not right:
        return "left"
    if right and not left:
        return "right"
    if left and right and left.mtime_ns >= right.mtime_ns:
        return "left"
    return "right"


def copy_file(src_root: Path, dst_root: Path, rel: str, dry_run: bool) -> str:
    src = src_root / rel
    dst = dst_root / rel
    if dry_run:
        return f"DRY copy {rel}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp = dst.with_name(dst.name + ".mirror_tmp")
    shutil.copy2(src, temp)
    os.replace(temp, dst)
    return f"copy {rel}"


def delete_file(root: Path, rel: str, dry_run: bool) -> str:
    path = root / rel
    if dry_run:
        return f"DRY delete {rel}"
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return f"delete {rel}"


def sync_once(left_root: Path, right_root: Path, state_path: Path, excludes: set[str], *, delete: bool, dry_run: bool) -> list[str]:
    previous = load_state(state_path)
    left = scan(left_root, excludes)
    right = scan(right_root, excludes)
    actions: list[str] = []

    for rel in sorted(set(left) | set(right) | set(previous)):
        left_now = left.get(rel)
        right_now = right.get(rel)
        old = previous.get(rel, {})
        left_old = old.get("left")
        right_old = old.get("right")

        if same(left_now, right_now):
            continue

        left_changed = changed_from(left_old, left_now)
        right_changed = changed_from(right_old, right_now)

        if left_now is None and right_now is not None:
            if delete and left_changed and not right_changed:
                actions.append(delete_file(right_root, rel, dry_run))
            else:
                actions.append(copy_file(right_root, left_root, rel, dry_run))
            continue

        if right_now is None and left_now is not None:
            if delete and right_changed and not left_changed:
                actions.append(delete_file(left_root, rel, dry_run))
            else:
                actions.append(copy_file(left_root, right_root, rel, dry_run))
            continue

        if left_now and right_now:
            if left_changed and not right_changed:
                actions.append(copy_file(left_root, right_root, rel, dry_run))
            elif right_changed and not left_changed:
                actions.append(copy_file(right_root, left_root, rel, dry_run))
            else:
                winner = newest_side(left_now, right_now)
                if winner == "left":
                    actions.append(copy_file(left_root, right_root, rel, dry_run))
                else:
                    actions.append(copy_file(right_root, left_root, rel, dry_run))

    if not dry_run:
        save_state(state_path, scan(left_root, excludes), scan(right_root, excludes))
    return actions


def parse_excludes(values: Iterable[str]) -> set[str]:
    excludes = set(DEFAULT_EXCLUDES)
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                excludes.add(part)
    return excludes


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror two Agentic Harness folders for n8n file-based participation.")
    parser.add_argument("--config", default="", help="Path to a mirror_config.local.json file created by setup_folder_mirror.py.")
    parser.add_argument("--left", default="", help="Primary/local Agentic Harness folder.")
    parser.add_argument("--right", default="", help="Mirror folder, such as a Google Drive synced folder.")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds.")
    parser.add_argument("--state-file", default="", help="State file outside both mirrored folders. Defaults to LOCALAPPDATA.")
    parser.add_argument("--exclude", action="append", default=[], help="Comma-separated names to exclude, repeatable.")
    parser.add_argument("--delete", action="store_true", help="Propagate deletions after the initial state is known.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true", help="Run one sync pass and exit.")
    args = parser.parse_args()

    if args.config:
        config = load_mirror_config(Path(args.config).expanduser().resolve())
        args.left = args.left or str(config.get("source_folder", ""))
        args.right = args.right or str(config.get("mirror_folder", ""))
        args.interval = float(config.get("interval_seconds", args.interval) or args.interval)
        args.delete = bool(config.get("delete_propagation", args.delete))
        if not args.state_file:
            args.state_file = str(config.get("state_file", "") or "")
        for item in config.get("exclude_names", []) if isinstance(config.get("exclude_names"), list) else []:
            args.exclude.append(str(item))

    if not args.left or not args.right:
        raise SystemExit("Provide --left and --right, or provide --config created by setup_folder_mirror.py")

    left = Path(args.left).expanduser().resolve()
    right = Path(args.right).expanduser().resolve()
    if left == right:
        raise SystemExit("--left and --right must be different folders")
    if not left.exists():
        raise SystemExit(f"left folder does not exist: {left}")
    right.mkdir(parents=True, exist_ok=True)
    state_path = Path(args.state_file).expanduser().resolve() if args.state_file else default_state_path(left, right)
    excludes = parse_excludes(args.exclude)

    print(f"Agentic Harness folder mirror")
    print(f"left:  {left}")
    print(f"right: {right}")
    print(f"state: {state_path}")
    print(f"delete propagation: {'on' if args.delete else 'off'}")

    while True:
        actions = sync_once(left, right, state_path, excludes, delete=args.delete, dry_run=args.dry_run)
        for action in actions:
            print(f"[{iso_now()}] {action}", flush=True)
        if args.once:
            return 0
        time.sleep(max(0.25, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
