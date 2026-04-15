import os
import time
import json
import psutil
from pathlib import Path
import subprocess
import re

def test_warm_boot_recovery():
    workspace = Path(r"c:\Users\info\OneDrive\Desktop\AgenticHarness\MainCode\FreezeTest")
    master_workspace = workspace / "MasterBot" / "workspace"
    master_def = workspace / "MasterBot" / "bot_definition"
    system_dir = workspace / "System"
    
    # Setup durable SystemProfile
    sp = {
        "routing_policy": "OPEN_COST",
        "durable_mode": True,
        "heartbeat_threshold_seconds": 120,
        "operating_mode": "deep"
    }
    system_dir.mkdir(parents=True, exist_ok=True)
    (system_dir / "SystemProfile.json").write_text(json.dumps(sp, indent=2), encoding="utf-8")
    
    # Setup MASTER_TASKS.md with one 'claimed' task with dead owner, and one 'in_progress' with dead owner and unmet dependencies
    tasks_content = """# Master Tasks

## Active

### Task
ID: task-boot-test-1
Status: claimed
Owner: TestBot1
Title: Claimed task test
DependsOn: none

### Task
ID: task-boot-test-2
Status: in_progress
Owner: TestBot2
Title: In Progress task test
DependsOn: task-upstream

## Done
"""
    master_workspace.mkdir(parents=True, exist_ok=True)
    (master_workspace / "MASTER_TASKS.md").write_text(tasks_content, encoding="utf-8")
    
    # Setup fake leases for TestBot1 and TestBot2
    for b in ["TestBot1", "TestBot2"]:
        bot_def = workspace / "Bots" / b / "bot_definition"
        bot_def.mkdir(parents=True, exist_ok=True)
        (bot_def / "Identity.md").write_text(f"Name: {b}\nRole: tester", encoding="utf-8")
        
        lease = {
            "lease_owner": "fakehost:99999",
            "pid": 99999
        }
        (bot_def / "Lease.json").write_text(json.dumps(lease, indent=2), encoding="utf-8")
        
        # also set stale heartbeat
        (bot_def / "Heartbeat.md").write_text("Last Updated: 2020-01-01T00:00:00Z\n", encoding="utf-8")
        
    print("Test setup complete. Spawning MasterBot iteration...")
    
    # Run MasterBot
    # We will spawn master_daemon.py and kill it after 3 seconds
    master_py = Path(r"c:\Users\info\OneDrive\Desktop\AgenticHarness\MainCode\core\master_daemon.py")
    proc = subprocess.Popen(["python", str(master_py), "--workspace", str(workspace)])
    time.sleep(3)
    proc.terminate()
    proc.wait()
    
    # Verify results
    res_content = (master_workspace / "MASTER_TASKS.md").read_text(encoding="utf-8")
    print("\n--- MASTER_TASKS.md ---")
    print(res_content)
    print("------------------------\n")
    
    m1 = re.search(r"ID:\s*task-boot-test-1\n(?:.*?\n)*?Status:\s*(\w+)", res_content)
    m2 = re.search(r"ID:\s*task-boot-test-2\n(?:.*?\n)*?Status:\s*(\w+)", res_content)
    
    s1 = m1.group(1) if m1 else "not found"
    s2 = m2.group(1) if m2 else "not found"
    
    print(f"Task 1 (no deps) resolved status: {s1}")
    print(f"Task 2 (has deps) resolved status: {s2}")
    
    assert s1.lower() == "new", "Task 1 should be 'new'"
    assert s2.lower() == "waiting", "Task 2 should be 'waiting' due to deps"
    
    print("Warm-boot recovery test passed successfully.")

if __name__ == "__main__":
    test_warm_boot_recovery()
