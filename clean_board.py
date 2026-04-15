import re
import os
from pathlib import Path

def clean_board(path):
    if not os.path.exists(path): return
    content = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    
    header = ""
    if "## Active" in content:
        header = content.split("## Active")[0] + "## Active\n\n"
        body = content.split("## Active")[1]
    else:
        return # Skip if no Active section
        
    # Split into blocks
    blocks = re.split(r"(?=### Task)", body)
    
    seen_ids = {}
    clean_blocks = []
    
    for block in blocks:
        if "ID:" not in block: continue
        tid_m = re.search(r"ID:\s*([^\n\r]*)", block)
        if not tid_m: continue
        tid = tid_m.group(1).strip()
        
        # Metadata cleansing
        block = re.sub(r"Preferred Bot:\s*-?\s*delegate:\s*", "Preferred Bot: ", block, flags=re.IGNORECASE)
        block = re.sub(r"InputArtifacts:\s*(ARTIFACTS|INPUTS):\s*", "InputArtifacts: ", block, flags=re.IGNORECASE)
        block = re.sub(r"DependsOn:\s*(ARTIFACTS|INPUTS):\s*", "DependsOn: ", block, flags=re.IGNORECASE)
        
        stat_m = re.search(r"Status:\s*(\w+)", block, re.IGNORECASE)
        status = stat_m.group(1).strip().lower() if stat_m else "none"
        
        # Deduplication logic: prefer new/in_progress over waiting
        if tid in seen_ids:
            old_stat = seen_ids[tid]['status']
            if status in ("new", "in_progress", "claimed") and old_stat == "waiting":
                seen_ids[tid] = {'status': status, 'block': block}
            continue
        
        seen_ids[tid] = {'status': status, 'block': block}

    # Re-assemble
    final_active = "".join([v['block'] for v in seen_ids.values()])
    
    # Restore the rest of the file (Blocked, Done)
    rest = ""
    if "## Blocked" in content:
        rest = "## Blocked" + content.split("## Blocked")[1]
    elif "## Done" in content:
        rest = "## Done" + content.split("## Done")[1]
        
    Path(path).write_text(header + final_active + "\n" + rest, encoding="utf-8")
    print(f"Cleaned {len(seen_ids)} tasks in MASTER_TASKS.md")

if __name__ == "__main__":
    clean_board(r"C:\Users\info\AgenticHarnessWork\MasterBot\workspace\MASTER_TASKS.md")
