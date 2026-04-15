import os
import json
import shutil
import argparse
from pathlib import Path
import datetime

def get_iso_timestamp():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds').replace(':', '-')

def main():
    parser = argparse.ArgumentParser(description="Agentic Harness Backup System")
    parser.add_argument("--workspace", type=str, required=True, help="Path to workspace root")
    parser.add_argument("--type", type=str, choices=["full", "bot", "project", "masterbot"], required=True, help="Backup type")
    parser.add_argument("--bot", type=str, help="Bot name (if type is bot)")
    parser.add_argument("--project", type=str, help="Project name (if type is project)")
    parser.add_argument("--note", type=str, default="", help="Optional note for manifest")
    
    args = parser.parse_args()
    workspace_root = Path(args.workspace).resolve()
    backup_root = workspace_root / "Backups"
    
    if not backup_root.exists():
        backup_root.mkdir(parents=True, exist_ok=True)
    
    timestamp = get_iso_timestamp()
    backup_dest = None
    includes = []

    if args.type == "full":
        backup_dest = backup_root / timestamp
        includes = ["MasterBot", "Bots", "Projects", "System"]
    elif args.type == "bot":
        if not args.bot:
            print("Error: --bot name required for bot backup")
            return
        backup_dest = backup_root / "bots" / args.bot / timestamp
        includes = [f"Bots/{args.bot}"]
    elif args.type == "project":
        if not args.project:
            print("Error: --project name required for project backup")
            return
        backup_dest = backup_root / "projects" / args.project / timestamp
        includes = [f"Projects/{args.project}"]
    elif args.type == "masterbot":
        backup_dest = backup_root / "masterbot" / timestamp
        includes = ["MasterBot"]

    print(f"Starting {args.type} backup to {backup_dest}...")
    
    if backup_dest.exists():
        print("Error: Backup destination already exists.")
        return
    
    backup_dest.mkdir(parents=True, exist_ok=True)
    
    for item in includes:
        src = workspace_root / item
        if not src.exists():
            print(f"Warning: {item} not found in workspace. Skipping.")
            continue
            
        dst = backup_dest / item
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"  Copied {item}")

    # Create MANIFEST.json
    manifest = {
        "type": args.type,
        "created_at": datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        "workspace_root": str(workspace_root),
        "includes": includes,
        "notes": args.note
    }
    (backup_dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    
    print(f"\nBackup complete: {backup_dest}")

if __name__ == "__main__":
    main()
