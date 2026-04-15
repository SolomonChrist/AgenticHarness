import os
import json
import datetime
from pathlib import Path
from build_bot import build_bot_files

class OnboardingManager:
    REQUIRED_FILES = [
        "MasterBot/bot_definition/Identity.md",
        "MasterBot/bot_definition/Soul.md",
        "MasterBot/bot_definition/ProviderProfile.json",
        "MasterBot/bot_definition/RuntimeProfile.json",
        "System/SYSTEM_STATUS.md"
    ]

    def __init__(self, workspace_path):
        self.workspace = Path(workspace_path).resolve()
        self.state_file = self.workspace / "System" / "ONBOARDING_STATE.json"

    def is_onboarded(self):
        # 1. Check required files
        for rel_path in self.REQUIRED_FILES:
            if not (self.workspace / rel_path).exists():
                return False
        
        # 2. Check onboarding marker in OPERATOR_NOTES.md
        notes_path = self.workspace / "MasterBot" / "workspace" / "OPERATOR_NOTES.md"
        if not notes_path.exists():
            return False
        
        content = notes_path.read_text(encoding="utf-8")
        if "FTUE complete" in content:
            return True
            
        provider_path = self.workspace / "MasterBot" / "bot_definition" / "ProviderProfile.json"
        if provider_path.exists():
            try:
                import json
                data = json.loads(provider_path.read_text(encoding="utf-8"))
                if data.get("enabled", False):
                    return True
            except: pass
            
        return False

    def get_state(self):
        if not self.state_file.exists():
            return {"step": 1, "data": {}}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except:
            return {"step": 1, "data": {}}

    def save_state(self, step, data):
        if not self.state_file.parent.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
        state = {"step": step, "data": data}
        self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def write_file(self, rel_path, content):
        path = self.workspace / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n") # Force LF for cross-platform safety where possible, but OS-default is usually better for users. Wait, user said Windows safety.

    def ensure_starter_swarm(self, provider_config):
        starter_specs = [
            {
                "name": "LocalBot1",
                "role": "execution specialist",
                "style": "direct",
                "skills": "- Execute concrete file and workspace tasks\n- Create and modify artifacts exactly as instructed",
                "work_types": "- file creation\n- file editing\n- implementation support",
            },
            {
                "name": "ResearchBot",
                "role": "research specialist",
                "style": "analytical",
                "skills": "- Research topics and synthesize findings\n- Produce concise markdown reports",
                "work_types": "- research\n- summarization\n- synthesis",
            },
        ]

        provider_name = provider_config.get("provider", "PLACEHOLDER")
        model_name = provider_config.get("model", "PLACEHOLDER")
        enabled = provider_config.get("enabled", False)

        for spec in starter_specs:
            bot_root = self.workspace / "Bots" / spec["name"]
            build_bot_files(
                name=spec["name"],
                target_dir=str(bot_root),
                role=spec["role"],
                harness="base-python",
                model=model_name,
                style=spec["style"],
                provider=provider_name,
                overwrite=False,
                skills_text=spec["skills"],
                work_types_text=spec["work_types"],
            )

            harness_profile_path = bot_root / "bot_definition" / "HarnessProfile.json"
            if harness_profile_path.exists():
                try:
                    harness_profile = json.loads(harness_profile_path.read_text(encoding="utf-8-sig"))
                except Exception:
                    harness_profile = {}
                harness_profile["harness"] = "base-python"
                harness_profile["provider"] = provider_name
                harness_profile["model"] = model_name
                harness_profile["enabled"] = enabled
                harness_profile_path.write_text(json.dumps(harness_profile, indent=2), encoding="utf-8")

            provider_path = bot_root / "bot_definition" / "ProviderProfile.json"
            starter_provider = {
                "provider": provider_name,
                "model": model_name,
                "api_base": provider_config.get("api_base", ""),
                "api_key": provider_config.get("api_key", ""),
                "enabled": enabled,
            }
            provider_path.write_text(json.dumps(starter_provider, indent=2), encoding="utf-8")

            runtime_path = bot_root / "bot_definition" / "RuntimeProfile.json"
            runtime_profile = {
                "heartbeat_seconds": 30,
                "lease_seconds": 600,
                "enabled": enabled,
                "degraded_mode_allowed": True,
            }
            runtime_path.write_text(json.dumps(runtime_profile, indent=2), encoding="utf-8")

    def finalize_onboarding(self, operator_name="Operator"):
        ts = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        marker = f"""
## Entry
Timestamp: {ts}
Operator: {operator_name}
Status: done

FTUE complete. MasterBot configured and workspace initialized.
"""
        notes_path = self.workspace / "MasterBot" / "workspace" / "OPERATOR_NOTES.md"
        if notes_path.exists():
            current = notes_path.read_text(encoding="utf-8")
            notes_path.write_text(current + marker, encoding="utf-8")
        else:
            self.write_file("MasterBot/workspace/OPERATOR_NOTES.md", "# Operator Notes\n" + marker)
        
        # Initialize other required files if they don't exist
        default_status = "# System Status\nOverall State: initialized\nLast Event: Onboarding complete\n"
        self.write_file("System/SYSTEM_STATUS.md", default_status)
        
        if self.state_file.exists():
            self.state_file.unlink() # Finish cleanup

    def process_step(self, step, state_data):
        if step == 1:
            self.save_state(2, state_data)
            return 2
            
        elif step == 2:
            name = state_data.get("name", "MasterBot")
            role = state_data.get("role", "Chief of Staff")
            style = state_data.get("style", "calm")
            purpose = state_data.get("purpose", "Coordinate work and protect operator time.")
            self.write_file("MasterBot/bot_definition/Identity.md", f"# Identity\nName: {name}\nRole: {role}\nMovement Style: {style}\n")
            self.write_file("MasterBot/bot_definition/Soul.md", f"# Soul\nCore Purpose: {purpose}\nCharacter: Calm and organized chief of staff.\n")
            self.save_state(3, state_data)
            return 3
            
        elif step == 3:
            choice = state_data.get("provider_choice", "3")
            provider_config = {"api_base": "", "api_key": state_data.get("api_key", ""), "enabled": True}
            if choice == "1":
                provider_config["provider"] = "openai"
                provider_config["model"] = "gpt-4o-mini"
            elif choice == "2":
                provider_config["provider"] = "lmstudio"
                provider_config["model"] = "local-model"
                provider_config["api_base"] = state_data.get("api_base", "http://localhost:1234/v1")
            else:
                provider_config["provider"] = "PLACEHOLDER"
                provider_config["model"] = "PLACEHOLDER"
                provider_config["enabled"] = False
                
            self.write_file("MasterBot/bot_definition/ProviderProfile.json", json.dumps(provider_config, indent=2))

            # Always scaffold starter bots so the swarm is actually runnable after onboarding.
            self.ensure_starter_swarm(provider_config)

            self.write_file("MasterBot/bot_definition/RuntimeProfile.json", json.dumps({
                "heartbeat_seconds": 30,
                "lease_seconds": 600,
                "enabled": True
            }, indent=2))
            self.save_state(4, state_data)
            return 4
            
        elif step == 4:
            if state_data.get("create_project"):
                p_name = state_data.get("project_name", "Research")
                p_purpose = state_data.get("project_purpose", "Initial research and exploration.")
                p_path = state_data.get("project_path", "")
                
                self.write_file(f"Projects/{p_name}/PROJECT_POINTER.json", json.dumps({"absolute_path": p_path}, indent=2))
                self.write_file(f"Projects/{p_name}/CONTEXT.md", f"# Context\n{p_purpose}\n")
                self.write_file(f"Projects/{p_name}/NEXT_ACTION.md", "# Next Actions\n- [ ] Define first goals\n")
                self.write_file(f"Projects/{p_name}/TEAM_COMMUNICATION.md", "# Team Communication\n")
                self.write_file(f"Projects/{p_name}/ARTIFACTS.md", "# Artifacts\n")
                self.write_file(f"Projects/{p_name}/KANBAN.md", "# Kanban\n")
            
            self.save_state(5, state_data)
            return 5
            
        elif step == 5:
            self.finalize_onboarding(state_data.get("operator_name", "Operator"))
            
            # V12.1 FTUE: Record First Contact Greeting
            ts = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
            greeting = f"""
## Message
Timestamp: {ts}
Sender: MasterBot
Type: announcement
Project: none
Task: none

WELCOME, OPERATOR. I am your MasterBot.

Your Agentic Harness is now initialized with a Starter Swarm (LocalBot1, ResearchBot). 
I am standing by to orchestrate your first initiative.

PRO-TIP: To give me a command, you can use the 'Global Composer' at the bottom of the Dashboard, or write directly into my OPERATOR_NOTES.md.
"""
            comms_path = self.workspace / "MasterBot" / "workspace" / "TEAM_COMMUNICATION.md"
            if comms_path.exists():
                current = comms_path.read_text(encoding="utf-8")
                comms_path.write_text(current + greeting, encoding="utf-8")
            
            return 6
            
        return step
