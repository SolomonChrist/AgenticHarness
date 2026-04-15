import json
from pathlib import Path

def test_patrol_recovery():
    workspace = Path(r"c:\Users\info\OneDrive\Desktop\AgenticHarness\MainCode\FreezeTest")
    master_py = Path(r"c:\Users\info\OneDrive\Desktop\AgenticHarness\MainCode\core\master_daemon.py")
    
    import sys
    sys.path.append(str(master_py.parent))
    from master_daemon import MasterDaemon
    
    # 1. Start with a task assigned to a dead worker
    master_workspace = workspace / "MasterBot" / "workspace"
    tasks_content = """# Master Tasks

## Active

### Task
ID: task-patrol-1
Status: in_progress
Owner: TestBot1
RetryCount: 0
Title: Stale task test
DependsOn: none

## Done
"""
    (master_workspace / "MASTER_TASKS.md").write_text(tasks_content, encoding="utf-8")
    
    daemon = MasterDaemon(str(workspace))
    # Reset durable mode if false, but test warm boot handled it
    # We want to test run_recovery_patrol, so we can isolate it
    
    # The heartbeat is stale > 120s from the previous test
    daemon.run_recovery_patrol()
    
    res = (master_workspace / "MASTER_TASKS.md").read_text(encoding="utf-8")
    print(res)
    if "Status: new" in res and "Owner: none" in res and "RetryCount: 1" in res:
        print("Recovery patrol successfully rerouted stale task.")
    else:
        print("Patrol test failed.")

if __name__ == "__main__":
    test_patrol_recovery()
