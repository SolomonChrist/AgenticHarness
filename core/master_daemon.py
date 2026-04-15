import os
import json
import time
import hashlib
import argparse
import socket
import sys
import psutil
from pathlib import Path
from datetime import datetime, timedelta
import re
import signal
import shutil
from provider_adapter import ProviderAdapter

from onboarding_manager import OnboardingManager

class MasterDaemon:
    def __init__(self, workspace_path):
        self.workspace = Path(workspace_path).resolve()
        
        # FTUE Check
        self.onboarding = OnboardingManager(self.workspace)
        if not self.onboarding.is_onboarded():
            print("\n" + "!"*60)
            print(" ERROR: Workspace is not yet onboarded.")
            print(f" Please run: py core/onboarding_cli.py --workspace {self.workspace}")
            print("!"*60 + "\n")
            sys.exit(1)

        self.master_dir = self.workspace / "MasterBot"
        self.bot_def_dir = self.master_dir / "bot_definition"
        self.workspace_dir = self.master_dir / "workspace"
        self.system_dir = self.workspace / "System"
        self.trigger_path = self.system_dir / ".master_trigger"
        
        self.load_profiles()
        self.adapter = ProviderAdapter(self.bot_def_dir / "ProviderProfile.json")
        
        self.heartbeat_seconds = self.runtime_profile.get("heartbeat_seconds", 60)
        self.lease_seconds = self.runtime_profile.get("lease_seconds", 600)
        self.processed_entries = self.runtime_profile.get("processed_entries", [])
        
        self.load_system_profile()
        
        self.load_identity()
        self.swarm_roster = []
        
        # Priority 3: Meta-Harness Control Plane Manifest
        self.control_plane = self.load_control_plane()

    def load_control_plane(self):
        cp_path = self.system_dir / "ControlPlane.json"
        if cp_path.exists():
            try:
                data = json.loads(cp_path.read_text(encoding="utf-8-sig"))
                print(f"[{self.get_iso_timestamp()}] Control Plane Manifest loaded.")
                return data
            except Exception as e:
                print(f"[{self.get_iso_timestamp()}] ERROR: Cannot load ControlPlane.json: {e}")
        return {}

    def load_profiles(self):
        with open(self.bot_def_dir / "ProviderProfile.json", 'r', encoding='utf-8-sig') as f:
            self.provider_profile = json.load(f)
        with open(self.bot_def_dir / "RuntimeProfile.json", 'r', encoding='utf-8-sig') as f:
            self.runtime_profile = json.load(f)

    def load_system_profile(self):
        sp_path = self.system_dir / "SystemProfile.json"
        defaults = {
            "routing_policy": "OPEN_COST",
            "durable_mode": True,
            "heartbeat_threshold_seconds": 120,
            "operating_mode": "deep"
        }
        if not self.system_dir.exists():
            self.system_dir.mkdir(parents=True, exist_ok=True)
            
        current = defaults.copy()
        if sp_path.exists():
            try:
                data = json.loads(sp_path.read_text(encoding="utf-8-sig"))
                for k in defaults:
                    if k in data:
                        current[k] = data[k]
            except Exception as e:
                print(f"[{self.get_iso_timestamp()}] [WARNING] Malformed SystemProfile.json, using defaults or existing in-memory state: {e}")
                if hasattr(self, 'operating_mode'):
                    current['operating_mode'] = self.operating_mode
        
        # Write back to ensure all fields exist
        try:
            sp_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
        except Exception:
            pass
            
        self.durable_mode = current.get("durable_mode", True)
        self.heartbeat_threshold_seconds = current.get("heartbeat_threshold_seconds", 120)
        self.operating_mode = current.get("operating_mode", "deep")

    def save_runtime_profile(self):
        self.runtime_profile["processed_entries"] = self.processed_entries
        self.runtime_profile["operating_mode"] = self.operating_mode
        with open(self.bot_def_dir / "RuntimeProfile.json", 'w', encoding='utf-8') as f:
            json.dump(self.runtime_profile, f, indent=2)

    def load_identity(self):
        content = self.get_file_content(self.bot_def_dir / "Identity.md")
        name_match = re.search(r"Name:\s*(.*)", content, re.IGNORECASE)
        role_match = re.search(r"Role:\s*(.*)", content, re.IGNORECASE)
        self.name = name_match.group(1).strip() if name_match else "MasterBot"
        self.role = role_match.group(1).strip() if role_match else "Orchestrator"

    def get_file_content(self, path):
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _log(self, text):
        ts = self.get_iso_timestamp()
        msg = f"[{ts}] {text}"
        print(msg)
        try:
            notes_path = self.workspace_dir / "WORKING_NOTES.md"
            current = self.get_file_content(notes_path)
            if current and not current.endswith("\n"):
                current += "\n"
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(current + msg + "\n", encoding="utf-8", newline="\n")
        except Exception as e:
            print(f"[{ts}] [MASTER_LOG_ERROR] {e}")

    def get_swarm_roster(self):
        roster = []
        bots_dir = self.workspace / "Bots"
        if not bots_dir.exists(): return roster
        
        for d in bots_dir.iterdir():
            if d.is_dir() and not d.name.startswith('_'):
                ident_path = d / "bot_definition" / "Identity.md"
                skills_path = d / "bot_definition" / "Skills.md"
                status_path = d / "bot_definition" / "Status.md"
                ident_content = self.get_file_content(ident_path)
                status_content = self.get_file_content(status_path)
                
                name_m = re.search(r"Name:\s*(.*)", ident_content, re.IGNORECASE)
                role_m = re.search(r"Role:\s*(.*)", ident_content, re.IGNORECASE)
                harness_m = re.search(r"Harness:\s*(.*)", ident_content, re.IGNORECASE)
                state_m = re.search(r"Current State:\s*(.*)", status_content, re.IGNORECASE) or \
                          re.search(r"Status:\s*(.*)", status_content, re.IGNORECASE)
                
                # S: Staffing Visibility Extraction
                run_prof = {}
                rp_path = d / "bot_definition" / "RuntimeProfile.json"
                if rp_path.exists():
                    try: run_prof = json.loads(rp_path.read_text(encoding="utf-8-sig"))
                    except: pass
                
                prov_prof = {}
                pp_path = d / "bot_definition" / "ProviderProfile.json"
                if pp_path.exists():
                    try: prov_prof = json.loads(pp_path.read_text(encoding="utf-8-sig"))
                    except: pass

                harness_prof = {}
                hp_path = d / "bot_definition" / "HarnessProfile.json"
                if hp_path.exists():
                    try:
                        harness_prof = json.loads(hp_path.read_text(encoding="utf-8-sig"))
                    except:
                        pass

                skills_content = self.get_file_content(skills_path)
                work_type_lines = []
                if "## Work Types" in skills_content:
                    work_types_section = skills_content.split("## Work Types", 1)[1]
                    work_types_section = work_types_section.split("## Tools", 1)[0]
                    work_type_lines = [ln.strip("- ").strip() for ln in work_types_section.splitlines() if ln.strip().startswith("-")]

                tool_lines = []
                if "## Tools" in skills_content:
                    tools_section = skills_content.split("## Tools", 1)[1]
                    tool_lines = [ln.strip("- ").strip() for ln in tools_section.splitlines() if ln.strip().startswith("-")]
                
                provider = prov_prof.get("provider", "unknown")
                model = prov_prof.get("model", "unknown")
                harness = run_prof.get("harness", "unknown")
                api_base = prov_prof.get("api_base", "")
                is_local = provider.lower() in ("lmstudio", "ollama") or "localhost" in api_base.lower()
                
                is_stale = self.is_bot_heartbeat_stale(d.name, self.heartbeat_threshold_seconds)
                runnable = prov_prof.get("enabled", False) and provider != "PLACEHOLDER"
                
                roster.append({
                    "name": name_m.group(1).strip() if name_m else d.name,
                    "folder": d.name,
                    "role": role_m.group(1).strip() if role_m else "specialist",
                    "harness": harness_m.group(1).strip() if harness_m else "base-python",
                    "provider": provider,
                    "model": model,
                    "cost_tier": prov_prof.get("cost_tier", 1),
                    "api_base": api_base,
                    "capabilities": harness_prof.get("capabilities", []),
                    "tools": " ".join(tool_lines),
                    "work_types": " ".join(work_type_lines),
                    "enabled": runnable,
                    "staff_type": "Starter" if d.name in ("LocalBot1", "ResearchBot", "IngestionBot", "SecondBrainBot") else "Custom",
                    "local_cloud": "Local" if is_local else "Cloud",
                    "is_alive": not is_stale,
                    "is_runnable": runnable,
                    "status": state_m.group(1).strip() if state_m else "unknown"
                })
        return roster

    def check_readiness(self):
        """S: Perform a categorical readiness check including reasoning tests."""
        # 1. Check MasterBot Provider
        mb_pp = self.bot_def_dir / "ProviderProfile.json"
        from provider_adapter import ProviderAdapter
        adapter = ProviderAdapter(mb_pp)
        ok, msg = adapter.test_reasoning()
        
        # 2. Check Specialist Availability
        roster = self.get_swarm_roster()
        runnable_count = sum(1 for b in roster if b["is_runnable"])
        unconfigured = [b["name"] for b in roster if not b["is_runnable"]]
        
        status = "READY"
        explanation = "All systems operational."
        
        if not ok:
            status = "NOT READY"
            explanation = f"MasterBot Reasoning Failure: {msg}"
        elif runnable_count == 0:
            status = "NOT READY"
            explanation = "No runnable specialist bots available."
        elif unconfigured:
            status = "PARTIAL"
            explanation = f"{len(unconfigured)} specialist bots are unconfigured."
            
        return {
            "status": status,
            "explanation": explanation,
            "master_reasoning_ok": ok,
            "master_reasoning_msg": msg,
            "runnable_specialists": runnable_count,
            "unconfigured_count": len(unconfigured)
        }

    def update_file(self, path, content, append=False):
        if not path.parent.exists(): path.parent.mkdir(parents=True, exist_ok=True)
        if append:
            current = self.get_file_content(path)
            # Normalize to LF
            current = current.replace("\r\n", "\n")
            if current and not current.endswith("\n"): current += "\n"
            path.write_text(current + content, encoding="utf-8", newline="\n")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")

    def create_board_snapshot(self):
        """S: Create a timestamped backup of MASTER_TASKS.md before structural changes."""
        path = self.workspace_dir / "MASTER_TASKS.md"
        if not path.exists(): return
        
        snapshot_dir = self.workspace_dir / "System" / "Snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        ts = self.get_iso_timestamp().replace(":", "-")
        snap_path = snapshot_dir / f"MASTER_TASKS_{ts}.md.bak"
        snap_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        
        # Keep only last 10 snapshots
        snaps = sorted(list(snapshot_dir.glob("MASTER_TASKS_*.bak")), key=os.path.getmtime)
        while len(snaps) > 10:
            snaps.pop(0).unlink()

    def normalize_board_structure(self):
        """S: Canonicalize MASTER_TASKS.md by moving task blocks to their correct lanes based on Status."""
        path = self.workspace_dir / "MASTER_TASKS.md"
        if not path.exists(): return
        
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        
        # 1. Identify Cannonical Lanes
        lanes = ["New", "Waiting", "Active", "Claimed", "In Progress", "Blocked", "Done", "Cancelled"]
        lane_map = {l.lower(): l for l in lanes}
        
        # 2. Extract Header (everything before first ##)
        header_match = re.search(r"^(.*?)(?=\n##\s+)", content, re.DOTALL)
        top_header = header_match.group(1).strip() if header_match else content.split("\n## ")[0].strip()
        
        # 3. Extract ALL Task Blocks
        all_blocks = []
        # Support both '### Task' and '### Task:' or similar
        raw_blocks = re.split(r"(?m)^###\s+Task", content)
        for rb in raw_blocks[1:]:
            # Clean rb: remove any lane headers trapped inside
            cleaned_rb = re.sub(r"(?m)^##\s+.*$", "", rb).strip()
            full_block = "### Task\n" + cleaned_rb
            all_blocks.append(full_block)

        # 4. Categorize Blocks by Status
        categorized = {l: [] for l in lanes}
        
        for block in all_blocks:
            stat_m = re.search(r"(?im)^Status:\s*([\w\-_]+)", block)
            status = stat_m.group(1).strip().lower() if stat_m else "new"
            
            # Map status to lane
            target_lane = "New"
            # Normalize status strings (master.py uses lowercase internally)
            if status == "new": target_lane = "New"
            elif status == "waiting": target_lane = "Waiting"
            elif status == "claimed": target_lane = "Claimed"
            elif status in ("active", "in_progress"): target_lane = "Active"
            elif status == "blocked": target_lane = "Blocked"
            elif status == "done": target_lane = "Done"
            elif status == "cancelled": target_lane = "Cancelled"
            
            # Ensure lane exists in map
            if target_lane not in categorized: target_lane = "New"
            
            categorized[target_lane].append(block.strip())

        # 5. Reconstruct Canonical Board
        new_content = top_header + "\n\n"
        for lane in lanes:
            blocks = categorized[lane]
            new_content += f"## {lane}\n"
            if blocks:
                new_content += "\n".join(blocks) + "\n"
            new_content += "\n"
        
        # 6. Final Cleanup
        new_content = re.sub(r"\n{3,}", "\n\n", new_content).strip() + "\n"
        
        if new_content.strip() != content.strip():
            self.create_board_snapshot()
            path.write_text(new_content, encoding="utf-8", newline="\n")
            print(f"[{self.get_iso_timestamp()}] [BOARD_INTEGRITY] Normalized MASTER_TASKS.md structure.")

    def insert_task_in_section(self, path, section_name, task_block):
        """Defensively inserts a task block into the specified section."""
        if not path.exists():
            self.update_file(path, f"# Master Tasks\n\n## {section_name}\n\n" + task_block)
            return
            
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        section_header = f"## {section_name}"
        
        # 1. If section missing, append at end
        if section_header.lower() not in content.lower():
            self.update_file(path, f"\n{section_header}\n\n" + task_block.strip() + "\n", append=True)
            return
            
        # 2. Section exists. Find where it starts and ends
        # Regex to find exactly the section and the next section (or end)
        pattern = rf"(?i)(##\s+{re.escape(section_name)}.*?)(\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            section_content = match.group(1)
            # Insert after the header line (first line of section_content)
            lines = section_content.splitlines()
            if len(lines) > 0:
                lines.insert(1, "") # Blank line
                lines.insert(2, task_block.strip())
                new_section_content = "\n".join(lines)
                new_content = content.replace(section_content, new_section_content)
                path.write_text(new_content, encoding="utf-8")
            else:
                # Fallback
                self.update_file(path, f"\n\n" + task_block.strip() + "\n", append=True)
        else:
            # Fallback
            self.update_file(path, f"\n{section_header}\n\n" + task_block.strip() + "\n", append=True)

    def get_iso_timestamp(self):
        # V12.1 FIX 3: Always include timezone for accurate health comparisons
        return datetime.now().astimezone().isoformat(timespec='seconds')

    def is_process_alive(self, hostname, pid):
        if hostname != socket.gethostname():
            return True
        return psutil.pid_exists(pid)

    def acquire_lease(self):
        lease_path = self.bot_def_dir / "Lease.json"
        now = datetime.now().astimezone()
        
        current_lease = {}
        if lease_path.exists():
            try:
                current_lease = json.loads(lease_path.read_text(encoding="utf-8"))
            except:
                pass

        my_id = f"{socket.gethostname()}:{os.getpid()}"
        owner_id = current_lease.get("lease_owner", "")
        
        is_stale = True
        expires_at_str = current_lease.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at > now:
                    is_stale = False
            except:
                pass

        if not is_stale and owner_id != my_id:
            owner_hostname = owner_id.split(':')[0] if ':' in owner_id else ""
            owner_pid = current_lease.get("pid")
            
            # V12.1 FIX: Be more aggressive about reclaiming leases from dead PIDs
            if owner_pid and not self.is_process_alive(owner_hostname, owner_pid):
                print(f"[{self.get_iso_timestamp()}] [RECOVER] Stale lease detected ({owner_id}). PID is dead. Reclaiming...")
                is_stale = True
            elif not owner_pid:
                # Malformed lease, treat as stale
                is_stale = True

        if not is_stale and owner_id != my_id:
            print(f"[{self.get_iso_timestamp()}] [REJECTED] Active lease held by {owner_id} until {expires_at_str}")
            return False

        new_lease = {
            "bot_id": "masterbot",
            "lease_owner": my_id,
            "pid": os.getpid(),
            "started_at": current_lease.get("started_at", self.get_iso_timestamp()),
            "renewed_at": self.get_iso_timestamp(),
            "expires_at": (now + timedelta(seconds=self.lease_seconds)).isoformat(timespec='seconds'),
            "current_activity": "active"
        }
        self.update_file(lease_path, json.dumps(new_lease, indent=2))
        return True

    def release_lease(self):
        lease_path = self.bot_def_dir / "Lease.json"
        if not lease_path.exists(): return
        
        try:
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            my_id = f"{socket.gethostname()}:{os.getpid()}"
            if lease.get("lease_owner") == my_id:
                print(f"[{self.get_iso_timestamp()}] [CLEANUP] Releasing lease and shuting down.")
                lease_path.unlink()
        except Exception as e:
            print(f"Error releasing lease: {e}")

    def update_lease_status(self, activity, focus="idle", mode="fast"):
        lease_path = self.bot_def_dir / "Lease.json"
        if not lease_path.exists(): return
        try:
            lease = json.loads(lease_path.read_text(encoding="utf-8"))
            lease["current_activity"] = activity
            lease["current_focus"] = focus
            lease["operating_mode"] = mode
            self.update_file(lease_path, json.dumps(lease, indent=2))
        except: pass

    def should_escalate(self, message):
        msg = message.lower()
        # V12.1 Production Hardened Triggers
        triggers = [
            "delegate", "assign", "route", "coordinate",   
            "task", "project", "status", "ongoing", "orchestrate",
            "create", "make", "write", "generate", "research", 
            "analyze", "analyse", "fix", "update", "check", 
            "run", "build", "inspect", "summarize", "notes", "vault",
            "audit", "setup", "config", "install", "verify", "test", 
            "deploy", "backup", "restore", "sync"
        ]
        
        # Pattern: Action + File Extension (e.g., "create script.py")
        file_ext_pattern = r"(?:create|write|make|generate|fix|update|check)\s+.*\.(?:py|txt|md|js|html|css|json|csv|sh|bat)"
        if re.search(file_ext_pattern, msg):
            return True

        if any(t in msg for t in triggers):
            return True
            
        # Check for project names
        projects_dir = self.workspace / "Projects"
        if projects_dir.exists():
            for p in projects_dir.iterdir():
                if p.is_dir() and p.name.lower() in msg:
                    return True
                    
        return False

    def get_routing_instruction(self, message):
        # 0. Load Policy
        policy = "OPEN_COST"
        system_profile_path = self.system_dir / "SystemProfile.json"
        if system_profile_path.exists():
            try:
                system_profile = json.loads(system_profile_path.read_text(encoding="utf-8"))
                policy = system_profile.get("routing_policy", "OPEN_COST")
            except: pass

        roster = self.get_swarm_roster()
        if not roster: return "RECOMMENDED_BOT: none (Reason: Swarm roster is empty.)"
        
        # 1. Prevent duplicate delegation for already active tasks
        tasks_raw = self.get_file_content(self.workspace_dir / "MASTER_TASKS.md")
        if message[:100].strip() in tasks_raw:
            return "RECOMMENDED_BOT: none (Reason: Possible duplicate request detected in active tasks. Skipping redundant delegation.)"

        # 2. Filter by viability (Enabled, Live, Not Blocked)
        viable_bots = [b for b in roster if b["enabled"] and b["is_alive"] and b["status"] != "blocked"]
        
        if not viable_bots:
            return f"RECOMMENDED_BOT: none (Reason: No viable bots are currently online/enabled. Check dashboard.)"

        # 3. Apply Policy Filtering
        if policy == "ZERO_COST":
            viable_bots = [b for b in viable_bots if b["cost_tier"] == 1]
            if not viable_bots:
                return f"RECOMMENDED_BOT: none (Policy: ZERO_COST | Reason: No local/zero-cost bots are currently online.)"
        elif policy == "CHEAPEST":
            viable_bots.sort(key=lambda x: x["cost_tier"])
        elif policy == "HIGHEST_QUALITY":
            viable_bots.sort(key=lambda x: x["cost_tier"], reverse=True)
        # OPEN_COST = use all viable, no special sort

        msg = message.lower()
        msg_keywords = set(re.findall(r'\w+', msg))

        CAPABILITY_INTENT_MAP = {
            "file_creation":       ["create", "make", "write", "generate", "produce", "build", "output"],
            "text_write":          ["write", "compose", "draft", "put", "save", "insert"],
            "text_generation":     ["generate", "summarize", "explain", "describe", "respond"],
            "research":            ["research", "investigate", "report", "study", "review", "findings"],
            "web_search":          ["search", "find", "lookup", "browse", "web"],
            "data_extraction":     ["extract", "parse", "scrape", "pull", "ingest"],
            "code_execution":      ["run", "execute", "python", "script", "code"],
            "analysis":            ["analyze", "analyse", "evaluate", "compare", "assess", "measure"],
            "report_writing":      ["report", "document", "write up", "findings", "summary"],
            # Vault / Second Brain capabilities — PREFER SecondBrainBot
            "vault_analysis":      ["vault", "obsidian", "second brain", "notes", "analyze notes",
                                    "analyse notes", "surface insights", "surface opportunities",
                                    "knowledge base", "note analysis", "vault analysis"],
            "note_analysis":       ["notes", "note", "vault", "obsidian", "markdown notes"],
            "knowledge_synthesis": ["synthesize", "synthesis", "connect ideas", "cross-reference",
                                    "knowledge", "insights", "patterns"],
            "vault":               ["vault", "obsidian", "markdown files", "knowledge base"],
            "ingestion":           ["ingest", "import", "categorize", "classify", "sort",
                                    "organize", "tag", "file", "drop folder"],
        }
        required_caps = set()
        for cap, triggers in CAPABILITY_INTENT_MAP.items():
            if any(t in msg for t in triggers):
                required_caps.add(cap)

        # Score bots: prefer same harness type, then by capability overlap
        best_bot = None
        best_score = -1

        for bot in viable_bots:
            # Load structured capabilities from HarnessProfile
            bot_caps = set(bot.get("capabilities", []))
            # Fallback: derive from text if capabilities[] not yet populated
            if not bot_caps:
                search_pool = (
                    bot.get("tools", "") + " " +
                    bot.get("work_types", "") + " " +
                    bot.get("role", "")
                ).lower()
                bot_caps = set(c for c in CAPABILITY_INTENT_MAP if c in search_pool.replace("_", ""))

            # Capability overlap score
            overlap = len(required_caps & bot_caps) if required_caps else 1
            if overlap == 0:
                continue

            # Bonus: harness keyword match in message
            harness_bonus = 2 if bot["harness"].lower().replace("-", "") in msg.replace("-", "") else 0
            score = overlap + harness_bonus

            if score > best_score:
                best_score = score
                best_bot = bot

        if best_bot:
            matched_caps = required_caps & set(best_bot.get("capabilities", []))
            reason = f"T:capability_match({','.join(matched_caps) if matched_caps else 'general'})"
            return (
                f"RECOMMENDED_BOT: {best_bot['name']}\n"
                f"Routing Policy: {policy}\n"
                f"Cost Tier: {best_bot['cost_tier']}\n"
                f"Reason: {reason}"
            )

        return f"RECOMMENDED_BOT: none (Policy: {policy} | Reason: No bot has the required capabilities for this request. Required: {required_caps})."

    def get_bot_data(self, folder):
        bot_def = folder / "bot_definition"
        data = {
            "Name": folder.name,
            "Role": "unknown",
            "Harness": "unknown",
            "Model": "PLACEHOLDER",
            "Status": "defined",
            "Last Heartbeat": "none",
            "Folder": f"Bots/{folder.name}" if "Bots" in str(folder) else folder.name
        }
        
        if not bot_def.exists(): return data
            
        identity = self.get_file_content(bot_def / "Identity.md")
        if "Role:" in identity: data["Role"] = identity.split("Role:")[1].split("\n")[0].strip()
        if "Name:" in identity: data["Name"] = identity.split("Name:")[1].split("\n")[0].strip()
        if "Harness:" in identity: data["Harness"] = identity.split("Harness:")[1].split("\n")[0].strip()
            
        harness_p = bot_def / "HarnessProfile.json"
        if harness_p.exists():
            try:
                h_data = json.loads(harness_p.read_text(encoding="utf-8"))
                data["Harness"] = h_data.get("harness", data["Harness"])
            except: pass
            
        provider_p = bot_def / "ProviderProfile.json"
        if provider_p.exists():
            try:
                p_data = json.loads(provider_p.read_text(encoding="utf-8"))
                data["Model"] = p_data.get("model", data["Model"])
            except: pass
            
        status_file = bot_def / "Status.md"
        if status_file.exists():
            content = self.get_file_content(status_file)
            if "Current State:" in content: data["Status"] = content.split("Current State:")[1].split("\n")[0].strip()
            elif "Status:" in content: data["Status"] = content.split("Status:")[1].split("\n")[0].strip()

        heartbeat_file = bot_def / "Heartbeat.md"
        if heartbeat_file.exists():
            content = self.get_file_content(heartbeat_file)
            if "Last Updated:" in content: data["Last Heartbeat"] = content.split("Last Updated:")[1].split("\n")[0].strip()

        return data

    def sync_live_bots(self):
        bots = [self.get_bot_data(self.master_dir)]
        bots_dir = self.workspace / "Bots"
        if bots_dir.exists():
            for folder in bots_dir.iterdir():
                if folder.is_dir(): bots.append(self.get_bot_data(folder))

        content = "# Live Bots\n"
        fields = ["Name", "Role", "Harness", "Model", "Status", "Last Heartbeat", "Folder"]
        for bot in bots:
            content += f"\n## Bot\n"
            for field in fields:
                content += f"{field}: {bot.get(field, 'unknown')}\n"
        
        self.update_file(self.system_dir / "LIVE_BOTS.md", content)
        return bots

    def sync_state(self, message, mode="monitoring", current_focus="idle"):
        """
        V2: Sync internal state with SYSTEM_STATUS and Dashboard.
        Uses LLM to summarize logs if message is dense. 
        """
        ts = self.get_iso_timestamp()
        print(f"[{ts}] [SYNC] {message}")
        
        # V12.1 FIX: Avoid LLM calls for simple status updates or short messages
        if mode == "system" or len(message) < 100:
            summary = message
        else:
            summary = self.adapter.get_response(
                "Summarize this system log message concisely.",
                message
            )
            if "[ERROR]" in summary:
                summary = message # Fallback
                
        hb_content = (
            f"# Heartbeat\nLast Updated: {ts}\nMode: active\n"
            f"Current Activity: {summary}\nCurrent Focus: {current_focus}\n"
        )
        self.update_file(self.bot_def_dir / "Heartbeat.md", hb_content)
        
        stat_content = (
            f"# Status\nCurrent State: active\nCurrent Focus: {current_focus}\n"
            f"Last Action: {summary}\nLast Updated: {ts}\n"
        )
        self.update_file(self.bot_def_dir / "Status.md", stat_content)
        
        # System status update
        sys_status = (
            f"# System Status\n\n## Runtime\n- MasterBot: active\n- Mode: {self.operating_mode}\n\n"
            f"## Last Updated\nMaster Pulsed: {ts}\n"
        )
        self.update_file(self.system_dir / "SYSTEM_STATUS.md", sys_status)

    def parse_operator_entries(self, content):
        entries = []
        # Normalize line endings
        content = content.replace("\r\n", "\n")
        raw_blocks = content.split("## Entry")
        for block in raw_blocks[1:]:
            ef = "## Entry" + block
            # V4.8: Only process entries that are explicitly marked as NEW
            if "Status: new" not in ef: continue
            
            eh = hashlib.sha256(ef.strip().encode('utf-8')).hexdigest()
            entries.append((eh, ef))
        return entries

    def repair_planner_syntax(self, resp):
        """V4.8 Syntax Repair: Normalize near-miss model output into canonical blocks."""
        if not resp: return resp
        
        # Mappings: (natural_pattern, canonical_key)
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
            # Log audit trail to WORKING_NOTES
            log_msg = (
                f"\n--- [REPAIR AUDIT] ---\n"
                f"Mappings: {', '.join(applied)}\n"
                f"Original Snippet (first 100 chars): {resp[:100].replace(chr(10), ' ')}...\n"
                f"Repaired Snippet (first 100 chars): {repaired[:100].replace(chr(10), ' ')}...\n"
                f"----------------------\n"
            )
            self._log(log_msg)
            
        return repaired

    def create_fallback_task_from_entry(self, entry_text, routing_instruction, summary_text):
        """Create a simple executable task when the planner intent is clear but formatting drifted."""
        bot_target = "LocalBot1"
        route_match = re.search(r"RECOMMENDED_BOT:\s*([^\n(]+)", routing_instruction or "", re.IGNORECASE)
        if route_match:
            candidate = route_match.group(1).strip()
            if candidate and candidate.lower() != "none":
                bot_target = candidate
        elif "research" in entry_text.lower():
            bot_target = "ResearchBot"

        task_title = (summary_text or "").strip()
        if not task_title:
            cleaned = re.sub(r"\s+", " ", entry_text.strip())
            task_title = cleaned[:80] if cleaned else "Operator task"

        tid = f"task-f-{hashlib.md5((entry_text + bot_target).encode()).hexdigest()[:6]}"
        body_oneline = re.sub(r"\s+", " ", entry_text.strip())
        te = (
            f"\n### Task\nID: {tid}\nStepKey: fallback_{tid[-6:]}\nTitle: {task_title}\n"
            f"Body: {body_oneline}\n"
            f"Project: none\nStatus: new\nPriority: high\n"
            f"DependsOn: none\nInputArtifacts: none\nOutputArtifacts: none\n"
            f"Preferred Bot: {bot_target}\nOwner: none\n"
            f"Routing Policy: fallback\nSelection Reason: Planner formatting drift; task synthesized from operator intent.\nCost Tier: N/A\n"
            f"\nDelegated via fallback synthesis.\n"
        )
        self.insert_task_in_section(self.workspace_dir / "MASTER_TASKS.md", "New", te)
        print(f"[{self.get_iso_timestamp()}] [FALLBACK_TASK] Created {tid} for {bot_target}")
        return 1

    def create_numbered_workflow_from_entry(self, entry_text):
        """Create a deterministic sequential workflow from numbered operator steps."""
        step_matches = re.findall(r"(?ms)^\s*(\d+)\.\s*(.*?)(?=^\s*\d+\.|\Z)", entry_text.strip())
        if len(step_matches) < 2:
            return 0

        created = 0
        prev_step_key = "none"
        prev_artifact = "none"

        for idx, (_, raw_step) in enumerate(step_matches, start=1):
            step_text = raw_step.strip()
            if not step_text:
                continue

            filename_match = re.search(r"([A-Za-z0-9_\-]+\.[A-Za-z0-9]+)", step_text)
            artifact = filename_match.group(1) if filename_match else (prev_artifact if prev_artifact != "none" else "none")

            lowered = step_text.lower()
            if "research" in lowered:
                bot_target = "ResearchBot"
                task_title = "Research Task"
            elif "append" in lowered:
                bot_target = "LocalBot1"
                task_title = "Append to File"
            elif "create" in lowered and "file" in lowered:
                bot_target = "LocalBot1"
                task_title = "Create File"
            else:
                bot_target = "LocalBot1"
                task_title = f"Workflow Step {idx}"

            step_key_match = re.search(r"(create|append|research|analyze|write)[A-Za-z0-9_\- ]*", lowered)
            if step_key_match:
                step_key = re.sub(r"[^a-z0-9]+", "_", step_key_match.group(0)).strip("_")
            else:
                step_key = f"step_{idx}"

            # Keep step bodies single-task focused.
            if idx < len(step_matches):
                step_text = step_text.replace("\r\n", "\n").strip()
            body_compact = step_text.replace("\r\n", "\n").replace("\n", "\\n")

            depends_on = prev_step_key if idx > 1 else "none"
            inputs = prev_artifact if idx > 1 and prev_artifact != "none" else "NONE"
            outputs = artifact if artifact != "none" else "NONE"
            status = "waiting" if depends_on != "none" else "new"
            target_section = "Waiting" if status == "waiting" else "New"
            tid = f"task-s-{hashlib.md5((step_key + step_text).encode()).hexdigest()[:6]}"

            te = (
                f"\n### Task\nID: {tid}\nStepKey: {step_key}\nTitle: {task_title}\n"
                f"Body: {body_compact}\n"
                f"Project: none\nStatus: {status}\nPriority: high\n"
                f"DependsOn: {depends_on}\nInputArtifacts: {inputs}\nOutputArtifacts: {outputs}\n"
                f"Preferred Bot: {bot_target}\nOwner: none\n"
                f"Routing Policy: deterministic\nSelection Reason: Numbered workflow synthesized directly from operator instruction.\nCost Tier: N/A\n"
                f"\nDelegated via deterministic sequential synthesis.\n"
            )
            self.insert_task_in_section(self.workspace_dir / "MASTER_TASKS.md", target_section, te)
            created += 1
            prev_step_key = step_key
            prev_artifact = artifact

        if created:
            print(f"[{self.get_iso_timestamp()}] [SEQUENTIAL_SYNTHESIS] Created {created} workflow steps from numbered instruction.")
        return created

    def handle_admin_commands(self, ec):
        """V4.7 Admin Handler: Intercept reset/clear commands before delegation."""
        cmd = ec.lower().strip()
        if not ("reset" in cmd or "clear tasks" in cmd or "/reset" in cmd):
            return False
            
        print(f"[{self.get_iso_timestamp()}] ADMIN COMMAND DETECTED: {cmd}")
        path = self.workspace_dir / "MASTER_TASKS.md"
        if not path.exists():
            return True
            
        # 1. Backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.workspace_dir / f"MASTER_TASKS_BACKUP_{ts}.md"
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        backup_path.write_text(content, encoding="utf-8")
        
        # 2. Parse and Archive
        # Split by sections
        sections = re.split(r"\n##\s+", "\n" + content)
        new_active = []
        new_history = []
        
        for sec in sections:
            if not sec.strip(): continue
            header = sec.split("\n")[0].strip().lower()
            
            if "active" in header or "waiting" in header or "blocked" in header:
                # These are cleared on reset
                pass
            elif "done" in header or "cancelled" in header or "history" in header:
                # These go to history
                lines = sec.splitlines()[1:] # skip header
                new_history.extend(lines)
            else:
                # Other sections (like top-level header)
                pass

        # 3. Rebuild clean board
        new_content = (
            "# Master Tasks\n\n"
            "## Active\n\n"
            "## Blocked\n\n"
            "## History\n" + "\n".join(new_history) + "\n\n"
        )
        
        path.write_text(new_content, encoding="utf-8")
        
        # Notify in Communication Log
        ts_iso = self.get_iso_timestamp()
        comms_path = self.workspace_dir / "TEAM_COMMUNICATION.md"
        reset_msg = (
            f"\n## Message\nTimestamp: {ts_iso}\nSender: {self.name}\nType: admin_reset\n\n"
            f"🔄 **Board Reset Complete**\n"
            f"- **Action**: {cmd}\n"
            f"- **Backup**: [MASTER_TASKS_BACKUP_{ts}.md](file:///{backup_path})\n"
            f"- **Status**: Active/Waiting/Blocked sections cleared. History preserved.\n"
        )
        self.update_file(comms_path, reset_msg, append=True)
        print(f"[{ts_iso}] Board reset successfully.")
        return True

    def mark_operator_entry_done(self, entry_content):
        """Precise replacement of 'Status: new' with 'Status: done' for a specific entry block."""
        notes_path = self.workspace_dir / "OPERATOR_NOTES.md"
        if not notes_path.exists(): return
        
        full_content = notes_path.read_text(encoding="utf-8")
        # Normalize and find the specific entry content to avoid marking adjacent entries
        marker = "Status: new"
        ec_norm = entry_content.strip()
        
        # We look for a block that contains entry_content AND Status: new
        # Since entries start with ## Entry, we can split and target
        blocks = full_content.split("## Entry")
        new_blocks = []
        replaced = False
        for b in blocks:
            if not b.strip(): 
                new_blocks.append(b)
                continue
            
            orig_b = "## Entry" + b
            if ec_norm in orig_b and marker in orig_b and not replaced:
                new_b = orig_b.replace(marker, "Status: done")
                new_blocks.append(new_b.replace("## Entry", "")) # splitting logic
                replaced = True
            else:
                new_blocks.append(b)
        
        if replaced:
            notes_path.write_text("## Entry".join(new_blocks), encoding="utf-8")

    def process_operator_notes(self):
        notes_path = self.workspace_dir / "OPERATOR_NOTES.md"
        content = self.get_file_content(notes_path)
        if not content.strip(): return

        entries = self.parse_operator_entries(content)
        new_processed = False
        for eh, ec in entries:
            if eh in self.processed_entries: continue
            
            # V4.7 Handle Admin Commands (Reset/Clear)
            if self.handle_admin_commands(ec):
                self.mark_operator_entry_done(ec)
                self.processed_entries.append(eh)
                new_processed = True
                # Break to force re-read of file to avoid in-memory loops on Status: new
                break
            
            # Determine Mode for this entry
            current_run_mode = self.operating_mode
            if current_run_mode == "fast" and self.should_escalate(ec):
                current_run_mode = "deep"
                print(f"[{self.get_iso_timestamp()}] Auto-escalating to DEEP mode for processing.")
            is_exec_intent = self.should_escalate(ec)
            routing = "RECOMMENDED_BOT: none"
            is_numbered_workflow = len(re.findall(r"(?m)^\s*\d+\.\s+", ec)) >= 2

            ui_status = "Delegating" if "delegate" in ec.lower() or "assign" in ec.lower() else ("Processing" if current_run_mode == "deep" else "Responding")
            self.sync_state(f"{ui_status} command {eh[:6]}", current_run_mode)
            self.update_lease_status(ui_status, focus=eh[:6], mode=current_run_mode)
            
            print(f"[{self.get_iso_timestamp()}] PROCESSING STARTED: {eh[:8]} in {current_run_mode.upper()} mode.")
            
            # Context Building
            s = self.get_file_content(self.bot_def_dir / "Soul.md")
            i = self.get_file_content(self.bot_def_dir / "Identity.md")
            rp = self.get_file_content(self.bot_def_dir / "RolePolicies.md")
            gp = self.get_file_content(self.system_dir / "GLOBAL_POLICIES.md")
            
            # Historical tail
            tc = self.get_file_content(self.workspace_dir / "TEAM_COMMUNICATION.md")
            
            if current_run_mode == "fast":
                # FAST: Minimal context, direct reply only
                tc_tail = "\n".join(tc.splitlines()[-6:]) if tc else ""
                sp = (
                    f"You are {self.name}, {self.role}.\n"
                    f"Be direct and concise. No menus. No bullet lists of options. No filler.\n"
                    f"If the operator asks about tasks or status, say you need DEEP mode context "
                    f"and give a one-line summary of your last known state.\n"
                    f"Recent context:\n{tc_tail}\n"
                    f"End your reply with: TASK_SUMMARY: <one-line intent>"
                )
            else:
                # DEEP: Full workspace context — direct operational response style
                mt = self.get_file_content(self.workspace_dir / "MASTER_TASKS.md")
                tc_tail = "\n".join(tc.splitlines()[-30:]) if tc else ""

                roster = self.get_swarm_roster()
                alive_bots = [b for b in roster if b["is_alive"] and b["enabled"]]
                roster_lines = []
                for b in roster:
                    alive_marker = "ONLINE" if b["is_alive"] else "OFFLINE"
                    caps = ", ".join(b.get("capabilities", []))[:60] or b.get("work_types", "")[:60]
                    roster_lines.append(f"  {b['name']} [{alive_marker}] tier={b['cost_tier']} caps={caps}")
                roster_str = "\n".join(roster_lines) if roster_lines else "  (no bots discovered)"

                routing = self.get_routing_instruction(ec)

                # Build a compact live task board summary from MASTER_TASKS.md
                task_summary_lines = []
                for block in re.split(r"### Task", mt)[1:]:
                    tid_m = re.search(r"ID:\s*([^\s\r\n]*)", block)
                    stat_m = re.search(r"Status:\s*(\w+)", block)
                    title_m = re.search(r"Title:\s*(.*)", block)
                    owner_m = re.search(r"Owner:\s*(.*)", block)
                    if tid_m and stat_m:
                        tid = tid_m.group(1).strip()
                        stat = stat_m.group(1).strip().lower()
                        title = title_m.group(1).strip()[:55] if title_m else "?"
                        owner = owner_m.group(1).strip() if owner_m else "none"
                        if stat not in ("done", "cancelled", "archived"):
                            task_summary_lines.append(f"  [{stat.upper():12s}] {tid} | {title} → {owner}")
                task_board_str = (
                    "\n".join(task_summary_lines)
                    if task_summary_lines else "  (no active tasks)"
                )

                sp = (
                    f"{s}\n{i}\n{rp}\n{gp}\n\n"
                    f"=== LIVE TASK BOARD (source of truth) ===\n"
                    f"{task_board_str}\n\n"
                    f"=== BOTS ONLINE ===\n"
                    f"{roster_str}\n\n"
                    f"=== ROUTING DECISION ===\n"
                    f"{routing}\n\n"
                    f"=== RECENT COMMUNICATION (last 30 lines) ===\n"
                    f"{tc_tail}\n\n"
                    f"=== REQUIRED BLOCK TEMPLATE ===\n"
                    f"STRICT: For every task you decompose, you MUST use this exact block format:\n"
                    f"STEP_KEY: <stable_snake_case_name>\n"
                    f"DELEGATE: <BotName> | <Short Title>\n"
                    f"BODY: <Detailed instructions for the bot>\n"
                    f"DEPENDS_ON: <StepKey or NONE>\n"
                    f"INPUTS: <files or NONE>\n"
                    f"ARTIFACTS: <files or NONE>\n\n"
                    f"RESPONSE RULES — follow exactly:\n"
                    f"1. For vault/markdown/knowledge base tasks, PREFER SecondBrainBot as primary owner.\n"
                    f"2. Decompose complex work into a SEQUENTIAL WORKFLOW using StepKeys.\n"
                    f"3. Use the REQUIRED BLOCK TEMPLATE above for every delegation.\n"
                    f"4. If a task depends on a previous step, use the StepKey in DEPENDS_ON.\n"
                    f"5. End with: TASK_SUMMARY: <one-line intent>\n"
                    f"6. Keep all responses under 300 words. Decompose and delegate immediately."
                )

            
            if is_exec_intent and is_numbered_workflow:
                created_task_count = self.create_numbered_workflow_from_entry(ec)
                resp = "I decomposed your numbered workflow into deterministic sequential tasks for the swarm."
                delegated_count = created_task_count
            else:
                p_model = self.provider_profile.get('model', 'unknown')
                p_engine = self.provider_profile.get('provider', 'unknown')
                # Pulse heartbeat before starting long LLM call
                self.sync_state("thinking (LLM call)", current_focus=eh[:6])
                resp = self.adapter.get_response(sp, f"OPERATOR ENTRY:\n{ec}")
                self.sync_state("processing response", current_focus=eh[:6])
            
                # V4.8 Syntax Repair Pass
                resp = self.repair_planner_syntax(resp)
            
                # Handle delegation parse (V2 ORCHESTRATION)
                delegated_count = 0
                created_task_count = 0
            if "DELEGATE:" in resp:
                # Capture blocks of StepKey + Delegate + Metadata
                blocks = re.split(r"(?=STEP_KEY:|###\s*STEP\s*\d+\s*:)", resp, flags=re.IGNORECASE)
                for block in blocks:
                    if "DELEGATE:" not in block: continue
                    delegated_count += 1
                    
                    sk_m = re.search(r"STEP_KEY:\s*([A-Za-z0-9_\-]+)", block)
                    if not sk_m:
                        sk_m = re.search(r"###\s*STEP\s*\d+\s*:\s*([A-Za-z0-9_\-]+)", block, re.IGNORECASE)
                    # V4.4 Flexible Delegate: pipe is now optional
                    del_m = re.search(r"DELEGATE:\s*([^|\n\r]+)(?:\|\s*(.*))?", block)
                    body_m = re.search(r"BODY:\s*(.*?)(?=\s*(?:DEPENDS_ON|INPUTS|ARTIFACTS|STEP_KEY|DELEGATE)|\Z)", block, re.DOTALL)
                    dep_m = re.search(r"DEPENDS_ON:\s*([^\n\r]*)", block)
                    inp_m = re.search(r"INPUTS:\s*([^\n\r]*)", block)
                    art_m = re.search(r"ARTIFACTS:\s*([^\n\r]*)", block)
                    
                    if not del_m:
                        print(f"[{self.get_iso_timestamp()}] [BRIDGE] Rejected block (missing DELEGATE): {block[:80]}...")
                        continue
                    
                    bot_target = del_m.group(1).strip()
                    task_title = del_m.group(2).strip() if del_m.group(2) else ""
                    step_key = sk_m.group(1).strip() if sk_m else "none"
                    step_body = body_m.group(1).strip() if body_m else ""
                    
                    # V4.4 Title Derivation
                    if not task_title:
                        first_line = step_body.split('\n')[0].split('.')[0].strip()
                        task_title = first_line if first_line else (step_key if step_key != "none" else "Untitled Task")
                    
                    # V3: Use explicit step body if provided, fallback to title
                    step_body = body_m.group(1).strip() if body_m else task_title
                    depends_on = dep_m.group(1).strip() if dep_m else "none"
                    inputs = inp_m.group(1).strip() if inp_m else "none"
                    artifacts = art_m.group(1).strip() if art_m else "none"

                    # V4.5 Dependency Normalization & Status Guard
                    def normalize_dep_v45(d):
                        d_clean = d.strip().lower()
                        if d_clean in ("", "none", "null", "none:"): return "none"
                        # Absolute path check (Drive letters, UNC, or /root)
                        if bool(re.match(r"^[A-Za-z]:[\\/]|^\/|^\\\\", d.strip())): return "none"
                        return d.strip()
                    
                    norm_dep = normalize_dep_v45(depends_on)
                    status = "waiting" if norm_dep != "none" else "new"
                    
                    # Create the task
                    tid = f"task-d-{hashlib.md5((task_title + step_key).encode()).hexdigest()[:6]}"
                    
                    # V4.5 Deduplication Check
                    m_tasks_content = self.get_file_content(self.workspace_dir / "MASTER_TASKS.md")
                    if f"StepKey: {step_key}" in m_tasks_content and step_key != "none":
                        print(f"[{self.get_iso_timestamp()}] [BRIDGE] Skipped duplicate StepKey: {step_key}")
                        continue
                    
                    r_policy = "unknown"; r_reason = ""; r_cost = "N/A" # V4.5 Scoping Fix
                    body_compact = step_body.replace("\r\n", "\n").replace("\n", "\\n")
                    target_section = "Waiting" if status == "waiting" else "New"

                    te = (
                        f"\n### Task\nID: {tid}\nStepKey: {step_key}\nTitle: {task_title}\n"
                        f"Body: {body_compact}\n"
                        f"Project: none\nStatus: {status}\nPriority: high\n"
                        f"DependsOn: {norm_dep}\nInputArtifacts: {inputs}\nOutputArtifacts: {artifacts}\n"
                        f"Preferred Bot: {bot_target}\nOwner: none\n"
                        f"Routing Policy: {r_policy}\nSelection Reason: {r_reason}\nCost Tier: {r_cost}\n"
                        f"\nDelegated via V2 Orchestration.\n"
                    )
                    self.insert_task_in_section(self.workspace_dir / "MASTER_TASKS.md", target_section, te)
                    created_task_count += 1
                    print(f"[{self.get_iso_timestamp()}] [BRIDGE] Created {tid} step={step_key} depends_on_raw={depends_on} depends_on_norm={norm_dep} status={status}")

            tsm = "Operator request processed"
            match = re.search(r"TASK_SUMMARY:\s*(.*)", resp)
            if match: tsm = match.group(1).strip()
            clean_resp = re.sub(r"TASK_SUMMARY:.*", "", resp, flags=re.IGNORECASE).strip()
            provider_failed = clean_resp.strip().startswith("[ERROR]")

            if is_exec_intent and created_task_count == 0 and not provider_failed:
                created_task_count += self.create_fallback_task_from_entry(ec, routing, tsm)
                if not clean_resp:
                    clean_resp = "I understood the request and created a fallback executable task for the swarm."
            
            # V4.5 Instant Bridge Cycle
            self.run_orchestration_cycle()
            
            ce = f"\n## Message\nTimestamp: {self.get_iso_timestamp()}\nSender: MasterBot\nType: operator_response\nProject: none\nTask: none\n\n{clean_resp}\n"
            self.update_file(self.workspace_dir / "TEAM_COMMUNICATION.md", ce, append=True)
            print(f"[{self.get_iso_timestamp()}] RESPONSE WRITTEN: {eh[:8]} complete.")
            
            # V12.1: Enforce signoff criteria for done status
            if provider_failed:
                ce = (
                    f"\n## Message\nTimestamp: {self.get_iso_timestamp()}\nSender: MasterBot\nType: error\nProject: none\nTask: none\n\n"
                    f"[WARN] **Execution Blocked**: The configured provider is unavailable. "
                    f"Please verify the model server or provider settings, then retry.\n"
                )
                self.update_file(self.workspace_dir / "TEAM_COMMUNICATION.md", ce, append=True)
                self.mark_operator_entry_done(ec)
                self.processed_entries.append(eh)
                new_processed = True
                print(f"[{self.get_iso_timestamp()}] REQUEST BLOCKED: Provider unavailable.")
            elif created_task_count > 0 or not is_exec_intent:
                # Mark as done in source file for persistence
                self.mark_operator_entry_done(ec)
                
                # Always append a Done task for operator audit
                tid = f"task-m-{eh[:6]}"
                te = f"\n### Task\nID: {tid}\nTitle: {tsm}\nProject: none\nStatus: done\nPriority: low\nPreferred Bot: none\nOwner: MasterBot\n\nCompleted: {tsm}\n"
                self.insert_task_in_section(self.workspace_dir / "MASTER_TASKS.md", "Done", te)
                
                self.processed_entries.append(eh)
                new_processed = True
                print(f"[{self.get_iso_timestamp()}] REQUEST COMPLETED: {eh[:8]}")
            else:
                # Execution intent but no tasks? Block it or mark as failed
                ce = f"\n## Message\nTimestamp: {self.get_iso_timestamp()}\nSender: MasterBot\nType: error\nProject: none\nTask: none\n\n" \
                     f"[WARN] **Execution Blocked**: Request implies action but no delegation blocks were generated. " \
                     f"Please rephrase or check specialist availability.\n"
                self.update_file(self.workspace_dir / "TEAM_COMMUNICATION.md", ce, append=True)
                print(f"[{self.get_iso_timestamp()}] REQUEST REJECTED: No delegation blocks for execution intent.")

            self.save_runtime_profile()
            self.sync_state("monitoring workspace", self.operating_mode)
            self.update_lease_status("active", focus="idle", mode=self.operating_mode)
            
            # Cleanup trigger after processing is complete
            if self.trigger_path.exists():
                try: self.trigger_path.unlink()
                except: pass

    # ─────────────────────────────────────────────────────────────────────
    # L: Recovery Patrol + S: SystemState Management
    # ─────────────────────────────────────────────────────────────────────

    def _load_lifecycle_config(self):
        """Load lifecycle config from SystemProfile.json."""
        config = {}
        sp = self.system_dir / "SystemProfile.json"
        if sp.exists():
            try: config = json.loads(sp.read_text(encoding="utf-8"))
            except: pass
        return config

    def is_bot_heartbeat_stale(self, bot_name, timeout_seconds):
        """Check if a bot's heartbeat is older than timeout_seconds OR if its process is dead."""
        bots_dir = self.workspace / "Bots"
        if not bots_dir.exists(): return True
        for d in bots_dir.iterdir():
            if d.is_dir():
                ident = self.get_file_content(d / "bot_definition" / "Identity.md")
                nm = re.search(r"Name:\s*(.*)", ident)
                if nm and nm.group(1).strip().lower() == bot_name.lower():
                    # 1. Check Lease (process validity)
                    lease = {}
                    lease_path = d / "bot_definition" / "Lease.json"
                    if lease_path.exists():
                        try: lease = json.loads(lease_path.read_text(encoding="utf-8"))
                        except: pass
                    
                    # WorkerDaemon uses 'owner' NOT 'lease_owner'
                    owner_name = lease.get("owner", "")
                    if owner_name:
                        owner_hostname = lease.get("hostname", "")
                        owner_pid = lease.get("pid")
                        if owner_pid and not self.is_process_alive(owner_hostname, owner_pid):
                            return True # Process is dead, therefore stale immediately

                    # 2. Check Heartbeat age
                    hb = self.get_file_content(d / "bot_definition" / "Heartbeat.md")
                    hb_m = re.search(r"Last Updated:\s*(.*)", hb)
                    if hb_m:
                        try:
                            hb_time = datetime.fromisoformat(hb_m.group(1).strip())
                            # Ensure hb_time is timezone aware for comparison
                            if hb_time.tzinfo is None:
                                hb_time = hb_time.astimezone()
                            age = (datetime.now().astimezone() - hb_time).total_seconds()
                            return age > timeout_seconds
                        except: pass
                    return True  # No valid timestamp = stale
        return True  # Not found = stale

    def update_task_fields_inplace(self, task_id, fields, path):
        """Update task block fields in-place without moving sections."""
        if not path.exists(): return
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        task_regex = rf"### Task\nID:\s*{re.escape(task_id)}(.*?)(?=\n### Task|\n## |\Z)"
        match = re.search(task_regex, content, re.DOTALL)
        if not match: return
        block_full = "### Task\nID: " + task_id + match.group(1)
        new_block = block_full
        for k, v in fields.items():
            field_pattern = rf"(?im)^{re.escape(k)}:\s*(.*)$"
            if re.search(field_pattern, new_block):
                new_block = re.sub(field_pattern, f"{k}: {v}", new_block, count=1)
            else:
                new_block = new_block.strip() + f"\n{k}: {v}\n"
        path.write_text(content.replace(block_full, new_block), encoding="utf-8")

    def write_reroute_notice(self, task_id, title, from_bot, to_bot, attempt, reason):
        """Write reroute event to MasterBot TEAM_COMMUNICATION.md."""
        ts = self.get_iso_timestamp()
        msg = (
            f"\n## Message\nTimestamp: {ts}\nSender: MasterBot\nType: task_reroute\n"
            f"Task: {task_id}\n\n"
            f"🔄 **Task Rerouted** (L:Recovery Patrol)\n"
            f"- **Task ID**: {task_id}\n"
            f"- **Title**: {title}\n"
            f"- **Rerouted From**: {from_bot}\n"
            f"- **Rerouted To**: {to_bot}\n"
            f"- **Attempt**: {attempt}\n"
            f"- **Reason**: {reason}\n"
        )
        self.update_file(self.workspace_dir / "TEAM_COMMUNICATION.md", msg, append=True)

    def write_system_state(self, recovery_events=None):
        """S: Write live swarm state snapshot to System/SystemState.json."""
        try:
            state_path = self.system_dir / "SystemState.json"
            existing = {}
            if state_path.exists():
                try: existing = json.loads(state_path.read_text(encoding="utf-8"))
                except: pass

            tasks_content = self.get_file_content(self.workspace_dir / "MASTER_TASKS.md")
            active_count = tasks_content.lower().count("status: new") + tasks_content.lower().count("status: claimed") + tasks_content.lower().count("status: in_progress")
            blocked_count = tasks_content.lower().count("status: blocked")
            done_count = tasks_content.lower().count("status: done")

            roster = self.get_swarm_roster()
            alive_count = sum(1 for b in roster if b.get("is_alive"))

            events = existing.get("lifecycle_events", [])
            if recovery_events:
                ts = self.get_iso_timestamp()
                for ev in recovery_events:
                    events.append({"ts": ts, "event": ev})
                events = events[-50:]  # Keep last 50 events

            readiness = self.check_readiness()

            state = {
                "active_tasks": active_count,
                "blocked_tasks": blocked_count,
                "done_tasks": done_count,
                "workers_alive": alive_count,
                "readiness_category": readiness["status"],
                "readiness_explanation": readiness["explanation"],
                "control_plane": {
                    "control_node": self.control_plane.get("control_node"),
                    "registered_harnesses": self.control_plane.get("execution_harnesses", []),
                    "active_hooks": list(self.control_plane.get("lifecycle_hooks", {}).keys())
                },
                "last_recovery_run": self.get_iso_timestamp(),
                "lifecycle_events": events
            }
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[SystemState] Write error: {e}")

    def run_recovery_patrol(self):
        """
        L: Lifecycle Hook — patrol for stale and blocked tasks.
        - Stale (claimed/in_progress + owner heartbeat expired) -> reset to new, reroute
        - Blocked (retry_count < max_retries) -> reset to new for reattempt
        Preserves full accountability: OriginalBot, ReroutedFrom, RerouteReason, RetryCount.
        """
        config = self._load_lifecycle_config()
        stale_timeout = self.heartbeat_threshold_seconds
        max_retries = config.get("max_retries", 3)
        
        # Priority 3: Hardened harness list from ControlPlane
        registered_harnesses = self.control_plane.get("execution_harnesses", [])

        master_tasks_path = self.workspace_dir / "MASTER_TASKS.md"
        if not master_tasks_path.exists():
            self.write_system_state()
            return

        content = master_tasks_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        recovery_events = []

        # Parse both Active and Blocked sections
        for sec in re.split(r"\n##\s+", "\n" + content):
            sec_lower = sec.strip().lower()
            if not (sec_lower.startswith("active") or sec_lower.startswith("blocked")):
                continue

            for block in re.split(r"### Task", sec, flags=re.IGNORECASE)[1:]:
                tid_m = re.search(r"(?im)^ID:\s*([^\s\r\n]*)", block)
                stat_m = re.search(r"(?im)^Status:\s*(\w+)", block)
                owner_m = re.search(r"(?im)^Owner:\s*(.*)", block)
                retry_m = re.search(r"(?im)^RetryCount:\s*(\d+)", block)
                title_m = re.search(r"(?im)^Title:\s*(.*)", block)
                orig_m = re.search(r"(?im)^OriginalBot:\s*(.*)", block)

                if not (tid_m and stat_m): continue

                tid = tid_m.group(1).strip()
                status = stat_m.group(1).strip().lower()
                owner = owner_m.group(1).strip() if owner_m else "none"
                retry_count = int(retry_m.group(1).strip()) if retry_m else 0
                title = title_m.group(1).strip() if title_m else tid
                original_bot = orig_m.group(1).strip() if orig_m else owner

                # Case 1: Stale task (claimed/in_progress but owner heartbeat expired)
                if status in ("claimed", "in_progress") and owner.lower() != "none":
                    if self.is_bot_heartbeat_stale(owner, stale_timeout):
                        new_retry = retry_count + 1
                        if new_retry > max_retries:
                            # Exhausted — mark permanently blocked
                            self.update_task_fields_inplace(tid, {
                                "Status": "blocked",
                                "RerouteReason": f"Owner {owner} stale, max retries ({max_retries}) exhausted"
                            }, master_tasks_path)
                            event = f"BLOCKED:{tid}|owner={owner}|max_retries_exceeded"
                        else:
                            # Reroute: reset to new, preserve accountability
                            self.update_task_fields_inplace(tid, {
                                "Status": "new",
                                "Owner": "none",
                                "RetryCount": str(new_retry),
                                "OriginalBot": original_bot,
                                "ReroutedFrom": owner,
                                "RerouteReason": f"Heartbeat stale >{stale_timeout}s"
                            }, master_tasks_path)
                            # Find best reroute target (T: Capability Based)
                            roster = self.get_swarm_roster()
                            reroute_to = "any available bot"
                            for b in roster:
                                # Must be registered in Control Plane to be an official reroute target
                                is_registered = not registered_harnesses or b["name"] in registered_harnesses
                                if b["is_alive"] and b["enabled"] and b["name"].lower() != owner.lower() and is_registered:
                                    reroute_to = b["name"]
                                    break
                            self.write_reroute_notice(
                                tid, title, owner, reroute_to, new_retry,
                                f"Bot {owner} heartbeat stale (>{stale_timeout}s)"
                            )
                            event = f"REROUTE:{tid}|from={owner}|to={reroute_to}|attempt={new_retry}"

                        recovery_events.append(event)
                        print(f"[PATROL] {event}")

                # Case 2: Blocked task with retries remaining
                elif status == "blocked" and retry_count < max_retries:
                    new_retry = retry_count + 1
                    self.update_task_fields_inplace(tid, {
                        "Status": "new",
                        "Owner": "none",
                        "RetryCount": str(new_retry),
                        "RerouteReason": f"Blocked task recovery (attempt {new_retry}/{max_retries})"
                    }, master_tasks_path)
                    self.write_reroute_notice(
                        tid, title, owner, "any available bot", new_retry,
                        f"Blocked task recovery attempt {new_retry}/{max_retries}"
                    )
                    event = f"RETRY_BLOCKED:{tid}|attempt={new_retry}"
                    recovery_events.append(event)
                    print(f"[PATROL] {event}")

        # S: Update SystemState.json
        self.write_system_state(recovery_events)
        if recovery_events:
            print(f"[PATROL] Recovery patrol complete. Events: {len(recovery_events)}")

    def run_orchestration_cycle(self):
        """
        V2 Orchestration (Meta-Harness logic):
        1. Resolve StepKey -> TaskID dependencies.
        2. Promote 'waiting' tasks to 'new' if upstream is DONE and INPUTS are verified.
        3. Manage Artifact Handoff (Copy files between workspaces).
        """
        master_tasks_path = self.workspace_dir / "MASTER_TASKS.md"
        if not master_tasks_path.exists(): return
        
        content = master_tasks_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        
        # 1. Build Registry (StepKey -> ID, ID -> Bot)
        registry = {} # step_key -> task_id
        task_info = {} # task_id -> {status, bot_dir, artifacts}
        
        # Scan all tasks (Active and Done)
        blocks = re.split(r"### Task", content, flags=re.IGNORECASE)[1:]
        for block in blocks:
            tid_m = re.search(r"(?im)^ID:\s*([^\s\r\n]*)", block)
            sk_m = re.search(r"(?im)^StepKey:\s*([^\s\r\n]*)", block)
            stat_m = re.search(r"(?im)^Status:\s*(\w+)", block)
            pref_m = re.search(r"(?im)^Preferred Bot:\s*([^\s\r\n]*)", block)
            art_m = re.search(r"(?im)^OutputArtifacts:\s*([^\n]*)", block)
            
            if not tid_m: continue
            tid = tid_m.group(1).strip()
            sk = sk_m.group(1).strip() if sk_m else "none"
            stat = stat_m.group(1).strip().lower() if stat_m else "unknown"
            pref = pref_m.group(1).strip() if pref_m else "none"
            arts = art_m.group(1).strip() if art_m else "none"
            
            if sk != "none": registry[sk] = tid
            
            # Find bot workspace
            bot_dir = None
            if pref != "none":
                potential = self.workspace / "Bots" / pref / "workspace"
                if potential.exists(): bot_dir = potential
            
            task_info[tid] = {
                "status": stat,
                "bot_dir": bot_dir,
                "artifacts": [a.strip() for a in arts.split(",") if a.strip() != "none"]
            }

        # 2. Process Waiting Tasks
        for tid, info in task_info.items():
            if info["status"] != "waiting": continue
            
            # Find the block for this task to read DependsOn/InputArtifacts
            block_match = re.search(rf"### Task\nID:\s*{re.escape(tid)}.*?(?=### Task|## |\Z)", content, re.DOTALL)
            if not block_match: continue
            block = block_match.group(0)
            
            dep_m = re.search(r"(?im)^DependsOn:\s*([^\n]*)", block)
            inp_m = re.search(r"(?im)^InputArtifacts:\s*([^\n]*)", block)
            
            dep = dep_m.group(1).strip() if dep_m else "none"
            inputs = [i.strip() for i in inp_m.group(1).split(",") if i.strip() != "none"] if inp_m else []
            
            # Resolve dependency ID
            dep_id = dep
            if dep in registry: dep_id = registry[dep]
            
            # V4.4 Guardrailed Normalization
            is_path = bool(re.match(r"^[A-Za-z]:[\\/]|^\/|^\\\\", dep_id.strip()))
            is_null = dep_id.lower().strip() in ("", "none", "null", "none:")
            
            if is_null or is_path:
                print(f"[ORCHESTRATOR] Task {tid} (Dependency normalized: {dep_id}) promoted to NEW.")
                self.update_task_fields_inplace(tid, {"Status": "new"}, master_tasks_path)
                continue

            if dep_id not in task_info:
                # Dependency doesn't exist? (Maybe archived or deleted)
                print(f"[BRIDGE] Unresolved dependency token: {dep_id} (Task {tid})")
                continue
                
            dep_info = task_info[dep_id]
            
            # Condition 1: Upstream task must be DONE
            if dep_info["status"] != "done":
                continue
            
            # Condition 2: Input Artifacts must exist in Source Workspace
            all_verified = True
            if inputs and dep_info["bot_dir"]:
                source_dir = dep_info["bot_dir"]
                dest_dir = info["bot_dir"]
                if not dest_dir:
                    print(f"[ORCHESTRATOR] ERROR: Destination bot for {tid} has no workspace.")
                    continue
                
                for art in inputs:
                    source_file = source_dir / art
                    if not source_file.exists():
                        print(f"[ORCHESTRATOR] {tid} waiting: Artifact {art} not found in {source_dir}")
                        all_verified = False
                        break
                    dest_file = dest_dir / art
                    if source_file.resolve() == dest_file.resolve():
                        print(f"[ORCHESTRATOR] Handoff skipped for {art}: source and destination are the same workspace.")
                        continue
                    
                    # 3. Artifact Handoff (Copy)
                    try:
                        shutil.copy2(source_file, dest_file)
                        print(f"[ORCHESTRATOR] Handoff: {art} copied from {source_dir.parent.name} to {dest_dir.parent.name}")
                    except Exception as e:
                        print(f"[ORCHESTRATOR] ERROR: {art} handoff failed: {e}")
                        all_verified = False
                        break
            
            if all_verified:
                # Promote to NEW
                self.update_task_fields_inplace(tid, {"Status": "new"}, master_tasks_path)
                print(f"[ORCHESTRATOR] Promoting {tid} to NEW (Dependency {dep_id} met + Files verified)")

    def auto_archive_tasks(self):
        """Hygiene: Move older 'Done' tasks to MASTER_TASKS_ARCHIVE.md."""
        master_tasks_path = self.workspace_dir / "MASTER_TASKS.md"
        archive_path = self.workspace_dir / "MASTER_TASKS_ARCHIVE.md"
        if not master_tasks_path.exists(): return
        
        archive_text = ""
        content = master_tasks_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        # 1. Archive Done tasks (keep latest 5)
        done_sec_match = re.search(r"(## Done.*?)(\n## |\Z)", content, re.DOTALL)
        if done_sec_match:
            done_sec = done_sec_match.group(1)
            tasks = re.split(r"### Task", done_sec, flags=re.IGNORECASE)
            if len(tasks) > 6:
                keep = tasks[:6]
                to_archive = tasks[6:]
                archive_text += "### Task" + "### Task".join(to_archive)
                content = content.replace(done_sec, "### Task".join(keep))

        # 2. Archive Blocked tasks (older than 30 mins)
        blocked_sec_match = re.search(r"(## Blocked.*?)(\n## |\Z)", content, re.DOTALL)
        if blocked_sec_match:
            blocked_sec = blocked_sec_match.group(1)
            tasks = re.split(r"### Task", blocked_sec, flags=re.IGNORECASE)
            b_keep = [tasks[0]] # Header
            b_archive = []
            for t in tasks[1:]:
                # Check for RetryCount: 3 or clear failure
                if "RetryCount: 3" in t or "BlockedReason:" in t:
                    b_archive.append(t)
                else:
                    b_keep.append(t)
            if b_archive:
                archive_text += "### Task" + "### Task".join(b_archive)
                content = content.replace(blocked_sec, "### Task".join(b_keep))

        if archive_text:
            self.update_file(archive_path, archive_text, append=True)
            master_tasks_path.write_text(content, encoding="utf-8")
            print(f"[HYGIENE] Archiving completed for better board readability.")

    def perform_warm_boot_recovery(self):
        if not self.durable_mode:
            print(f"[{self.get_iso_timestamp()}] [DURABLE_MODE] Durable mode is false, skipping warm-boot recovery.")
            return
            
        master_tasks_path = self.workspace_dir / "MASTER_TASKS.md"
        if not master_tasks_path.exists():
            return
            
        content = master_tasks_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        recovered_count = 0
        
        for sec in re.split(r"\n##\s+", "\n" + content):
            sec_lower = sec.strip().lower()
            if not sec_lower.startswith("active"):
                continue

            for block in re.split(r"### Task", sec, flags=re.IGNORECASE)[1:]:
                tid_m = re.search(r"(?im)^ID:\s*([^\s\r\n]*)", block)
                stat_m = re.search(r"(?im)^Status:\s*(\w+)", block)
                owner_m = re.search(r"(?im)^Owner:\s*(.*)", block)
                dep_m = re.search(r"(?im)^DependsOn:\s*([^\n]*)", block)

                if not (tid_m and stat_m): continue

                tid = tid_m.group(1).strip()
                status = stat_m.group(1).strip().lower()
                owner = owner_m.group(1).strip() if owner_m else "none"
                dep = dep_m.group(1).strip() if dep_m else "none"

                if status in ("claimed", "in_progress"):
                    is_owner_dead = False
                    if owner.lower() == "none" or owner.lower() == "masterbot":
                        is_owner_dead = True
                    else:
                        is_owner_dead = self.is_bot_heartbeat_stale(owner, self.heartbeat_threshold_seconds)

                    if is_owner_dead:
                        # Recover task
                        is_path = bool(re.match(r"^[A-Za-z]:[\\/]|^\/|^\\\\", dep.strip()))
                        is_null = dep.lower().strip() in ("", "none", "null", "none:")
                        new_status = "new" if (is_null or is_path) else "waiting"
                        
                        self.update_task_fields_inplace(tid, {
                            "Status": new_status,
                            "Owner": "none"
                        }, master_tasks_path)
                        
                        ts = self.get_iso_timestamp()
                        msg = (
                            f"\n## Message\nTimestamp: {ts}\nSender: MasterBot\nType: task_recovery\n"
                            f"Task: {tid}\n\n"
                            f"🔄 **Warm Boot Recovery**\n"
                            f"- **Task ID**: {tid}\n"
                            f"- **Previous Owner**: {owner}\n"
                            f"- **Reason**: MasterBot restarted and owner was dead/stale\n"
                            f"- **Resulting State**: {new_status}\n"
                        )
                        self.update_file(self.workspace_dir / "TEAM_COMMUNICATION.md", msg, append=True)
                        print(f"[{ts}] [WARM_BOOT] Recovered task {tid} from {owner} to canonical {new_status}")
                        recovered_count += 1
                        
        if recovered_count > 0:
            print(f"[{self.get_iso_timestamp()}] [WARM_BOOT] Recovery complete. {recovered_count} tasks recovered.")

    def run(self):
        print(f"MasterBot Daemon Active. Workspace: {self.workspace}")
        
        # Registration signal handlers for graceful shutdown
        def handler(signum, frame):
            print(f"\n[{self.get_iso_timestamp()}] Received signal {signum}. Shutting down...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
        
        self.perform_warm_boot_recovery()
        
        last_bg_sync = 0
        try:
            while True:
                try:
                    now = time.time()
                    triggered = self.trigger_path.exists()
                    
                    # 1. Reactive Path (Immediate)
                    if triggered:
                        print(f"[{self.get_iso_timestamp()}] TRIGGER DETECTED: Reactive pulse initiated.")
                        try:
                            self.trigger_path.unlink(missing_ok=True)
                            self.process_operator_notes()
                        except Exception as e:
                            print(f"[{self.get_iso_timestamp()}] [ERROR] Reactive pulse failed: {e}")
                    
                    # 2. Background Path (Periodic)
                    if (now - last_bg_sync) >= self.heartbeat_seconds or last_bg_sync == 0:
                        if not self.acquire_lease(): sys.exit(1)
                        
                        # Background re-scan of operator notes if not triggered (Safety)
                        if not triggered:
                            try: self.process_operator_notes()
                            except: pass
                        
                        # V2 Orchestration & Recovery Cycle
                        # Always run these in background even if notes parsing fails
                        try:
                            self.normalize_board_structure()
                        except: pass

                        try: self.run_recovery_patrol()
                        except Exception as e: print(f"[{self.get_iso_timestamp()}] [RECOVERY ERROR] {e}")
                        
                        try: self.run_orchestration_cycle()
                        except Exception as e: print(f"[{self.get_iso_timestamp()}] [ORCHESTRATION ERROR] {e}")
                        
                        try: self.auto_archive_tasks()
                        except Exception as e: print(f"[{self.get_iso_timestamp()}] [HYGIENE ERROR] {e}")

                        self.sync_state("monitoring workspace", self.operating_mode)
                        last_bg_sync = now
                        
                except Exception as e:
                    print(f"[ERROR] {str(e)}")
                
                # Fast pulse for reactive trigger file detection
                time.sleep(1)
        finally:
            self.release_lease()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", type=str, default="../AgenticHarnessWork")
    a = p.parse_args()
    MasterDaemon(a.workspace).run()
