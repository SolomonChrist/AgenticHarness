# 🦂 Agentic Harness v11.0 — Complete Setup Guide

> *The Universal Standard for Autonomous AI Agent Swarms*
> By Solomon Christ | [AgenticHarness.io](https://AgenticHarness.io) | [SolomonChrist.com](https://SolomonChrist.com)

---

## WHAT YOU'RE GETTING

One system. Three services. Unlimited agents.

```
┌─────────────────────────────────────────────────────────────┐
│  HARNESS_PROMPT.md   → paste into ANY AI agent to boot      │
│  VirtualWorlds/      → watch your agents in 2D / 3D / VR    │
│  TelegramBot/        → control everything from your phone    │
└─────────────────────────────────────────────────────────────┘
```

Time to first working agent: **5 minutes**
Time to full setup (world + Telegram): **20 minutes**

---

## PREREQUISITES

| Tool | Where | Required? |
|------|-------|-----------|
| Claude Code | [claude.ai/code](https://claude.ai/code) | ✅ Yes (primary agent runtime) |
| Python 3.8+ | [python.org/downloads](https://python.org/downloads) | ✅ Yes (world server + bots) |
| Git | [git-scm.com](https://git-scm.com) | ✅ Yes (agent commits) |
| Telegram app | Any device | Optional (EA bot) |

**Windows users:** When installing Python, check ✅ **"Add Python to PATH"**

---

## PHASE 1 — FIRST AGENT (5 minutes)

### 1. Create your projects folder

```bash
# Windows
mkdir C:\Users\YourName\MyAIProjects
mkdir C:\Users\YourName\MyAIProjects\my-first-project

# Mac/Linux
mkdir -p ~/MyAIProjects/my-first-project
```

### 2. Copy the core files into your project

From this repo, copy these 4 files into `my-first-project/`:
```
HARNESS_PROMPT.md        ← THE main file
AGENTS.md                ← universal platform boot
GEMINI.md                ← Gemini CLI boot
CLAUDE.md                ← Claude Code root fallback
```

Also copy the `project-template/.claude/` folder into your project:
```
my-first-project/
└── .claude/
    ├── CLAUDE.md        ← auto-boot (Claude reads every session)
    └── settings.json    ← pre-approves agent file writes
```

### 3. Open Claude Code and boot your agent

```bash
cd my-first-project
claude
```

**Paste this once** (you'll never need to paste again after this):
```
Read HARNESS_PROMPT.md and run it.
This is a new project — Scenario A.
```

The agent will:
1. Ask you 9 setup questions (project name, goals, security level...)
2. Create all 10 LAYER files
3. Write `.claude/CLAUDE.md` — auto-boots every future session
4. Print its WHO_AM_I card
5. Start working on your first task

### 4. Every session after this — zero setup

```bash
cd my-first-project
claude
# Agent reads .claude/CLAUDE.md automatically → boots → WHO_AM_I card → works
```

---

## PHASE 2 — WORLD SERVER (10 minutes)

Watch your agents in a live visual world.

### 1. Set up VirtualWorlds folder

```bash
# Windows
mkdir C:\Users\YourName\MyAIProjects\VirtualWorlds

# Mac/Linux  
mkdir ~/MyAIProjects/VirtualWorlds
```

Copy ALL files from this repo's `VirtualWorlds/` folder into it:
```
VirtualWorlds/
├── world_server.py
├── world.html          ← 2D RPG office world
├── world3d.html        ← 3D night city
├── worldvr.html        ← VR headset (Quest/Pico/Vision Pro)
├── dashboard_server.py
├── dashboard.html      ← web dashboard
├── install.py
├── install.bat         ← Windows installer
├── start_world.bat     ← Windows launcher
└── start_world.sh      ← Mac/Linux launcher
```

### 2. Run the installer

```bash
# Windows — navigate to VirtualWorlds and double-click install.bat
# OR in PowerShell/CMD:
cd C:\Users\YourName\MyAIProjects\VirtualWorlds
install.bat

# Mac/Linux
cd ~/MyAIProjects/VirtualWorlds
python3 install.py
```

The installer:
- Installs Python dependencies (flask, flask-cors, python-dotenv)
- Creates `.env` with default settings
- Creates helper launcher scripts

### 3. Edit .env — set your projects path

Open `VirtualWorlds/.env` in any text editor. Change ONE line:

```bash
# Windows example:
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects

# Mac/Linux example:
HARNESS_PROJECTS_PATH=/Users/yourname/MyAIProjects
```

### 4. Start the world server

```bash
# Windows — double-click start_world.bat
# Mac/Linux
./start_world.sh
```

### 5. Open your worlds

| World | URL | Best for |
|-------|-----|---------|
| 2D Office Map | http://localhost:8888/ | Overview, adding tasks |
| 3D Night City | http://localhost:8888/world3d.html | Immersive monitoring |
| VR Headset | http://localhost:8888/worldvr.html | Quest/Pico/Vision Pro |
| Dashboard | http://localhost:8765/dashboard.html | Stats, notifications |
| Unity/Unreal | http://localhost:8888/api/world/unity | Game engine data feed |

**LAN access** (phone, tablet, VR headset on same WiFi):
```
# Find your local IP:
Windows: ipconfig      → look for IPv4 Address
Mac:     ifconfig      → look for inet
Linux:   hostname -I

# Then use: http://192.168.x.x:8888/
```

---

## PHASE 3 — TELEGRAM EA BOT (5 minutes)

Your 24/7 Executive Assistant. Control everything from your phone.

### 1. Create your Telegram bot

1. Open Telegram → search **@BotFather** → send `/newbot`
2. Follow prompts → **copy the TOKEN** it gives you
3. Open Telegram → search **@userinfobot** → send `/start` → **copy your ID number**

### 2. Set up TelegramBot folder

```bash
# Windows
mkdir C:\Users\YourName\MyAIProjects\TelegramBot

# Mac/Linux
mkdir ~/MyAIProjects/TelegramBot
```

Copy ALL files from this repo's `TelegramBot/` folder:
```
TelegramBot/
├── telegram_bot.py
├── .env.telegram.template
├── start_telegram.bat    ← Windows
└── start_telegram.sh     ← Mac/Linux
```

### 3. Configure credentials

```bash
# Windows
copy .env.telegram.template .env.telegram

# Mac/Linux
cp .env.telegram.template .env.telegram
```

Edit `.env.telegram`:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_ALLOWED_USER_IDS=123456789
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects
BOT_NAME=My AI Assistant
OWNER_NAME=YourFirstName
```

### 4. Install and start

```bash
pip install requests python-dotenv

# Windows — double-click start_telegram.bat
# Mac/Linux
./start_telegram.sh
```

### 5. Test from your phone

Open Telegram → find your bot → send `/start`

**Commands:**
```
/projects          → all project status
/agents            → agent roster + summon commands
/tasks             → all task queues
/add proj | task | HIGH   → queue a task
/wake project-name → get summon command for offline agent
/status            → full system overview
```

**Natural language:**
```
"Add a HIGH task to SecondBrain to fix the login bug"
"What's the status on the CPA project?"
"Wake my finance agent"
```

---

## START EVERYTHING AT ONCE (Windows)

Copy `start_all.bat` from this repo's root into your `MyAIProjects/` folder.
Double-click it — starts world server + Telegram bot in separate windows.

---

## MIGRATION — Already Have an Older Harness Version?

```bash
# Copy harness_migrate.py from tools/ into your MyAIProjects folder
# Run it:
python harness_migrate.py --projects "C:\Users\YourName\MyAIProjects" --dry-run
python harness_migrate.py --projects "C:\Users\YourName\MyAIProjects"
```

What it does across ALL projects at once:
- Moves soul files to `~/.harness/souls/` (global)
- Creates `.claude/CLAUDE.md` in every project (auto-boot)
- Creates all 16 platform boot files
- Removes legacy v9/v10 files
- Builds global agent roster

---

## COMPLETE FOLDER STRUCTURE

```
MyAIProjects/                          ← your root folder
│
├── start_all.bat                      ← start everything (Windows)
├── harness_migrate.py                 ← migration tool
│
├── VirtualWorlds/
│   ├── world_server.py
│   ├── world.html
│   ├── world3d.html
│   ├── worldvr.html
│   ├── dashboard_server.py
│   ├── dashboard.html
│   ├── install.bat / install.py
│   ├── start_world.bat / start_world.sh
│   └── .env                           ← HARNESS_PROJECTS_PATH=...
│
├── TelegramBot/
│   ├── telegram_bot.py
│   ├── .env.telegram                  ← your credentials (gitignored)
│   ├── start_telegram.bat / .sh
│   └── data/                          ← auto-created
│
├── my-first-project/
│   ├── HARNESS_PROMPT.md             ← copy from this repo
│   ├── AGENTS.md
│   ├── GEMINI.md
│   ├── CLAUDE.md
│   ├── .claude/
│   │   ├── CLAUDE.md                  ← auto-boot every session ⭐
│   │   └── settings.json
│   ├── AGENT_CARD.md                  ← created by agent
│   ├── PROJECT.md                     ← created by agent
│   ├── LAYER_*.MD (×6)               ← created by agent
│   └── SKILLS/                        ← created by agent
│
└── another-project/                   ← same structure

~/.harness/                            ← global (auto-created)
├── souls/SOUL_*.md                    ← agent identities
├── agents/AGENTS.md                   ← global team roster
└── skills/                            ← shared skills
```

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| Agent doesn't auto-boot | Check `.claude/CLAUDE.md` exists in project folder |
| World shows 0 projects | Check `HARNESS_PROJECTS_PATH` in `.env` |
| Telegram bot not responding | Check token + your user ID in `.env.telegram` |
| Python not found (Windows) | Reinstall Python, check "Add to PATH" |
| Agent named "Transitionary" | Say: "Suggest a domain-appropriate name for this project" |
| `pip install` fails | Try: `pip install --break-system-packages flask flask-cors python-dotenv` |
| Can't reach world on phone | Use your LAN IP (from ipconfig/ifconfig), same WiFi |

---

## WHAT AGENTS DO WITHOUT YOU

Once running, agents:
- Work through your task list autonomously
- Pulse their heartbeat every 5 minutes
- Commit to git every 15 minutes
- Send 📨 notifications to Telegram when they need you
- Save reusable discoveries to `SKILLS/`
- Write nightly retrospectives to their SOUL file
- Pick up `.harness_wake` tasks you added from your phone

You check in when the 📨 comes. Otherwise they just work.

---

## LINKS

- 🌐 Website: [AgenticHarness.io](https://AgenticHarness.io)
- 💻 GitHub: [github.com/SolomonChrist/AgenticHarness](https://github.com/SolomonChrist/AgenticHarness)
- 👤 Author: [SolomonChrist.com](https://SolomonChrist.com)
- 📄 License: MIT — free to use, modify, distribute

*© Solomon Christ Holdings Inc. — The OPC Stack. One person. Virtual team. Real results.*
