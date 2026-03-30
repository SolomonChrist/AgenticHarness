#!/usr/bin/env python3
"""
🦂 Agentic Harness — Installer
By Solomon Christ | AgenticHarness.io

Run this once. Everything gets set up.
  python install.py

What it does:
  1. Installs Python dependencies
  2. Creates .env template
  3. Creates launcher scripts for all services
  4. Tests the server starts correctly
  5. Prints your LAN IP and next steps
"""

import os
import sys
import subprocess
import socket
import platform
from pathlib import Path

HERE = Path(__file__).parent
IS_WIN = platform.system() == 'Windows'
IS_MAC = platform.system() == 'Darwin'

BANNER = """
╔══════════════════════════════════════════════════════╗
║  🦂  AGENTIC HARNESS — INSTALLER                     ║
║  By Solomon Christ | AgenticHarness.io               ║
╚══════════════════════════════════════════════════════╝
"""

def run(cmd, check=True):
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ⚠️  {result.stderr.strip()}")
    return result

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "unknown"

def step(n, text):
    print(f"\n{'─'*52}")
    print(f"  STEP {n}: {text}")
    print(f"{'─'*52}")

def check(text):
    print(f"  ✅ {text}")

def warn(text):
    print(f"  ⚠️  {text}")

def info(text):
    print(f"  ℹ️  {text}")

# ── MAIN ────────────────────────────────────────────
print(BANNER)

# ── STEP 1: Python version ──
step(1, "Checking Python version")
if sys.version_info < (3, 9):
    warn(f"Python 3.9+ required. You have {sys.version}. Please upgrade.")
    sys.exit(1)
check(f"Python {sys.version.split()[0]}")

# ── STEP 2: Install dependencies ──
step(2, "Installing Python dependencies")
deps = ["flask", "flask-cors", "python-dotenv", "python-telegram-bot"]
for dep in deps:
    r = run(f"{sys.executable} -m pip install {dep} -q")
    if r.returncode == 0:
        check(dep)
    else:
        warn(f"Failed to install {dep} — you may need to run as admin or in a venv")

# ── STEP 3: Create .env template ──
step(3, "Creating .env template")
env_file = HERE / ".env"
if not env_file.exists():
    env_file.write_text("""\
# 🦂 Agentic Harness — Environment Variables
# Fill in your values below, then save.

# ── TELEGRAM (optional but recommended) ──
# 1. Message @BotFather on Telegram → /newbot → copy token
# 2. Send any message to your bot
# 3. Open: https://api.telegram.org/bot<TOKEN>/getUpdates → find chat id
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# ── HARNESS SETTINGS ──
# Path to the folder containing all your Harness projects
# Example: C:/Users/YourName/projects  or  /home/yourname/projects
HARNESS_PROJECTS_PATH=./projects

# World server port (default: 8888)
WORLD_PORT=8888

# Dashboard server port (default: 8765)
DASHBOARD_PORT=8765

# Telegram bot poll interval in seconds
TELEGRAM_POLL_INTERVAL=60
""", encoding='utf-8')
    check(".env template created — edit it with your values")
else:
    check(".env already exists — skipping")

# ── STEP 4: Create projects folder ──
step(4, "Creating default projects folder")
projects_dir = HERE / "projects"
projects_dir.mkdir(exist_ok=True)
check(f"projects/ folder ready at {projects_dir}")

# ── STEP 5: Create launcher scripts ──
step(5, "Creating launcher scripts")

# Start world server
if IS_WIN:
    world_bat = HERE / "start_world.bat"
    world_bat.write_text("""\
@echo off
title 🦂 Agentic Harness — World Server
echo.
echo  🦂 Starting Agentic Harness World Server...
echo  Reading projects path from .env...
echo.
for %%P in (py python python3) do (
    %%P --version >nul 2>&1 && %%P world_server.py && goto done
)
echo  Python not found. Run install.bat first.
pause
:done
""", encoding='utf-8')
    check("start_world.bat created")

    dashboard_bat = HERE / "start_dashboard.bat"
    dashboard_bat.write_text("""\
@echo off
title 🦂 Agentic Harness — Dashboard
echo.
echo  🦂 Starting Agentic Harness Dashboard...
echo  Reading projects path from .env...
echo.
for %%P in (py python python3) do (
    %%P --version >nul 2>&1 && %%P dashboard_server.py && goto done
)
echo  Python not found. Run install.bat first.
pause
:done
""", encoding='utf-8')
    check("start_dashboard.bat created")

    telegram_bat = HERE / "start_telegram.bat"
    telegram_bat.write_text("""\
@echo off
title 🦂 Agentic Harness — Telegram Bot
echo.
echo  🦂 Starting Agentic Harness Telegram Bot...
echo  Reading projects path from .env...
echo.
for %%P in (py python python3) do (
    %%P --version >nul 2>&1 && %%P telegram_bot.py && goto done
)
echo  Python not found. Run install.bat first.
pause
:done
""", encoding='utf-8')
    check("start_telegram.bat created")

    start_all_bat = HERE / "start_all.bat"
    start_all_bat.write_text("""\
@echo off
echo.
echo  🦂 Starting all Agentic Harness services...
echo  Reading projects path from .env...
echo.

REM Find Python
set PY=
for %%P in (py python python3) do (
    if not defined PY (
        %%P --version >nul 2>&1 && set PY=%%P
    )
)

if not defined PY (
    echo  ERROR: Python not found. Run install.bat first.
    pause
    exit /b 1
)

start "World Server"  cmd /k "%PY% world_server.py"
start "Dashboard"     cmd /k "%PY% dashboard_server.py"
start "Telegram Bot"  cmd /k "%PY% telegram_bot.py"

echo.
echo  All services started. Reading paths from .env
echo.
echo  2D World:   http://localhost:8888/
echo  3D World:   http://localhost:8888/world3d.html
echo  VR World:   http://localhost:8888/worldvr.html
echo  Dashboard:  http://localhost:8765/dashboard.html
echo.
timeout /t 5
""", encoding='utf-8')
    check("start_all.bat created — double-click to start everything")

else:
    # Mac/Linux shell scripts
    start_sh = HERE / "start_world.sh"
    start_sh.write_text("""\
#!/bin/bash
echo ""
echo "🦂 Starting Agentic Harness World Server..."
echo ""
source .env 2>/dev/null || true
PROJECTS=${HARNESS_PROJECTS_PATH:-./projects}
PORT=${WORLD_PORT:-8888}
python3 world_server.py --projects "$PROJECTS" --port "$PORT"
""", encoding='utf-8')
    start_sh.chmod(0o755)
    check("start_world.sh created")

    start_all_sh = HERE / "start_all.sh"
    start_all_sh.write_text("""\
#!/bin/bash
source .env 2>/dev/null || true
PROJECTS=${HARNESS_PROJECTS_PATH:-./projects}

echo "🦂 Starting all Agentic Harness services..."
echo ""

python3 world_server.py     --projects "$PROJECTS" --port ${WORLD_PORT:-8888}     &
python3 dashboard_server.py --projects "$PROJECTS" --port ${DASHBOARD_PORT:-8765} &
python3 telegram_bot.py     --projects "$PROJECTS"                                  &

echo ""
echo "✅ All services running in background."
echo "   World:     http://localhost:${WORLD_PORT:-8888}"
echo "   Dashboard: http://localhost:${DASHBOARD_PORT:-8765}"
echo ""
echo "   Stop all:  kill \$(lsof -t -i:${WORLD_PORT:-8888}) \$(lsof -t -i:${DASHBOARD_PORT:-8765})"
""", encoding='utf-8')
    start_all_sh.chmod(0o755)
    check("start_all.sh created")

# ── STEP 6: Creating HARNESS_PROMPT guide ──
step(6, "Creating guide files")
readme = HERE / "HOW_TO_USE.md"
readme.write_text("""\
# 🦂 Agentic Harness — How To Use

## Quick Start (3 steps)

**Step 1 — Edit .env**
Open `.env` and set your paths and Telegram credentials.

**Step 2 — Start services**
- Windows: Double-click `start_all.bat`
- Mac/Linux: Run `./start_all.sh`

**Step 3 — Open a browser**
- 2D World:   http://localhost:8888/
- 3D World:   http://localhost:8888/world3d.html
- VR World:   http://localhost:8888/worldvr.html
- Dashboard:  http://localhost:8765/dashboard.html

---

## Using on a Project

**Copy HARNESS_PROMPT.md to any project folder, then paste into your AI:**

```
# New empty project:
Read HARNESS_PROMPT.md and run it. New empty project — Scenario A.

# Continue existing Harness project:
Read HARNESS_PROMPT.md and run it.
You are [YOUR_AGENT_NAME]. Existing Harness project — Scenario B.

# Convert existing project:
Read HARNESS_PROMPT.md and run it. Non-Harness project — Scenario C.
Backup first, then migrate.

# Upgrade old Harness version:
Read HARNESS_PROMPT.md and run it. Upgrade to v11.0 — Scenario D.
```

---

## LAN Access (phone, tablet, VR headset)

Find your local IP:
- Windows: run `ipconfig` → look for IPv4 Address
- Mac/Linux: run `ifconfig | grep "inet "`

Then open: `http://YOUR_IP:8888` on any device on your network.

For VR: open `http://YOUR_IP:8888/worldvr.html` in your headset browser.

---

## Unity / Unreal / Game Engine

Poll this endpoint every 5 seconds:
`GET http://YOUR_IP:8888/api/world/unity`

Returns JSON with `zones[]` and `agents[]` arrays with position,
color, status, and archetype data ready to use in your scene.

---

By Solomon Christ | AgenticHarness.io | SolomonChrist.com
""", encoding='utf-8')
check("HOW_TO_USE.md created")

# ── PLATFORM BOOT FILES ──────────────────────────────────────────────────────
# Every major agentic platform reads a specific root file on session start.
# We write ALL of them — same single instruction: read HARNESS_PROMPT.md first.
# Strategy: AGENTS.md is the universal standard (Linux Foundation AAIF, 60k+ repos).
# All other files contain identical content or point to AGENTS.md.
# ─────────────────────────────────────────────────────────────────────────────

step(6, "Creating platform boot files")

HARNESS_BOOT = """\
# Agentic Harness v11.0 — AgenticHarness.io | By Solomon Christ
# ──────────────────────────────────────────────────────────────
# This project runs on Agentic Harness.
# Read HARNESS_PROMPT.md and run it before doing anything else.
# Detect scenario (A/B/C/D) and execute immediately. No chat first.
# ──────────────────────────────────────────────────────────────
Read HARNESS_PROMPT.md and run it.
"""

# ── TIER 1: Universal standard (AGENTS.md) ───────────────────────────────────
# Backed by Linux Foundation AAIF. Supported by: OpenCode, Codex CLI,
# Cursor, Gemini CLI (via config), Aider, Zed AI, GitHub Copilot (Aug 2025+)
# 60,000+ open-source repos. This is the primary file.
(HERE / "AGENTS.md").write_text(HARNESS_BOOT, encoding='utf-8')
check("AGENTS.md — Universal standard (OpenCode, Codex, Cursor, Gemini, Aider, Zed, Copilot)")

# ── TIER 2: Platform-specific files ──────────────────────────────────────────

# Claude Code (.claude/CLAUDE.md) — reads on every session start automatically
# Also reads root CLAUDE.md as fallback
claude_dir = HERE / ".claude"
claude_dir.mkdir(exist_ok=True)
(claude_dir / "CLAUDE.md").write_text(HARNESS_BOOT, encoding='utf-8')
(HERE / "CLAUDE.md").write_text(HARNESS_BOOT, encoding='utf-8')
check(".claude/CLAUDE.md + CLAUDE.md — Claude Code auto-boot")

# Gemini CLI (GEMINI.md) — reads project root GEMINI.md, also AGENT.md
# Google's hierarchical discovery: ~/.gemini/GEMINI.md → project root → subdirs
(HERE / "GEMINI.md").write_text(HARNESS_BOOT, encoding='utf-8')
(HERE / "AGENT.md").write_text(HARNESS_BOOT, encoding='utf-8')
check("GEMINI.md + AGENT.md — Gemini CLI + Gemini Code Assist")

# Cursor — .cursor/rules/*.mdc (current) + .cursorrules (legacy, still read)
cursor_dir = HERE / ".cursor" / "rules"
cursor_dir.mkdir(parents=True, exist_ok=True)
(cursor_dir / "harness.mdc").write_text(
    "---\nalwaysApply: true\n---\n" + HARNESS_BOOT, encoding='utf-8')
(HERE / ".cursorrules").write_text(HARNESS_BOOT, encoding='utf-8')
check(".cursor/rules/harness.mdc + .cursorrules — Cursor")

# Windsurf (Cascade) — .windsurf/rules/rules.md (new) + .windsurfrules (legacy)
windsurf_dir = HERE / ".windsurf" / "rules"
windsurf_dir.mkdir(parents=True, exist_ok=True)
(windsurf_dir / "rules.md").write_text(HARNESS_BOOT, encoding='utf-8')
(HERE / ".windsurfrules").write_text(HARNESS_BOOT, encoding='utf-8')
check(".windsurf/rules/rules.md + .windsurfrules — Windsurf Cascade")

# GitHub Copilot — .github/copilot-instructions.md
github_dir = HERE / ".github"
github_dir.mkdir(exist_ok=True)
(github_dir / "copilot-instructions.md").write_text(HARNESS_BOOT, encoding='utf-8')
check(".github/copilot-instructions.md — GitHub Copilot")

# Cline + RooCode (VS Code extensions) — .clinerules/ directory
# Cline reads all .md files inside .clinerules/
clinerules_dir = HERE / ".clinerules"
clinerules_dir.mkdir(exist_ok=True)
(clinerules_dir / "harness.md").write_text(HARNESS_BOOT, encoding='utf-8')
# RooCode uses .roo/ directory
roo_dir = HERE / ".roo"
roo_dir.mkdir(exist_ok=True)
(roo_dir / "rules.md").write_text(HARNESS_BOOT, encoding='utf-8')
check(".clinerules/harness.md + .roo/rules.md — Cline + RooCode")

# Google Antigravity — .agent/rules/rules.md
antigravity_dir = HERE / ".agent" / "rules"
antigravity_dir.mkdir(parents=True, exist_ok=True)
(antigravity_dir / "rules.md").write_text(HARNESS_BOOT, encoding='utf-8')
check(".agent/rules/rules.md — Google Antigravity")

# Google Jules — JULES.md
(HERE / "JULES.md").write_text(HARNESS_BOOT, encoding='utf-8')
check("JULES.md — Google Jules")

# Aider — CONVENTIONS.md (recommended) + .aider (legacy)
(HERE / "CONVENTIONS.md").write_text(HARNESS_BOOT, encoding='utf-8')
check("CONVENTIONS.md — Aider")

# Zed AI — .zed/settings.json includes system_prompt field
zed_dir = HERE / ".zed"
zed_dir.mkdir(exist_ok=True)
(zed_dir / "settings.json").write_text(
    '{\n  "assistant": {\n    "default_model": {"provider":"anthropic","model":"claude-sonnet-4-5-20251022"},\n'
    '    "system_prompt": "Read HARNESS_PROMPT.md and run it before doing anything. This project uses Agentic Harness v11.0 by Solomon Christ — AgenticHarness.io. Detect scenario A/B/C/D and execute immediately."\n  }\n}\n',
    encoding='utf-8')
check(".zed/settings.json — Zed AI")

# OpenCode — reads AGENTS.md natively (already created above)
# Also has opencode.json for advanced config
check("AGENTS.md (already created) — OpenCode primary")

# Codex CLI (OpenAI) — reads AGENTS.md natively + AGENTS.override.md for local
(HERE / "AGENTS.override.md").write_text(HARNESS_BOOT, encoding='utf-8')
check("AGENTS.override.md — Codex CLI local override")

# CLAUDE.md.template — for agents to deploy into new project folders
(HERE / "CLAUDE.md.template").write_text(HARNESS_BOOT, encoding='utf-8')
check("CLAUDE.md.template — reference copy for manual deploys")

info = """
╔══════════════════════════════════════════════════════════════╗
║  Platform boot files created. Copy these into each project:  ║
╠══════════════════════════════════════════════════════════════╣
║  AGENTS.md              Universal (OpenCode, Codex, Cursor)  ║
║  CLAUDE.md              Claude Code fallback                 ║
║  .claude/CLAUDE.md      Claude Code auto-boot               ║
║  GEMINI.md + AGENT.md   Gemini CLI / Code Assist            ║
║  .cursor/rules/         Cursor (current format)             ║
║  .cursorrules           Cursor (legacy)                     ║
║  .windsurf/rules/       Windsurf (current)                  ║
║  .windsurfrules         Windsurf (legacy)                   ║
║  .github/copilot-*.md   GitHub Copilot                      ║
║  .clinerules/           Cline                               ║
║  .roo/rules.md          RooCode                             ║
║  .agent/rules/rules.md  Google Antigravity                  ║
║  JULES.md               Google Jules                        ║
║  CONVENTIONS.md         Aider                               ║
║  .zed/settings.json     Zed AI                              ║
╚══════════════════════════════════════════════════════════════╝
"""
print(info)


# ── STEP 7: Test import ──
step(7, "Testing server imports")
test = run(f"{sys.executable} -c \"import flask, flask_cors; print('OK')\"")
if "OK" in test.stdout:
    check("Flask ready")
else:
    warn("Flask import failed — try: pip install flask flask-cors")

# ── STEP 8: Verify all required files present ──
step(8, "Checking required files")
required = {
    'world_server.py':     'World server (required)',
    'world.html':          '2D canvas world (required)',
    'world3d.html':        '3D Three.js world (required)',
    'worldvr.html':        'VR world (required)',
    'dashboard_server.py': 'Dashboard server',
    'dashboard.html':      'Dashboard UI',
    'telegram_bot.py':     'Telegram bot (optional)',
}
missing = []
for fname, label in required.items():
    f = HERE / fname
    if f.exists():
        check(f"{fname} — {label}")
    else:
        if 'optional' not in label:
            warn(f"MISSING: {fname} — {label}")
            missing.append(fname)
        else:
            info(f"Optional: {fname} not found (Telegram bot)")

if missing:
    print(f"\n  ⚠️  Missing {len(missing)} required file(s):")
    for f in missing:
        print(f"       → {f}")
    print(f"\n  Download all files from:")
    print(f"  https://github.com/SolomonChrist/AgenticHarness")
    print(f"  and place them in: {HERE}")

# ── DONE ──
ip = get_local_ip()
print(f"""
╔══════════════════════════════════════════════════════╗
║  ✅  INSTALLATION COMPLETE                           ║
╚══════════════════════════════════════════════════════╝

  NEXT STEPS:
  ─────────────────────────────────────────────────
  1. Edit .env → set HARNESS_PROJECTS_PATH to your
     folder containing Harness projects

  2. {'Double-click start_all.bat' if IS_WIN else 'Run ./start_all.sh'}

  3. Open in browser:
     2D World:   http://localhost:8888/
     3D World:   http://localhost:8888/world3d.html
     VR World:   http://localhost:8888/worldvr.html
     Dashboard:  http://localhost:8765/dashboard.html

  4. On any device on your network:
     http://{ip}:8888/

  YOUR LOCAL IP: {ip}
  ─────────────────────────────────────────────────

  To start using Harness on a project:
  → Copy HARNESS_PROMPT.md to your project folder
  → Paste into Claude Code / OpenCode / any agent:
    "Read HARNESS_PROMPT.md and run it."

  See HOW_TO_USE.md for full instructions.

  🦂 AgenticHarness.io | By Solomon Christ
""")
