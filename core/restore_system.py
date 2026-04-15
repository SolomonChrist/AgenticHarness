import os
import json
import shutil
import argparse
from pathlib import Path

def validate_restore_path(backup_type, target_path):
    target = Path(target_path).resolve()
    if backup_type == "full":
        # Full restoration should usually be into a root folder, not a bot/project subdir.
        if "Bots" in target.parts or "Projects" in target.parts:
             print(f"Warning: You are restoring a FULL workspace into a subdirectory: {target}")
             return True # Allowed but warned
    elif backup_type == "bot":
        # Bot restoration should look like its going to a bot folder.
        # Just check if 'Bots' is elsewhere and this folder isn't obvious.
        if not target.name.lower().endswith("bot") and "Bots" not in target.parts:
             print(f"Advice: Bot restores are typically targeted at a folder inside 'Bots/' or named '*Bot'.")
    elif backup_type == "project":
        if "Projects" not in target.parts:
             print(f"Advice: Project restores are typically targeted at a folder inside 'Projects/'.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Agentic Harness Restore System")
    parser.add_argument("--backup", type=str, required=True, help="Path to backup folder (containing MANIFEST.json)")
    parser.add_argument("--target", type=str, required=True, help="Path to target workspace/folder")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing files")
    
    args = parser.parse_args()
    backup_src = Path(args.backup).resolve()
    target_root = Path(args.target).resolve()
    
    if not (backup_src / "MANIFEST.json").exists():
        print(f"Error: MANIFEST.json not found in {backup_src}")
        return
        
    with open(backup_src / "MANIFEST.json", 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    if not validate_restore_path(manifest.get("type"), args.target):
        return

    print(f"Restoring {manifest['type']} backup from {manifest['created_at']}...")
    print(f"Target: {target_root}")
    
    if not target_root.exists():
        target_root.mkdir(parents=True, exist_ok=True)
    
    includes = manifest.get("includes", [])
    for item in includes:
        src = backup_src / item
        dst = target_root / item
        
        if not src.exists():
            print(f"Warning: {item} found in manifest but missing in backup folder. Skipping.")
            continue
            
        if dst.exists() and not args.overwrite:
            print(f"Error: {item} already exists at target. Use --overwrite to allow replacement.")
            return

        print(f"  Restoring {item}...")
        if src.is_dir():
            if dst.exists() and args.overwrite:
                # Merge logic: copy only new/modified files
                for root, dirs, files in os.walk(src):
                    rel_path = Path(root).relative_to(src)
                    target_parent = dst / rel_path
                    target_parent.mkdir(parents=True, exist_ok=True)
                    
                    for f in files:
                        s_file = Path(root) / f
                        d_file = target_parent / f
                        if d_file.exists() and not args.overwrite:
                            continue
                        shutil.copy2(s_file, d_file)
            else:
                shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    print("\nRestore complete.")

if __name__ == "__main__":
    main()
