import os
import sys
import json
import subprocess
import hashlib
import datetime
import re
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, render_template_string
from onboarding_manager import OnboardingManager
from build_bot import build_bot_files

app = Flask(__name__, static_folder='dashboard')

# Global single-user workspace target
WORKSPACE_PATH = None

def get_manager():
    if not WORKSPACE_PATH:
        return None
    try:
        return OnboardingManager(WORKSPACE_PATH)
    except Exception as e:
        print(f"Error initializing manager: {e}")
        return None

def read_file_safe(path):
    p = Path(path)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return ""

def read_json_safe(path):
    p = Path(path)
    if p.exists() and p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def list_projects(workspace_root):
    projects_dir = Path(workspace_root) / "Projects"
    projects = []
    if projects_dir.exists():
        for d in projects_dir.iterdir():
            if d.is_dir():
                ptr_path = d / "PROJECT_POINTER.json"
                real_path = ""
                if ptr_path.exists():
                    try:
                        ptr_data = json.loads(ptr_path.read_text(encoding="utf-8"))
                        real_path = ptr_data.get("absolute_path", "")
                    except:
                        pass
                projects.append({
                    "name": d.name,
                    "pointer": real_path
                })
    return projects

def parse_tasks(content):
    """
    V4 Robust Task Parsing: 
    Scans for all '### Task' blocks globally, then identifies Section 
    by searching backwards for the nearest '##' header.
    """
    tasks = []
    # Find all task starting positions
    task_starts = [m.start() for m in re.finditer(r"###\s+Task", content, re.IGNORECASE)]
    
    for i in range(len(task_starts)):
        start_pos = task_starts[i]
        end_pos = task_starts[i+1] if i+1 < len(task_starts) else len(content)
        block = content[start_pos:end_pos]
        
        # 1. Determine Section (Status Category)
        # Search backwards from start_pos for the nearest '## '
        prefix = content[:start_pos]
        section_matches = list(re.finditer(r"##\s+(.*)", prefix))
        section_name = section_matches[-1].group(1).strip() if section_matches else "Unknown"
        
        def _field(pattern, default=""):
            m = re.search(pattern, block, re.IGNORECASE)
            return m.group(1).strip() if m else default

        tid = _field(r"ID:\s*([^\s\r\n]*)")
        if not tid: continue

        status_raw = _field(r"Status:\s*(\w+)", "active")

        # Body extraction: Capture everything from Body: until the next field or empty line
        body_m = re.search(r"Body:\s*(.*?)(?=\n[A-Z][a-zA-Z]+:|\n\s*\n|\Z)", block, re.DOTALL | re.IGNORECASE)
        body = body_m.group(1).strip() if body_m else _field(r"Body:\s*(.*)")

        tasks.append({
            "id":               tid,
            "title":            _field(r"Title:\s*(.*)", "Untitled"),
            "body":             body,
            "status":           status_raw.lower(),
            "owner":            _field(r"Owner:\s*(.*)", "none"),
            "pref_bot":         _field(r"Preferred Bot:\s*(.*)", "none"),
            "priority":         _field(r"Priority:\s*(.*)", "normal"),
            "routing_policy":   _field(r"Routing Policy:\s*(.*)", "unknown"),
            "selection_reason": _field(r"(?:Selection Reason|Reason):\s*(.*)", ""),
            "cost_tier":        _field(r"Cost Tier:\s*(.*)", "N/A"),
            "retry_count":      _field(r"RetryCount:\s*(\d+)", "0"),
            "original_bot":     _field(r"OriginalBot:\s*(.*)", ""),
            "rerouted_from":    _field(r"ReroutedFrom:\s*(.*)", ""),
            "reroute_reason":   _field(r"RerouteReason:\s*(.*)", ""),
            "blocked_reason":   _field(r"BlockedReason:\s*(.*)", ""),
            "eval_fail_reason": _field(r"EvalFailReason:\s*(.*)", ""),
            "completed_at":     _field(r"CompletedAt:\s*(.*)", ""),
            "cancelled_at":     _field(r"CancelledAt:\s*(.*)", ""),
            "inputs":           _field(r"InputArtifacts:\s*(.*)", "none"),
            "outputs":          _field(r"OutputArtifacts:\s*(.*)", "none"),
            "section":          section_name,
        })
    return tasks

def parse_team_comms(content):
    """
    V4.1 Robust Chat Parsing:
    Separates metadata from body by finding the line break after the header block.
    """
    if not content: return []
    comms = []
    # Split on the message delimiter, handling potential line ending variations
    blocks = re.split(r"##\s+Message", content, flags=re.IGNORECASE)
    for block in blocks[1:]:
        def _field(p, d=""):
            m = re.search(p, block, re.IGNORECASE)
            return m.group(1).strip() if m else d

        lines = block.strip().splitlines()
        header_end_idx = -1
        
        # V12.1 FTUE Fix: Robustly find the end of the header block
        for i, line in enumerate(lines):
            if ":" in line[:30] and any(h in line for h in ["Timestamp", "Sender", "Type", "Project", "Task"]):
                header_end_idx = i
            elif not line.strip():
                if header_end_idx != -1: # We have seen at least one header, and now hit a blank line
                    break
                continue
            else:
                break
        
        body = "\n".join(lines[header_end_idx+1:]).strip()
        
        comms.append({
            "ts": _field(r"Timestamp:\s*(.*)"),
            "sender": _field(r"Sender:\s*(.*)", "Unknown"),
            "type": _field(r"Type:\s*(.*)", "unknown"),
            "project": _field(r"Project:\s*(.*)", "none"),
            "task_id": _field(r"Task:\s*(.*)", "none"),
            "body": body
        })
    return comms


def update_master_tasks(workspace_path, task_id, action):
    path = Path(workspace_path) / "MasterBot" / "workspace" / "MASTER_TASKS.md"
    if not path.exists(): return False, "MASTER_TASKS.md not found"

    content = path.read_text(encoding="utf-8").replace("\r\n", "\n")

    task_regex = rf"### Task\nID:\s*{re.escape(task_id)}(.*?)(?=\n### Task|\n## |\Z)"
    match = re.search(task_regex, content, re.DOTALL)
    if not match: return False, f"Task {task_id} not found"

    block_full = "### Task\nID: " + task_id + match.group(1)
    new_block = block_full
    target_section = None
    ts = datetime.datetime.now().astimezone().isoformat(timespec='seconds')

    if action == "cancel":
        new_block = re.sub(r"Status:\s*(.*)", "Status: cancelled", new_block)
        if "CancelledAt:" in new_block:
            new_block = re.sub(r"CancelledAt:\s*(.*)", f"CancelledAt: {ts}", new_block)
        else:
            new_block = new_block.strip() + f"\nCancelledAt: {ts}\n"
        target_section = "Cancelled"
    elif action == "done":
        new_block = re.sub(r"Status:\s*(.*)", "Status: done", new_block)
        target_section = "Done"
    elif action == "block":
        new_block = re.sub(r"Status:\s*(.*)", "Status: blocked", new_block)
        target_section = "Blocked"
    elif action == "archive":
        new_content = content.replace(block_full, "").strip()
        path.write_text(new_content, encoding="utf-8", newline="\n")
        return True, "archived"

    if target_section:
        new_content = content.replace(block_full, "").strip()
        new_content = re.sub(r"\n\s*\n\s*\n", "\n\n", new_content)
        section_header = f"## {target_section}"
        if section_header not in new_content:
            new_content += f"\n\n{section_header}\n"
        lines = new_content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().lower() == section_header.lower():
                lines.insert(i + 1, "")
                lines.insert(i + 2, new_block.strip())
                break
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return True, action

    return False, "unknown action"


ALLOWED_BOT_FILES = {
    "Identity.md", "Soul.md", "Skills.md", "RolePolicies.md", 
    "Memory.md", "Learnings.md", "Status.md", "Heartbeat.md", 
    "Lease.json", "HarnessProfile.json", "ProviderProfile.json", "RuntimeProfile.json"
}

def get_bot_path(bot_name):
    if bot_name == "MasterBot":
        return Path(WORKSPACE_PATH) / "MasterBot"
    return Path(WORKSPACE_PATH) / "Bots" / bot_name

@app.route("/api/bots", methods=["GET"])
def list_bots():
    if not WORKSPACE_PATH: return jsonify({"bots": []})
    bots = ["MasterBot"] if (Path(WORKSPACE_PATH) / "MasterBot").exists() else []
    bots_dir = Path(WORKSPACE_PATH) / "Bots"
    if bots_dir.exists():
        for d in bots_dir.iterdir():
            if d.is_dir() and not d.name.startswith('_'):
                bots.append(d.name)
    return jsonify({"bots": bots})

@app.route("/api/bot/<bot_name>/file/<filename>", methods=["GET"])
def get_bot_file(bot_name, filename):
    if not WORKSPACE_PATH: return jsonify({"error": "No workspace"}), 400
    if filename not in ALLOWED_BOT_FILES: return jsonify({"error": "Unauthorized file"}), 403
    
    bot_dir = get_bot_path(bot_name)
    file_path = bot_dir / "bot_definition" / filename
    
    if not file_path.exists():
        return jsonify({"content": ""})
        
    content = file_path.read_text(encoding="utf-8")
    return jsonify({"content": content})

@app.route("/api/bot/<bot_name>/file/<filename>", methods=["POST"])
def save_bot_file(bot_name, filename):
    if not WORKSPACE_PATH: return jsonify({"error": "No workspace"}), 400
    if filename not in ALLOWED_BOT_FILES: return jsonify({"error": "Unauthorized file"}), 403
    
    content = request.json.get("content", "")
    bot_dir = get_bot_path(bot_name)
    file_path = bot_dir / "bot_definition" / filename
    

    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
    file_path.write_text(content, encoding="utf-8", newline="\n")
    return jsonify({"success": True})

@app.route("/")
def index():
    # Serve index.html from static_folder
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/api/workspace", methods=["GET"])
def get_workspace():
    return jsonify({"workspace": str(WORKSPACE_PATH) if WORKSPACE_PATH else ""})

@app.route("/api/workspace", methods=["POST"])
def set_workspace():
    global WORKSPACE_PATH
    data = request.json
    path_str = data.get("workspace", "")
    create_mode = data.get("create", False)
    
    if not path_str:
        return jsonify({"success": False, "error_type": "missing", "error": "Path cannot be empty"}), 400
        
    p = Path(path_str).resolve()
    
    try:
        if create_mode:
            p.mkdir(parents=True, exist_ok=True)
            import subprocess
            import sys
            setup_script = Path(__file__).parent.parent / "setup.py"
            subprocess.run([sys.executable, str(setup_script), "--target", str(p)], check=True)
            WORKSPACE_PATH = p
            return jsonify({"success": True, "workspace": str(WORKSPACE_PATH)})
            
        if not p.exists():
            return jsonify({"success": False, "error_type": "missing", "error": "Path does not exist"}), 400
            
        if not p.is_dir():
            return jsonify({"success": False, "error_type": "not_dir", "error": "Path is not a directory"}), 400
            
        # Optional: loosely check if it has been initialized by setup.py
        if not (p / "MasterBot").exists() and not (p / "Projects").exists():
            return jsonify({"success": False, "error_type": "uninitialized", "error": "Workspace is not initialized"}), 400
            
        WORKSPACE_PATH = p
        return jsonify({"success": True, "workspace": str(WORKSPACE_PATH)})
        
    except Exception as e:
        return jsonify({"success": False, "error_type": "internal", "error": f"Failed to initialize workspace: {str(e)}"}), 500

@app.route("/api/status", methods=["GET"])
def get_status():
    manager = get_manager()
    if not manager:
        return jsonify({"workspace_set": False})
    
    is_onboarded = manager.is_onboarded()
    state = manager.get_state() if not is_onboarded else {}
    return jsonify({
        "workspace_set": True,
        "is_onboarded": is_onboarded,
        "onboarding_state": state
    })

@app.route("/api/onboard/step", methods=["POST"])
def next_onboard_step():
    manager = get_manager()
    if not manager:
        return jsonify({"error": "Workspace not set"}), 400
    
    data = request.json
    step = data.get("step")
    state_data = data.get("data", {})
    
    try:
        next_step = manager.process_step(step, state_data)
        if next_step == 6:  # Finalize returns 6
            return jsonify({"complete": True})
        return jsonify({"next_step": next_step})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_readiness_data(workspace_path):
    # Categorical Readiness Check (Dashboard Level)
    unconfigured_bots = []
    runnable_workers = 0
    bots_dir = Path(workspace_path) / "Bots"
    if bots_dir.exists():
        for d in bots_dir.iterdir():
            if d.is_dir() and not d.name.startswith('_'):
                prof = read_json_safe(d / "bot_definition" / "ProviderProfile.json")
                if prof.get("provider") == "PLACEHOLDER" or prof.get("model") == "PLACEHOLDER":
                    unconfigured_bots.append(d.name)
                elif prof.get("enabled", False):
                    runnable_workers += 1
                    
    master_prof = read_json_safe(Path(workspace_path) / "MasterBot" / "bot_definition" / "ProviderProfile.json")
    master_ok = master_prof.get("provider") != "PLACEHOLDER" and master_prof.get("model") != "PLACEHOLDER"
    
    # Check SystemState.json for daemon-verified readiness
    state = read_json_safe(Path(workspace_path) / "System" / "SystemState.json")
    daemon_status = state.get("readiness_category", "UNKNOWN")
    daemon_exp = state.get("readiness_explanation", "")

    explanation = ""
    state_cat = "UNKNOWN"
    
    if not master_ok:
        state_cat = "NOT READY"
        explanation = "WELCOME: Step 1 - Ensure MasterBot is configured in 'Configuration'."
    elif runnable_workers == 0:
        state_cat = "NOT READY"
        explanation = "GETTING STARTED: Step 2 - Enable your specialists in 'Bot Management'."
    else:
        # V12.1 Hardened Heartbeat Check
        sys_status_path = Path(workspace_path) / "System" / "SYSTEM_STATUS.md"
        sys_status = read_file_safe(sys_status_path)
        
        # Check MasterBot specifically
        is_active = "MasterBot: active" in sys_status
        last_master_update = 99999
        
        if is_active:
            try:
                # Extract timestamp from SYSTEM_STATUS
                m = re.search(r"Master Pulsed:\s*(.*)", sys_status, re.IGNORECASE)
                if m:
                    last_time = datetime.datetime.fromisoformat(m.group(1).strip())
                    last_master_update = (datetime.datetime.now().astimezone() - last_time).total_seconds()
            except: pass

        if not is_active or last_master_update > 60:
            state_cat = "NOT READY"
            explanation = "MASTERBOT OFFLINE: You must run 'py core/master_daemon.py' in your terminal."
        else:
            state_cat = "READY"
            explanation = "SYSTEM ONLINE: Awaiting instructions."

    return {
        "state": state_cat if daemon_status == "UNKNOWN" else daemon_status,
        "master_ok": master_ok,
        "runnable_workers": runnable_workers,
        "unconfigured": unconfigured_bots,
        "explanation": daemon_exp if daemon_exp else explanation,
        "daemon_verified": daemon_status != "UNKNOWN"
    }

def build_visualizer_state(workspace_path):
    workspace_path = Path(workspace_path)
    readiness = get_readiness_data(workspace_path)
    tasks_raw = read_file_safe(workspace_path / "MasterBot" / "workspace" / "MASTER_TASKS.md")
    parsed_tasks = parse_tasks(tasks_raw)
    comms_raw = read_file_safe(workspace_path / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md")
    parsed_comms = parse_team_comms(comms_raw)
    sys_state = read_json_safe(workspace_path / "System" / "SystemState.json")

    ident = read_file_safe(workspace_path / "MasterBot" / "bot_definition" / "Identity.md")
    master_provider = read_json_safe(workspace_path / "MasterBot" / "bot_definition" / "ProviderProfile.json")
    master_status = read_file_safe(workspace_path / "MasterBot" / "bot_definition" / "Status.md")
    master_hb = read_file_safe(workspace_path / "MasterBot" / "bot_definition" / "Heartbeat.md")

    def _field(text, pattern, default=""):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    def _normalize_status(raw_status):
        status = (raw_status or "").strip().lower()
        mapping = {
            "new": "queue",
            "waiting": "queue",
            "claimed": "working",
            "active": "working",
            "in_progress": "working",
            "done": "done",
            "blocked": "blocked",
            "cancelled": "cancelled",
        }
        return mapping.get(status, status or "idle")

    bots = []
    tasks_by_owner = {}
    for task in parsed_tasks:
        owner = (task.get("owner") or "").strip()
        pref = (task.get("pref_bot") or "").strip()
        bucket_name = owner if owner and owner.lower() != "none" else pref
        if not bucket_name or bucket_name.lower() == "none":
            continue
        current = tasks_by_owner.get(bucket_name.lower())
        priority = {"working": 4, "queue": 3, "blocked": 2, "done": 1}.get(_normalize_status(task.get("status")), 0)
        if not current or priority >= current["priority"]:
            tasks_by_owner[bucket_name.lower()] = {
                "title": task.get("title") or "Untitled Task",
                "status": _normalize_status(task.get("status")),
                "body": task.get("body") or "",
                "priority": priority,
                "task_id": task.get("id") or "",
            }

    master_name = _field(ident, r"Name:\s*(.*)", "MasterBot")
    master_role = _field(ident, r"Role:\s*(.*)", "Orchestrator")
    master_focus = _field(master_status, r"Current Focus:\s*(.*)", "idle")
    master_state = _field(master_status, r"Current State:\s*(.*)", "idle")
    master_activity = _field(master_hb, r"Current Activity:\s*(.*)", master_focus or "idle")
    master_mode = _field(master_hb, r"Mode:\s*(.*)", "inactive")
    master_task = tasks_by_owner.get(master_name.lower()) or tasks_by_owner.get("masterbot")
    bots.append({
        "id": "masterbot",
        "name": master_name,
        "role": master_role,
        "provider": master_provider.get("provider", "unknown"),
        "model": master_provider.get("model", "unknown"),
        "harness": "orchestrator",
        "local_cloud": "Cloud" if master_provider.get("provider") not in ("lmstudio", "ollama") else "Local",
        "staff_type": "Core",
        "status": _normalize_status(master_task["status"] if master_task else master_state),
        "focus": master_task["title"] if master_task else master_focus,
        "activity": master_activity,
        "mode": master_mode,
        "heartbeat_age": sys_state.get("master_age_seconds", 0),
        "blockers": _field(master_status, r"Blockers:\s*(.*)", "none"),
        "task_id": master_task["task_id"] if master_task else "",
        "task_body": master_task["body"] if master_task else "",
        "is_master": True,
    })

    bots_dir = workspace_path / "Bots"
    if bots_dir.exists():
        for d in bots_dir.iterdir():
            if not d.is_dir() or d.name.startswith('_'):
                continue
            sid_content = read_file_safe(d / "bot_definition" / "Identity.md")
            st_content = read_file_safe(d / "bot_definition" / "Status.md")
            hb_content = read_file_safe(d / "bot_definition" / "Heartbeat.md")
            prov_prof = read_json_safe(d / "bot_definition" / "ProviderProfile.json")

            bot_name = _field(sid_content, r"Name:\s*(.*)", d.name)
            bot_role = _field(sid_content, r"Role:\s*(.*)", "Specialist")
            bot_harness = _field(sid_content, r"Harness:\s*(.*)", "base-python")
            bot_task = tasks_by_owner.get(bot_name.lower()) or tasks_by_owner.get(d.name.lower())
            hb_age = 9999
            hb_ts = _field(hb_content, r"Last Updated:\s*(.*)", "")
            if hb_ts and hb_ts.lower() != "none":
                try:
                    hb_age = int((datetime.datetime.now().astimezone() - datetime.datetime.fromisoformat(hb_ts)).total_seconds())
                except Exception:
                    hb_age = 9999

            provider = prov_prof.get("provider", "unknown")
            is_local = provider.lower() in ("lmstudio", "ollama") or "localhost" in (prov_prof.get("api_base", "") or "").lower()

            bots.append({
                "id": d.name.lower(),
                "name": bot_name,
                "role": bot_role,
                "provider": provider,
                "model": prov_prof.get("model", "unknown"),
                "harness": bot_harness,
                "local_cloud": "Local" if is_local else "Cloud",
                "staff_type": "Starter" if d.name in ("LocalBot1", "ResearchBot", "IngestionBot", "SecondBrainBot") else "Custom",
                "status": _normalize_status(bot_task["status"] if bot_task else _field(st_content, r"Current State:\s*(.*)", "idle")),
                "focus": bot_task["title"] if bot_task else _field(st_content, r"Current Focus:\s*(.*)", "idle"),
                "activity": _field(hb_content, r"Current Activity:\s*(.*)", "idle"),
                "mode": _field(hb_content, r"Mode:\s*(.*)", "inactive"),
                "heartbeat_age": hb_age,
                "blockers": _field(st_content, r"Blockers:\s*(.*)", "none"),
                "task_id": bot_task["task_id"] if bot_task else "",
                "task_body": bot_task["body"] if bot_task else "",
                "is_master": False,
            })

    feed = []
    for msg in parsed_comms[-24:]:
        sender = msg.get("sender", "Unknown")
        body = (msg.get("body") or "").strip()
        if len(body) > 280:
            body = body[:277] + "..."
        feed.append({
            "timestamp": msg.get("ts", ""),
            "sender": sender,
            "type": msg.get("type", "note"),
            "body": body,
        })

    summary = {
        "ready_state": readiness["state"],
        "ready_explanation": readiness["explanation"],
        "bot_count": len(bots),
        "working_count": sum(1 for b in bots if b["status"] == "working"),
        "blocked_count": sum(1 for b in bots if b["status"] == "blocked"),
        "done_count": sum(1 for t in parsed_tasks if _normalize_status(t.get("status")) == "done"),
        "queue_count": sum(1 for t in parsed_tasks if _normalize_status(t.get("status")) == "queue"),
    }

    return {
        "workspace_path": str(workspace_path),
        "summary": summary,
        "bots": bots,
        "feed": feed,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
    }

@app.route("/api/data", methods=["GET"])
def get_data():
    if not WORKSPACE_PATH:
        return jsonify({"error": "Workspace not set"}), 400
        
    # Dynamic Identity Discovery
    status_content = read_file_safe(WORKSPACE_PATH / "System" / "SYSTEM_STATUS.md")
    master_ident = read_file_safe(WORKSPACE_PATH / "MasterBot" / "bot_definition" / "Identity.md")
    master_name = re.search(r"Name:\s*(.*)", master_ident, re.IGNORECASE)
    master_role = re.search(r"Role:\s*(.*)", master_ident, re.IGNORECASE)
    
    bot_activity = "Idle"
    activity_match = re.search(r"Last Meaningful Action:\s*(.*)", status_content)
    if activity_match: bot_activity = activity_match.group(1).strip()
    
    lease_path = WORKSPACE_PATH / "MasterBot" / "bot_definition" / "Lease.json"
    bot_mode = "fast"
    if lease_path.exists():
        try:
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            # V12.1 FIX 4: Preferred source is SystemProfile, but for UI we check lease
            # V12.1 FIX: Check if there's an Operator instruction waiting for a dead MasterBot
            comm_raw = read_file_safe(WORKSPACE_PATH / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md")
            latest_comm = parse_team_comms(comm_raw)[-1:]
            pending_instruction = False
            if latest_comm and latest_comm[0]['sender'].lower() == 'operator':
                # If there's an operator message, check if its body exists in any task description or title
                tasks_raw = read_file_safe(WORKSPACE_PATH / "MasterBot" / "workspace" / "MASTER_TASKS.md")
                # Simple check: if MASTER_TASKS is empty but we have an instruction, it's definitely pending
                if not tasks_raw.strip() or len(tasks_raw.splitlines()) < 5:
                    pending_instruction = True
            
            data["pending_instruction"] = pending_instruction
            data["bot_mode"] = lease.get("operating_mode", "fast")
        except: pass
    swarm_roster = []
    bots_dir = WORKSPACE_PATH / "Bots"
    if bots_dir.exists():
        for d in bots_dir.iterdir():
            if d.is_dir() and not d.name.startswith('_'):
                sid_path = d / "bot_definition" / "Identity.md"
                st_path = d / "bot_definition" / "Status.md"
                sid_content = read_file_safe(sid_path)
                status_content_bot = read_file_safe(st_path)
                
                s_name = re.search(r"Name:\s*(.*)", sid_content, re.IGNORECASE)
                s_role = re.search(r"Role:\s*(.*)", sid_content, re.IGNORECASE)
                hb_ts = re.search(r"Heartbeat:\s*(.*)", status_content_bot, re.IGNORECASE)
                hb_mode = re.search(r"Mode:\s*(.*)", status_content_bot, re.IGNORECASE)
                st_state = re.search(r"Status:\s*(.*)", status_content_bot, re.IGNORECASE)
                st_block = re.search(r"Blocked Reason:\s*(.*)", status_content_bot, re.IGNORECASE)

                # Heartbeat Age calc
                hb_age = "infinite"
                if hb_ts:
                    try:
                        hb_time = datetime.fromisoformat(hb_ts.group(1).strip())
                        diff = datetime.now() - hb_time
                        hb_age = int(diff.total_seconds())
                    except: pass

                # S: Staffing Visibility Extraction
                prov_prof = read_json_safe(d / "bot_definition" / "ProviderProfile.json")
                provider = prov_prof.get("provider", "unknown")
                is_local = provider.lower() in ("lmstudio", "ollama") or "localhost" in prov_prof.get("api_base", "").lower()
                
                swarm_roster.append({
                    "name": s_name.group(1).strip() if s_name else d.name,
                    "role": s_role.group(1).strip() if s_role else "Specialist",
                    "folder": d.name,
                    "provider": provider,
                    "model": prov_prof.get("model", "unknown"),
                    "harness": h_mode.group(1).strip() if (h_mode := re.search(r"Harness:\s*(.*)", sid_content, re.IGNORECASE)) else "base-python",
                    "local_cloud": "Local" if is_local else "Cloud",
                    "staff_type": "Starter" if d.name in ("LocalBot1", "ResearchBot", "IngestionBot", "SecondBrainBot") else "Custom",
                    "heartbeat": hb_ts.group(1).strip() if hb_ts else "none",
                    "heartbeat_age": hb_age,
                    "mode": hb_mode.group(1).strip() if hb_mode else "inactive",
                    "status": st_state.group(1).strip() if st_state else "unknown",
                    "blockers": st_block.group(1).strip() if st_block else "none",
                    "is_runnable": prov_prof.get("enabled", False) and provider != "PLACEHOLDER"
                })

    tasks_raw = read_file_safe(WORKSPACE_PATH / "MasterBot" / "workspace" / "MASTER_TASKS.md")
    parsed_tasks = parse_tasks(tasks_raw)
    comms_raw = read_file_safe(WORKSPACE_PATH / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md")
    parsed_comms = parse_team_comms(comms_raw)

    readiness = get_readiness_data(WORKSPACE_PATH)
    
    data = {
        "master_name": master_name.group(1).strip() if master_name else "MasterBot",
        "master_role": master_role.group(1).strip() if master_role else "Orchestrator",
        "readiness": readiness,
        "swarm_roster": swarm_roster,
        "status": status_content,
        "bot_activity": bot_activity,
        "bot_mode": bot_mode,
        "live_bots": read_file_safe(WORKSPACE_PATH / "System" / "LIVE_BOTS.md"),
        "master_board": read_file_safe(WORKSPACE_PATH / "MasterBot" / "workspace" / "MASTER_BOARD.md"),
        "master_tasks": tasks_raw,
        "parsed_tasks": parsed_tasks,
        "team_communication": comms_raw,
        "parsed_comms": parsed_comms,
        "diagnostics": {
            "tasks_total": len(parsed_tasks),
            "comms_total": len(parsed_comms),
            "raw_tasks_size": len(tasks_raw),
            "raw_comms_size": len(comms_raw)
        },
        "operator_notes": read_file_safe(WORKSPACE_PATH / "MasterBot" / "workspace" / "OPERATOR_NOTES.md"),
        "projects": list_projects(WORKSPACE_PATH),
        "workspace_path": str(WORKSPACE_PATH),
        "routing_policy": read_json_safe(WORKSPACE_PATH / "System" / "SystemProfile.json").get("routing_policy", "OPEN_COST")
    }
    return jsonify(data)

@app.route("/api/visualizer_state", methods=["GET"])
def get_visualizer_state():
    if not WORKSPACE_PATH:
        return jsonify({"error": "Workspace not set"}), 400
    return jsonify(build_visualizer_state(WORKSPACE_PATH))

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Dedicated fast-poll tasks endpoint — returns parsed task list + summary counters."""
    if not WORKSPACE_PATH:
        return jsonify({"error": "Workspace not set"}), 400
    tasks_raw = read_file_safe(Path(WORKSPACE_PATH) / "MasterBot" / "workspace" / "MASTER_TASKS.md")
    parsed = parse_tasks(tasks_raw)
    # Summary counters for the board header
    by_status = {}
    for t in parsed:
        s = t["status"]
        by_status[s] = by_status.get(s, 0) + 1
    active_count = sum(by_status.get(s, 0) for s in ("new", "active", "claimed", "in_progress"))
    # Also include SystemState if available
    state = read_json_safe(Path(WORKSPACE_PATH) / "System" / "SystemState.json")
    return jsonify({
        "tasks": parsed,
        "summary": {
            "active": active_count,
            "blocked": by_status.get("blocked", 0),
            "done": by_status.get("done", 0),
            "cancelled": by_status.get("cancelled", 0),
            "waiting": by_status.get("waiting", 0),
            "total": len(parsed),
        },
        "diagnostics": {
            "tasks_total": len(parsed),
        },
        "system_state": state,
    })

@app.route("/api/health", methods=["GET"])
def get_health():
    """Health check returning master/worker ages and runnable counts (Blocker 3)."""
    if not WORKSPACE_PATH: return jsonify({"status": "unconfigured"}), 200
    
    hb_path = WORKSPACE_PATH / "MasterBot" / "bot_definition" / "Heartbeat.md"
    master_age = 9999
    if hb_path.exists():
        # V12.1 FIX 3: Parse timestamp from file content for maximum reliability
        content = read_file_safe(hb_path)
        ts_match = re.search(r"Last Updated:\s*(.*)", content, re.IGNORECASE)
        if ts_match:
            try:
                hb_time = datetime.datetime.fromisoformat(ts_match.group(1).strip())
                now = datetime.datetime.now().astimezone()
                master_age = (now - hb_time).total_seconds()
            except: 
                # Fallback to mtime if parse fails
                mtime = datetime.datetime.fromtimestamp(hb_path.stat().st_mtime).astimezone()
                master_age = (datetime.datetime.now().astimezone() - mtime).total_seconds()
    
    # Discovery loop for runnable workers
    runnable_count = 0
    worker_stats = {}
    
    sys_profile = read_json_safe(WORKSPACE_PATH / "System" / "SystemProfile.json")
    threshold = sys_profile.get("heartbeat_threshold_seconds", 120)
    
    bots_dir = WORKSPACE_PATH / "Bots"
    if bots_dir.exists():
        for d in bots_dir.iterdir():
            if d.is_dir() and not d.name.startswith('_'):
                prof = read_json_safe(d / "bot_definition" / "ProviderProfile.json")
                bhb = d / "bot_definition" / "Heartbeat.md"
                age = 9999
                if bhb.exists():
                    # V12.1 FIX 3: Timezone-aware local mtime comparison
                    mtime = datetime.datetime.fromtimestamp(bhb.stat().st_mtime).astimezone()
                    age = (datetime.datetime.now().astimezone() - mtime).total_seconds()
                
                is_runnable = prof.get("enabled", False) and prof.get("provider") != "PLACEHOLDER"
                if is_runnable: runnable_count += 1
                
                worker_stats[d.name] = {"age": age, "runnable": is_runnable, "stale": age > threshold}

    readiness = get_readiness_data(WORKSPACE_PATH)

    return jsonify({
        "status": "online" if master_age < threshold else "stale",
        "master_age": master_age,
        "runnable_workers": runnable_count,
        "worker_stats": worker_stats,
        "readiness": readiness,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/api/tasks/action", methods=["POST"])
def task_action():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    data = request.json
    task_id = data.get("taskId")
    action = data.get("action")

    success, msg = update_master_tasks(WORKSPACE_PATH, task_id, action)
    if success:
        return jsonify({"success": True, "msg": msg})
    return jsonify({"success": False, "error": msg}), 404


@app.route("/api/tasks/archive", methods=["GET"])
def get_task_archive():
    if not WORKSPACE_PATH:
        return jsonify({"error": "Workspace not set"}), 400
    archive_raw = read_file_safe(Path(WORKSPACE_PATH) / "MasterBot" / "workspace" / "MASTER_TASKS_ARCHIVE.md")
    parsed = parse_tasks(archive_raw)
    return jsonify({
        "tasks": parsed,
        "total": len(parsed)
    })

@app.route("/api/bots/create", methods=["POST"])
def create_bot():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    
    data = request.json
    name = data.get("name")
    role = data.get("role", "specialist")
    harness = data.get("harness", "claude-code")
    provider = data.get("provider", "openai")
    model = data.get("model", "gpt-4-turbo")
    style = data.get("style", "proactive")
    skills = data.get("skills", "")
    tools = data.get("tools", "")
    work_types = data.get("work_types", "")
    
    if not name: return jsonify({"error": "Bot name is required"}), 400
    
    target_dir = WORKSPACE_PATH / "Bots" / name
    
    try:
        build_bot_files(
            name=name,
            target_dir=str(target_dir),
            role=role,
            harness=harness,
            model=model,
            style=style,
            provider=provider,
            skills_text=skills,
            tools_text=tools,
            work_types_text=work_types,
            overwrite=False
        )
        return jsonify({"success": True, "bot": name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/bot/mode", methods=["POST"])
def toggle_bot_mode():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    
    mode = request.json.get("mode", "fast")
    if mode not in ["fast", "deep"]: return jsonify({"error": "Invalid mode"}), 400
    
    # Update RuntimeProfile.json
    runtime_path = WORKSPACE_PATH / "MasterBot" / "bot_definition" / "RuntimeProfile.json"
    if runtime_path.exists():
        try:
            profile = json.loads(runtime_path.read_text(encoding="utf-8"))
            profile["operating_mode"] = mode
            runtime_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        except: pass
        
    # FIX 4: Update SystemProfile.json (Durable Persistence)
    system_path = WORKSPACE_PATH / "System" / "SystemProfile.json"
    if system_path.exists():
        try:
            sp = json.loads(system_path.read_text(encoding="utf-8"))
            sp["operating_mode"] = mode
            system_path.write_text(json.dumps(sp, indent=2), encoding="utf-8")
        except: pass
        
    # Also update Lease if exists for immediate UI feedback
    lease_path = WORKSPACE_PATH / "MasterBot" / "bot_definition" / "Lease.json"
    if lease_path.exists():
        try:
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            lease["operating_mode"] = mode
            lease_path.write_text(json.dumps(lease, indent=2), encoding="utf-8")
        except: pass
        
    return jsonify({"success": True, "mode": mode})

@app.route("/api/entry", methods=["POST"])
def post_entry():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    msg = request.json.get("message", "").strip()
    if not msg: return jsonify({"error": "Empty message"}), 400
    
    notes_path = WORKSPACE_PATH / "MasterBot" / "workspace" / "OPERATOR_NOTES.md"
    current = read_file_safe(notes_path)
    
    ts = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    entry = f"\n## Entry\nTimestamp: {ts}\nOperator: Operator\nStatus: new\n\n{msg}\n"
    
    if current and not current.endswith("\n"): current += "\n"
    notes_path.write_text(current + entry, encoding="utf-8", newline="\n")
    
    # Also inject the entry into the universal chat room
    comms_path = WORKSPACE_PATH / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md"
    comms_current = read_file_safe(comms_path)
    comms_entry = f"\n## Message\nTimestamp: {ts}\nSender: Operator\nType: instruction\nProject: none\nTask: none\n\n{msg}\n"
    if comms_current and not comms_current.endswith("\n"): comms_current += "\n"
    if comms_path.exists():
        comms_path.write_text(comms_current + comms_entry, encoding="utf-8", newline="\n")
        
    # Trigger MasterBot instantly
    trigger_path = WORKSPACE_PATH / "System" / ".master_trigger"
    trigger_path.touch()
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [DASHBOARD] Sent reactive trigger to MasterBot.")
    
    return jsonify({"success": True})

@app.route("/api/projects/register", methods=["POST"])
def register_project():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    name = request.json.get("name", "").strip()
    abs_path = request.json.get("path", "").strip()
    if not name: return jsonify({"error": "Project name required"}), 400

    manager = get_manager()
    manager.write_file(f"Projects/{name}/PROJECT_POINTER.json", json.dumps({"absolute_path": abs_path}, indent=2))
    manager.write_file(f"Projects/{name}/CONTEXT.md", f"# Context\n{name} Project\n")
    manager.write_file(f"Projects/{name}/TEAM_COMMUNICATION.md", "# Team Communication\n")
    
    return jsonify({"success": True})

@app.route("/api/system/policy", methods=["POST"])
def set_routing_policy():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    policy = request.json.get("policy", "OPEN_COST")
    
    ppath = WORKSPACE_PATH / "System" / "SystemProfile.json"
    try:
        data = read_json_safe(ppath)
        data["routing_policy"] = policy
        ppath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return jsonify({"success": True, "policy": policy})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/action", methods=["POST"])
def run_action():
    # Bridge for backup/restore
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    
    action = request.json.get("action")
    target = request.json.get("target", "full")
    subtarget = request.json.get("subtarget", "")
    
    try:
        if action == "backup":
            cmd = [sys.executable, str(Path(__file__).parent / "backup_system.py"), "--workspace", str(WORKSPACE_PATH), "--type", target]
            if target == "bot" and subtarget: cmd.extend(["--bot", subtarget])
            if target == "project" and subtarget: cmd.extend(["--project", subtarget])
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return jsonify({"success": True, "message": "Backup completed"})
        elif action == "kill_all" or action == "restart_daemons":
            import psutil
            import subprocess
            killed = 0
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = p.info.get('cmdline', [])
                    if cmdline:
                        cmd_str = " ".join(cmdline).lower()
                        if "master_daemon.py" in cmd_str or "worker_daemon.py" in cmd_str:
                            # V12.1.3 LOGGING: Trace trigger detection
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [DASHBOARD] Cleanup trigger detected.")
                            p.terminate()
                            killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if action == "restart_daemons":
                m_path = Path(__file__).parent / "master_daemon.py"
                w_path = Path(__file__).parent / "worker_daemon.py"
                spawned = []
                
                # 1. Spawn Master
                if os.name == 'nt':
                    # V12.1 HARDENING: Use /k so the console stays open if it crashes (No more silent failures)
                    m_cmd = ["cmd", "/k", "start", "py", str(m_path), "--workspace", str(WORKSPACE_PATH)]
                    subprocess.Popen(m_cmd, shell=True)
                else:
                    subprocess.Popen([sys.executable, str(m_path), "--workspace", str(WORKSPACE_PATH)], start_new_session=True)
                spawned.append("MasterBot")
                
                # 2. Spawn Specialists
                bots_dir = WORKSPACE_PATH / "Bots"
                if bots_dir.exists():
                    for d in bots_dir.iterdir():
                        if d.is_dir() and not d.name.startswith('_'):
                            print(f"Spawning worker for {d.name}...")
                            if os.name == 'nt':
                                # V12.1 HARDENING: Use /k for workers too
                                w_cmd = ["cmd", "/k", "start", "py", str(w_path), "--workspace", str(WORKSPACE_PATH), "--bot", d.name]
                                subprocess.Popen(w_cmd, shell=True)
                            else:
                                subprocess.Popen([sys.executable, str(w_path), "--workspace", str(WORKSPACE_PATH), "--bot", d.name], start_new_session=True)
                            spawned.append(d.name)
                            
                return jsonify({"success": True, "message": f"Killed {killed} processes. Spawned fresh console for: {', '.join(spawned)}"})
                
            return jsonify({"success": True, "message": f"Terminated {killed} daemon processes."})
            
        elif action == "restore":
            backup_path = request.json.get("backup_path", "")
            overwrite = request.json.get("overwrite", False)
            if not backup_path: return jsonify({"error": "Backup path required for restore"}), 400
            cmd = [sys.executable, str(Path(__file__).parent / "restore_system.py"), "--backup", backup_path, "--target", str(WORKSPACE_PATH)]
            if overwrite:
                cmd.append("--overwrite")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return jsonify({"success": True, "message": "Restore completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    return jsonify({"error": "Unknown action"}), 400

@app.route("/api/open-item", methods=["POST"])
def open_item():
    if not WORKSPACE_PATH: return jsonify({"error": "Workspace not set"}), 400
    bot_name = request.json.get("bot_name", "MasterBot")
    item = request.json.get("item", "").strip()
    
    # 1. Resolve Path
    base_dir = WORKSPACE_PATH / "MasterBot" / "workspace"
    if bot_name != "MasterBot":
        base_dir = WORKSPACE_PATH / "Bots" / bot_name / "workspace"
    
    target_path = base_dir / item if item else base_dir
    
    if not target_path.exists():
        return jsonify({"error": f"Path not found: {target_path}"}), 404
        
    try:
        # V12.1 FIX 1: Windows-native behavior
        print(f"[UI] Opening: {target_path}")
        os.startfile(target_path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agentic Harness Dashboard Server")
    parser.add_argument("--workspace", type=str, help="Pre-load workspace path")
    args = parser.parse_args()
    
    if args.workspace:
        p = Path(args.workspace).resolve()
        if p.exists() and p.is_dir():
            WORKSPACE_PATH = p
            print(f"Pre-loaded workspace: {WORKSPACE_PATH}")

    app.run(host="0.0.0.0", port=5000, debug=False)
