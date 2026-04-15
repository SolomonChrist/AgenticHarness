import os
import json
import argparse
from pathlib import Path

def create_file(path, content):
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")

def main():
    parser = argparse.ArgumentParser(description="Agentic Harness Skeleton Generator")
    parser.add_argument("--target", type=str, required=True, help="Target directory for the harness")
    parser.add_argument("--repair", action="store_true", help="Only create missing files, do not overwrite")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files silently")
    args = parser.parse_args()

    target_root = Path(args.target).resolve()
    
    # Define generic framework defaults
    master_bot_files = {
        "MasterBot/bot_definition/Identity.md": "# Identity\nName: MasterBot\nRole: Chief of Staff\n",
        "MasterBot/bot_definition/Soul.md": "# Soul\nMovement Style: calm\nCore Purpose: Coordinate work and protect operator time.\n",
        "MasterBot/bot_definition/Skills.md": "# Skills\n- Orchestration\n- Resource Management\n- Status Tracking\n",
        "MasterBot/bot_definition/RolePolicies.md": "# Role Policies\n- Maintain clear communication logs.\n- Ensure tasks are accurately categorized.\n",
        "MasterBot/bot_definition/ProviderProfile.json": json.dumps({
            "provider": "PLACEHOLDER",
            "model": "PLACEHOLDER",
            "api_base": "",
            "api_key": "",
            "enabled": False
        }, indent=2),
        "MasterBot/bot_definition/RuntimeProfile.json": json.dumps({
            "heartbeat_seconds": 10,
            "lease_seconds": 600,
            "enabled": True,
            "processed_entries": []
        }, indent=2),
        "MasterBot/bot_definition/HarnessProfile.json": json.dumps({
            "harness": "unknown",
            "enabled": True
        }, indent=2),
        "MasterBot/bot_definition/Status.md": "# Status\nCurrent State: idle\nLast Updated: none\n",
        "MasterBot/bot_definition/Heartbeat.md": "# Heartbeat\nLast Updated: none\n",
        "MasterBot/bot_definition/Lease.json": "{}",
        "MasterBot/bot_definition/Memory.md": "# Memory\nNo recent session memories.\n",
        "MasterBot/bot_definition/Learnings.md": "# Learnings\nNo recursive insights yet.\n",
        "MasterBot/workspace/OPERATOR_NOTES.md": "# Operator Notes\n",
        "MasterBot/workspace/MASTER_TASKS.md": "# Master Tasks\n\n## Active\n\n## Blocked\n\n## Done\n",
        "MasterBot/workspace/MASTER_BOARD.md": "# Master Board\nStatus of all active initiatives.\n",
        "MasterBot/workspace/TEAM_COMMUNICATION.md": "# Team Communication\nMain log for swarm collaboration.\n",
    }

    project_files = {
        "Projects/ExampleProject/PROJECT_POINTER.json": json.dumps({"absolute_path": ""}, indent=2),
        "Projects/ExampleProject/CONTEXT.md": "# Context\nExample project for framework demonstration.\n",
        "Projects/ExampleProject/NEXT_ACTION.md": "# Next Actions\n- [ ] Configure the system\n",
        "Projects/ExampleProject/TEAM_COMMUNICATION.md": "# Team Communication\n",
        "Projects/ExampleProject/ARTIFACTS.md": "# Artifacts\n",
        "Projects/ExampleProject/KANBAN.md": "# Kanban\n",
    }

    system_files = {
        "System/SYSTEM_STATUS.md": "# System Status\nOverall State: initialized\n",
        "System/LIVE_BOTS.md": "# Live Bots\n",
        "System/ROUTING_RULES.md": "# Routing Rules\nDefine which bots handle which tasks.\n",
        "System/GLOBAL_CONTEXT.md": "# Global Context\nHigh-level system objectives.\n",
    }
    
    root_files = {
        ".gitignore": "# Ignore private credentials\n**/ProviderProfile.json\n"
    }

    all_files = {**master_bot_files, **project_files, **system_files, **root_files}

    for rel_path, content in all_files.items():
        file_path = target_root / rel_path
        if file_path.exists() and args.repair:
            continue
        create_file(file_path, content)

    print("\nPhase 1 Schema Generation Complete.")
    print(f"Target: {target_root}")
    if not args.repair and not args.overwrite:
        print("\nNext step: Run the in-system onboarding to define your MasterBot.")
        print(f"Command: py core/onboarding_cli.py --workspace {args.target}")

if __name__ == "__main__":
    main()
