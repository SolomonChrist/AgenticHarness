import sys
import os
import argparse
from pathlib import Path
from onboarding_manager import OnboardingManager

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Agentic Harness Onboarding")
    parser.add_argument("--workspace", type=str, required=True, help="Path to workspace")
    args = parser.parse_args()
    
    workspace_path = Path(args.workspace).resolve()
    manager = OnboardingManager(workspace_path)
    
    if manager.is_onboarded():
        print(f"Workspace {workspace_path} is already onboarded.")
        return

    state = manager.get_state()
    step = state["step"]
    data = state["data"]

    try:
        if step == 1:
            clear_screen()
            print_header("Welcome to Agentic Harness")
            print("This system will guide you through setting up your MasterBot.")
            print("- Your bot is defined by the files you own.")
            print("- Providers (OpenAI, LM Studio) are replaceable engines.")
            print("- You will define your MasterBot's identity now.")
            input("\nPress Enter to begin...")
            step = manager.process_step(1, data)

        if step == 2:
            clear_screen()
            print_header("Step 2: MasterBot Identity")
            print("Define the core identity of the swarm leader.")
            print(" - NAME: The handle workers use to address the master.")
            print(" - ROLE: The internal function (e.g. Chief of Staff, Architect).")
            print(" - STYLE: The 'tone' of communication (e.g. calm, aggressive, analytical).")
            print(" - PURPOSE: The high-level objective for this specific harness.")
            print("\n" + "-"*30)
            
            data["name"] = input("MasterBot Name [MasterBot]: ") or "MasterBot"
            data["role"] = input("Role Label [Chief of Staff]: ") or "Chief of Staff"
            data["style"] = input("Communication Tone [calm]: ") or "calm"
            print("\nExample: Organize research notes and automate deployment workflows.")
            data["purpose"] = input("MasterBot Purpose: ") or "Coordinate work and protect operator time."
            
            step = manager.process_step(2, data)

        if step == 3:
            clear_screen()
            print_header("Step 3: Intelligence Provider")
            print("Every bot needs a brain. Choose where the 'thinking' happens.")
            print(" - OPENAI: Ready to go (requires API key). Good for stability.")
            print(" - LM STUDIO: Use your own local models (Offline / Private).")
            print("\n" + "-"*30)
            
            print("1. OpenAI (Cloud - Recommended for first run)")
            print("2. LM Studio (Local)")
            print("3. Configure Later (Manual setup required)")
            choice = input("\nChoose a provider [1-3]: ")
            data["provider_choice"] = choice
            if choice == "1":
                print("\nTip: Get your key at platform.openai.com. It is kept in a local JSON only.")
                data["api_key"] = input("OpenAI API Key: ") or ""
            elif choice == "2":
                print("\nTip: Start LM Studio and load a model first.")
                data["api_base"] = input("LM Studio Base URL [http://localhost:1234/v1]: ") or "http://localhost:1234/v1"
            else:
                print("\nNote: You must configure a provider in bot_definition/ProviderProfile.json before running.")
                
            step = manager.process_step(3, data)

        if step == 4:
            clear_screen()
            print_header("Step 4: Primary Project")
            print("What is the MAIN source folder or codebase this harness will manage?")
            print("Defining a project lets bots know where the 'real work' lives.")
            print("\nExample Name: WebApp_V2")
            print("Example Purpose: Refactor the auth layer and add unit tests.")
            print("\n" + "-"*30)

            choice = input("Would you like to create your first project now? (y/n): ").lower()
            if choice == 'y':
                data["create_project"] = True
                data["project_name"] = input("Project Name [Research]: ") or "Research"
                data["project_purpose"] = input("Project Purpose: ") or "Initial research and exploration."
                print("\nTip: Provide an absolute path (e.g. C:\\Code\\MyProject) or leave blank for a sandbox.")
                data["project_path"] = input("Absolute Path to Source Code: ") or ""
            else:
                data["create_project"] = False
                
            step = manager.process_step(4, data)

        if step == 5:
            clear_screen()
            print_header("Final Step: Swarm Activation")
            print(f"Configuration for MasterBot '{data['name']}' is complete.")
            print("A 'Starter Swarm' of 2 specialists will be automatically enabled.")
            
            print("\n" + "="*30)
            print(" NEXT STEPS AFTER EXIT:")
            print("="*30)
            print(" 1.  Open THE DASHBOARD (Already running if you used INSTALL_HARNESS.bat)")
            print(" 2.  Start THE MASTER: py core/master_daemon.py --workspace .")
            print(" 3.  Start THE WORKER: py core/worker_daemon.py --workspace . --bot LocalBot1")
            print("-" * 30)
            
            manager.process_step(5, data)
            print("\nONBOARDING COMPLETE! Your harness is ready for instructions.")

    except KeyboardInterrupt:
        print("\n\nOnboarding paused. Run again to resume.")
        sys.exit(0)

if __name__ == "__main__":
    import json # Ensure json is available
    main()
