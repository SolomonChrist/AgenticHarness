import json
import time
import subprocess
from pathlib import Path

def test_durability():
    workspace = Path(r"c:\Users\info\OneDrive\Desktop\AgenticHarness\MainCode\FreezeTest")
    sp_path = workspace / "System" / "SystemProfile.json"
    
    # 1. Manually set to fast
    sp = json.loads(sp_path.read_text(encoding="utf-8"))
    sp["operating_mode"] = "fast"
    sp_path.write_text(json.dumps(sp), encoding="utf-8")
    
    print("Set SystemProfile to fast. Spawning MasterBot.")
    
    master_py = Path(r"c:\Users\info\OneDrive\Desktop\AgenticHarness\MainCode\core\master_daemon.py")
    proc = subprocess.Popen(["python", str(master_py), "--workspace", str(workspace)])
    time.sleep(3)
    proc.terminate()
    proc.wait()
    
    # Check Lease.json for active mode
    lease_path = workspace / "MasterBot" / "bot_definition" / "Lease.json"
    if lease_path.exists():
        lease = json.loads(lease_path.read_text(encoding="utf-8"))
        assert lease.get("operating_mode") == "fast", f"Expected fast, got {lease.get('operating_mode')}"
        print("Durable settings passed. MasterBot synced operating_mode successfully.")
    else:
        print("Lease not found.")
        
if __name__ == "__main__":
    test_durability()
