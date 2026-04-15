import os
import json
import argparse
from pathlib import Path

def create_directory(path):
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def create_file(path, content, overwrite=False):
    p = Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or overwrite:
        p.write_text(content, encoding="utf-8", newline="\n")
        print(f"  Created: {path}")
    else:
        print(f"  Skipped (exists): {path}")

def build_bot_files(name, target_dir, role="specialist", harness="claude-code", model="PLACEHOLDER", style="proactive", provider="PLACEHOLDER", overwrite=False, skills_text=None, tools_text=None, work_types_text=None):
    target_root = Path(target_dir).resolve()
    create_directory(target_root)
    
    # 1. bot_definition
    bot_def_files = {
        "bot_definition/Soul.md": f"# Soul\nCore essence and enduring purpose of this bot.\n\n## Core Drive\n- Serve as a {role} for the organization.\n\n## Commitments\n- Work clearly\n- Preserve continuity\n- Update files faithfully",
        "bot_definition/Identity.md": f"# Identity\nFormal identity, role, and movement style.\n\nName: {name}\nRole: {role}\nMovement Style: {style}\nHarness: {harness}",
        "bot_definition/Memory.md": "# Memory\nLong-term context and operational history.",
        "bot_definition/Learnings.md": "# Learnings\nExtracted insights and continuous improvements.",
        "bot_definition/Skills.md": f"# Skills\nSpecific capabilities and learned strengths.\n\n## Core Skills\n- {role} capabilities\n{skills_text if skills_text else ''}\n\n## Work Types\n{work_types_text if work_types_text else '- ' + role}\n\n## Tools\n- standard {harness} toolset\n{tools_text if tools_text else ''}",
        "bot_definition/RolePolicies.md": "# Role Policies\nRules and constraints specific to this bot's role.",
        "bot_definition/Status.md": "# Status\nCurrent State: idle\nCurrent Focus: none\nBlockers: none\nLast Meaningful Action: initialized\nLast Updated: none",
        "bot_definition/Heartbeat.md": "# Heartbeat\nLast Updated: none\nMode: inactive\nCurrent Activity: idle\nCurrent Focus: none",
        "bot_definition/Lease.json": "{}",
        "bot_definition/HarnessProfile.json": json.dumps({
            "harness": harness,
            "entry_command": "",
            "provider": provider,
            "model": model,
            "cost_tier": 1 if provider == "lmstudio" else 7,
            "enabled": True
        }, indent=2),
        "bot_definition/ProviderProfile.json": json.dumps({
            "provider": provider,
            "model": model,
            "api_base": "http://localhost:1234/v1" if provider == "lmstudio" else "",
            "api_key": "not-needed" if provider == "lmstudio" else "",
            "enabled": True
        }, indent=2),
        "bot_definition/RuntimeProfile.json": json.dumps({
            "heartbeat_seconds": 300,
            "lease_seconds": 600,
            "enabled": True,
            "degraded_mode_allowed": True
        }, indent=2),
    }

    # 2. workspace
    workspace_files = {
        "workspace/WORKING_NOTES.md": "# Working Notes\nInternal working scratchpad for the bot.",
        "workspace/TASKS.md": "# Tasks\nBot-local task view or currently assigned items.",
        "workspace/TEAM_COMMUNICATION.md": "# Team Communication\nBot-local communication context if needed.",
        "workspace/ARTIFACTS.md": "# Artifacts\nBot-local index of outputs created by this bot.",
    }
    
    # Hardened base-python bot_main.py template (HARNESS_TASK env var, proper sandbox, fallback)
    if harness == "base-python":
        bot_main_template = (
            "import os\n"
            "import json\n"
            "import sys\n"
            "import re\n"
            "import io\n"
            "import contextlib\n"
            "from pathlib import Path\n"
            "from openai import OpenAI\n"
            "\n"
            "def main():\n"
            "    # Read task from HARNESS_TASK env var (authoritative); sys.argv as fallback\n"
            "    task_description = os.environ.get('HARNESS_TASK', '').strip()\n"
            "    task_id = os.environ.get('HARNESS_TASK_ID', 'unknown')\n"
            "    bot_name = os.environ.get('HARNESS_BOT_NAME', 'Worker')\n"
            "    output_artifacts = [a.strip() for a in os.environ.get('HARNESS_OUTPUT_ARTIFACTS', '').split(',') if a.strip()]\n"
            "    if not task_description:\n"
            "        if len(sys.argv) >= 2:\n"
            "            task_description = ' '.join(sys.argv[1:]).strip()\n"
            "        else:\n"
            "            print('ERROR: No task via HARNESS_TASK env var or args.')\n"
            "            sys.exit(1)\n"
            "\n"
            "    bot_root = Path(__file__).parent.parent\n"
            "    bot_def = bot_root / 'bot_definition'\n"
            "    bot_workspace = Path(os.environ.get('HARNESS_WORKSPACE', str(bot_root / 'workspace')))\n"
            "\n"
            "    try:\n"
            "        with open(bot_def / 'ProviderProfile.json', 'r') as f:\n"
            "            p_cfg = json.load(f)\n"
            "\n"
            "        api_key = p_cfg.get('api_key') or os.environ.get('OPENAI_API_KEY', 'none')\n"
            "        c_args = {'api_key': api_key}\n"
            "        provider = (p_cfg.get('provider') or '').lower()\n"
            "        api_base = p_cfg.get('api_base') or os.environ.get('OPENAI_BASE_URL', '')\n"
            "        if api_base:\n"
            "            api_base = api_base.rstrip('/')\n"
            "            if provider in ('lmstudio', 'ollama') and not api_base.endswith('/v1'):\n"
            "                api_base += '/v1'\n"
            "            c_args['base_url'] = api_base + '/'\n"
            "\n"
            "        client = OpenAI(**c_args)\n"
            "        model = p_cfg.get('model', 'gpt-4o')\n"
            "        print(f'--- Brain [{bot_name}] Task: {task_description[:120]} ---')\n"
            "\n"
            "        system_prompt = (\n"
            "            f'You are a specialist Agentic Harness worker bot named {bot_name}.\\n'\n"
            "            f'Your workspace directory is: {bot_workspace}\\n'\n"
            "            'Perform the task exactly as described. Respond with a Python code block if creating/writing files.\\n'\n"
            "            'The variable `workspace` is a Path to your workspace. You have full builtins, Path, os, re, json.\\n'\n"
            "            'CRITICAL: Do not truncate or simplify the content to write. Execute the full instruction.'\n"
            "        )\n"
            "\n"
            "        resp = client.chat.completions.create(\n"
            "            model=model,\n"
            "            messages=[\n"
            "                {'role': 'system', 'content': system_prompt},\n"
            "                {'role': 'user', 'content': task_description}\n"
            "            ]\n"
            "        )\n"
            "\n"
            "        msg = resp.choices[0].message\n"
            "        raw_content = getattr(msg, 'content', '')\n"
            "        if isinstance(raw_content, list):\n"
            "            content = ''.join(part.get('text', '') if isinstance(part, dict) else str(part) for part in raw_content)\n"
            "        else:\n"
            "            content = raw_content or ''\n"
            "        print(content)\n"
            "\n"
            "        py_blocks = re.findall(r'```python\\n(.*?)\\n```', content, re.DOTALL)\n"
            "        had_code_blocks = bool(py_blocks)\n"
            "        executed_any = False\n"
            "        exec_errors = []\n"
            "        exec_captured_output = []\n"
            "        for block in py_blocks:\n"
            "            exec_globals = {\n"
            "                '__builtins__': __builtins__,\n"
            "                'workspace': bot_workspace,\n"
            "                'Path': Path,\n"
            "                'os': os,\n"
            "                're': re,\n"
            "                'json': json,\n"
            "            }\n"
            "            try:\n"
            "                block_stdout = io.StringIO()\n"
            "                with contextlib.redirect_stdout(block_stdout):\n"
            "                    exec(block, exec_globals)\n"
            "                captured = block_stdout.getvalue()\n"
            "                if captured:\n"
            "                    exec_captured_output.append(captured)\n"
            "                    print(captured, end='')\n"
            "                executed_any = True\n"
            "            except Exception as exec_err:\n"
            "                exec_errors.append(str(exec_err))\n"
            "                print(f'Exec error: {exec_err}')\n"
            "\n"
            "        existing_outputs = [bot_workspace / name for name in output_artifacts if name]\n"
            "        has_expected_output = any(path.exists() for path in existing_outputs)\n"
            "        if output_artifacts and not has_expected_output and exec_captured_output:\n"
            "            fallback_text = '\\n'.join(part.strip('\\n') for part in exec_captured_output if part.strip())\n"
            "            if fallback_text:\n"
            "                fallback_path = bot_workspace / output_artifacts[0]\n"
            "                fallback_path.write_text(fallback_text.strip() + '\\n', encoding='utf-8')\n"
            "                print(f'Auto-saved captured output to: {fallback_path}')\n"
            "                has_expected_output = True\n"
            "\n"
            "        with open(bot_workspace / 'WORKING_NOTES.md', 'a', encoding='utf-8') as f:\n"
            "            if executed_any and (not output_artifacts or has_expected_output):\n"
            "                status = 'executed'\n"
            "            elif executed_any and output_artifacts and not has_expected_output:\n"
            "                status = 'missing_artifact'\n"
            "            elif had_code_blocks:\n"
            "                status = 'exec_failed'\n"
            "            else:\n"
            "                status = 'no_code_block'\n"
            "            f.write(f'\\n## AI Execution\\nTask: {task_id}\\nStatus: {status}\\n')\n"
            "            if exec_errors:\n"
            "                f.write('Errors:\\n')\n"
            "                for err in exec_errors:\n"
            "                    f.write(f'- {err}\\n')\n"
            "\n"
            "        if output_artifacts and not has_expected_output:\n"
            "            print(f'ERROR: Expected artifact not created: {output_artifacts[0]}')\n"
            "            sys.exit(1)\n"
            "\n"
            "        if had_code_blocks and not executed_any:\n"
            "            print('ERROR: All generated code blocks failed to execute.')\n"
            "            sys.exit(1)\n"
            "\n"
            "    except Exception as e:\n"
            "        print(f'ERROR: {str(e)}')\n"
            "        sys.exit(1)\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        workspace_files["workspace/bot_main.py"] = bot_main_template

    all_files = {**bot_def_files, **workspace_files}

    for rel_path, content in all_files.items():
        create_file(target_root / rel_path, content, overwrite=overwrite)

    print(f"\nBot '{name}' built successfully.")

def main():
    parser = argparse.ArgumentParser(description="Agentic Harness Bot Builder")
    parser.add_argument("--name", type=str, required=True, help="Bot name")
    parser.add_argument("--role", type=str, default="specialist", help="Bot role")
    parser.add_argument("--harness", type=str, default="claude-code", help="Harness type (claude-code, opencode, etc.)")
    parser.add_argument("--model", type=str, default="PLACEHOLDER", help="Model name")
    parser.add_argument("--style", type=str, default="proactive", help="Movement style")
    parser.add_argument("--target", type=str, required=True, help="Target folder for the bot")
    parser.add_argument("--provider", type=str, default="PLACEHOLDER", help="Provider name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing bot files")
    
    args = parser.parse_args()
    build_bot_files(args.name, args.target, args.role, args.harness, args.model, args.style, args.provider, args.overwrite)

if __name__ == "__main__":
    main()
