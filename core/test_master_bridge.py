import sys
import re
from pathlib import Path

# Simulation of the MasterDaemon logic for V4.8 Syntax Repair
class MasterDecompositionTester:
    def __init__(self):
        self.log_entries = []

    def get_iso_timestamp(self):
        return "2026-04-12T02:15:00-04:00"

    def _log(self, msg):
        self.log_entries.append(msg)

    def repair_planner_syntax(self, resp):
        """Identical to the implementation in master_daemon.py."""
        if not resp: return resp
        
        mappings = [
            (r"(?im)^Step Name:\s*", "STEP_KEY: "),
            (r"(?im)^Task:\s*", "STEP_KEY: "),
            (r"(?im)^Assigned To:\s*", "DELEGATE: "),
            (r"(?im)^Target Bot:\s*", "DELEGATE: "),
            (r"(?im)^Bot:\s*", "DELEGATE: "),
            (r"(?im)^Instructions:\s*", "BODY: "),
            (r"(?im)^Details:\s*", "BODY: "),
            (r"(?im)^Prerequisites:\s*", "DEPENDS_ON: "),
            (r"(?im)^Depends On:\s*", "DEPENDS_ON: "),
            (r"(?im)^Files Needed:\s*", "INPUTS: "),
            (r"(?im)^Files Produced:\s*", "ARTIFACTS: "),
            (r"(?im)^Output Files:\s*", "ARTIFACTS: "),
        ]
        
        repaired = resp
        applied = []
        for pat, key in mappings:
            if re.search(pat, repaired):
                repaired = re.sub(pat, key, repaired)
                applied.append(key.strip(": "))
                
        if applied:
            print(f"[{self.get_iso_timestamp()}] [REPAIR] Applied field mappings: {', '.join(applied)}")
            log_msg = (
                f"\n--- [REPAIR AUDIT] ---\n"
                f"Mappings: {', '.join(applied)}\n"
                f"Original: {resp[:50]}...\n"
                f"Repaired: {repaired[:50]}...\n"
                f"----------------------\n"
            )
            self._log(log_msg)
            
        return repaired

    def parse_delegations(self, resp):
        """Simulation of the MasterDaemon parsing loop."""
        if "DELEGATE:" not in resp:
            return []
            
        tasks = []
        blocks = re.split(r"(?=STEP_KEY:)", resp)
        for block in blocks:
            if "DELEGATE:" not in block: continue
            
            # Simple attribute extraction
            task = {}
            for key in ["STEP_KEY", "DELEGATE", "BODY", "DEPENDS_ON"]:
                m = re.search(rf"{key}:\s*(.*)", block)
                task[key] = m.group(1).strip() if m else "none"
            tasks.append(task)
        return tasks

def run_test():
    tester = MasterDecompositionTester()
    
    print("=== V4.8 MASTER BRIDGE SMOKE TEST ===")

    # FIXTURE 1: Perfect Canonical Output
    print("\n[TEST 1] Testing Perfect Canonical Output...")
    f1 = (
        "STEP_KEY: scan_vault\n"
        "DELEGATE: SecondBrainBot | Scan my vault\n"
        "BODY: Perform a full scan of the Obsidian vault.\n"
        "DEPENDS_ON: NONE\n"
    )
    r1 = tester.repair_planner_syntax(f1)
    t1 = tester.parse_delegations(r1)
    assert len(t1) == 1
    assert t1[0]["STEP_KEY"] == "scan_vault"
    assert "SecondBrainBot" in t1[0]["DELEGATE"]
    print("  SUCCESS: Canonical output parsed correctly.")

    # FIXTURE 2: Near-Miss Field Labels
    print("\n[TEST 2] Testing Near-Miss Field Labels...")
    f2 = (
        "Step Name: analyze_data\n"
        "Assigned To: ResearchBot | Analyze results\n"
        "Details: Analyze the extracted data for trends.\n"
        "Prerequisites: scan_vault\n"
    )
    r2 = tester.repair_planner_syntax(f2)
    t2 = tester.parse_delegations(r2)
    assert len(t2) == 1
    assert t2[0]["STEP_KEY"] == "analyze_data"
    assert "ResearchBot" in t2[0]["DELEGATE"]
    assert t2[0]["DEPENDS_ON"] == "scan_vault"
    print("  SUCCESS: Near-miss labels repaired and parsed correctly.")

    # FIXTURE 3: Invalid Prose-Only Output
    print("\n[TEST 3] Testing Invalid Prose-Only Output (Fail-Closed)...")
    f3 = (
        "I will have the ResearchBot look into the vault first, and then the IngestionBot "
        "will take over the processing of all the markdown files."
    )
    r3 = tester.repair_planner_syntax(f3)
    t3 = tester.parse_delegations(r3)
    assert len(t3) == 0
    print("  SUCCESS: Invalid prose correctly failed to create tasks.")

    print("\n=== ALL V4.8 BRIDGE TESTS PASSED ===")

if __name__ == "__main__":
    run_test()
