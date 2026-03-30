# 🦂 Agentic Harness v11.0 — Folder Structure & Setup Map
# By Solomon Christ | AgenticHarness.io

This file maps exactly where every file from this repository goes on your machine,
and how your overall MyAIProjects folder should look after setup.

---

## WHAT YOU'RE SETTING UP

```
MyAIProjects/                        ← CREATE THIS FOLDER anywhere on your machine
│
├── TelegramBot/                     ← your 24/7 Executive Assistant bot
├── VirtualWorlds/                   ← 2D/3D/VR world server + dashboard
│
├── ai-SecondBrain/                  ← your first Harness project (example)
├── AI-CPA-Financials/               ← another project (example)
└── (more projects as you grow)
```

---

## STEP 1 — CREATE YOUR FOLDER STRUCTURE

```bash
# Windows (PowerShell or Command Prompt)
mkdir "C:\Users\YourName\MyAIProjects"
mkdir "C:\Users\YourName\MyAIProjects\TelegramBot"
mkdir "C:\Users\YourName\MyAIProjects\VirtualWorlds"

# Mac/Linux
mkdir -p ~/MyAIProjects/TelegramBot
mkdir -p ~/MyAIProjects/VirtualWorlds
```

---

## STEP 2 — WHAT GOES WHERE

### VirtualWorlds/ folder
Copy these files from this repo's `VirtualWorlds/` folder:

```
MyAIProjects/VirtualWorlds/
├── world_server.py          ← main server (serves all 4 worlds)
├── world.html               ← 2D RPG office world
├── world3d.html             ← 3D night city world
├── worldvr.html             ← WebXR VR world
├── dashboard_server.py      ← dashboard API server
├── dashboard.html           ← web dashboard UI
├── install.py               ← one-command installer (run this first)
├── install.bat              ← Windows: double-click to install
├── start_world.bat          ← Windows: start world server
├── start_world.sh           ← Mac/Linux: start world server
├── start_all.bat            ← Windows: start everything at once
└── .env                     ← CREATED BY INSTALLER (edit HARNESS_PROJECTS_PATH)
```

**After copying, run the installer:**
```bash
# Windows — double-click install.bat, OR:
cd "C:\Users\YourName\MyAIProjects\VirtualWorlds"
install.bat

# Mac/Linux
cd ~/MyAIProjects/VirtualWorlds
python3 install.py
```

**Then edit `.env`** — change ONE line:
```
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects
```

---

### TelegramBot/ folder
Copy these files from this repo's `TelegramBot/` folder:

```
MyAIProjects/TelegramBot/
├── telegram_bot.py          ← EA bot (just requests + python-dotenv)
├── .env.telegram.template   ← copy to .env.telegram and fill in
├── start_telegram.bat       ← Windows: double-click to start
└── start_telegram.sh        ← Mac/Linux: start bot
```

**Setup:**
```bash
# 1. Copy template
copy .env.telegram.template .env.telegram    # Windows
cp .env.telegram.template .env.telegram      # Mac/Linux

# 2. Edit .env.telegram — fill in:
#    TELEGRAM_BOT_TOKEN     (from @BotFather in Telegram)
#    TELEGRAM_ALLOWED_USER_IDS  (from @userinfobot in Telegram)
#    HARNESS_PROJECTS_PATH  (same as VirtualWorlds .env)
#    BOT_NAME               (whatever you want to call your EA)

# 3. Install dependencies
pip install requests python-dotenv

# 4. Start
python telegram_bot.py         # Mac/Linux
start_telegram.bat             # Windows (double-click)
```

---

### Each Harness project folder
When setting up a new project, copy these from this repo's `project-template/` folder:

```
MyAIProjects/my-project/
├── HARNESS_PROMPT.md        ← THE MAIN FILE — paste into any AI agent
├── AGENTS.md                ← universal platform boot (OpenCode, Codex, Cursor...)
├── GEMINI.md                ← Gemini CLI boot
├── CLAUDE.md                ← Claude Code root fallback
└── .claude/
    ├── CLAUDE.md            ← Claude Code AUTO-BOOT (reads every session)
    └── settings.json        ← pre-approves LAYER file writes
```

**On first use:**
```
cd MyAIProjects/my-project
claude                        # open Claude Code

# Paste this (one time only):
Read HARNESS_PROMPT.md and run it.
I want you to be my [role] agent called [NAME].
```

After that, `.claude/CLAUDE.md` makes the agent **auto-boot every future session** — no paste needed.

---

### Root / global files (go in MyAIProjects/ root or anywhere accessible)
```
MyAIProjects/
├── start_all.bat            ← Windows: starts world + telegram together
├── harness_migrate.py       ← run once to migrate/cleanup all projects
└── CLAUDE.md.template       ← reference copy for manual .claude/CLAUDE.md setup
```

---

## STEP 3 — GLOBAL ~/.harness/ DIRECTORY

The installer auto-creates this. If not, create manually:

```bash
# Windows
mkdir "%USERPROFILE%\.harness\souls"
mkdir "%USERPROFILE%\.harness\agents"
mkdir "%USERPROFILE%\.harness\skills"

# Mac/Linux
mkdir -p ~/.harness/souls
mkdir -p ~/.harness/agents
mkdir -p ~/.harness/skills
```

**What goes here:**
```
~/.harness/
├── souls/
│   ├── SOUL_MaxMoney-Guardian-01.md    ← auto-created by agents
│   ├── SOUL_SecondBrain-Sage-01.md     ← auto-created by agents
│   └── ...                            ← all agent identities live here
├── agents/
│   └── AGENTS.md                       ← global roster (updated by agents)
└── skills/
    └── ...                             ← reusable skills across all projects
```

---

## COMPLETE PICTURE — After Full Setup

```
C:\Users\YourName\MyAIProjects\          (or ~/MyAIProjects/ on Mac/Linux)
│
├── start_all.bat                        ← double-click: start everything
├── harness_migrate.py                   ← run once to migrate existing projects
├── CLAUDE.md.template                   ← reference file
│
├── VirtualWorlds/
│   ├── world_server.py
│   ├── world.html · world3d.html · worldvr.html
│   ├── dashboard_server.py · dashboard.html
│   ├── install.bat · install.py
│   ├── start_world.bat · start_world.sh
│   ├── start_all.bat
│   └── .env                            ← HARNESS_PROJECTS_PATH=...
│
├── TelegramBot/
│   ├── telegram_bot.py
│   ├── .env.telegram                   ← your credentials (gitignored)
│   ├── .env.telegram.template
│   ├── start_telegram.bat · start_telegram.sh
│   └── data/                           ← session data (auto-created)
│
├── ai-SecondBrain/                      ← Harness project
│   ├── HARNESS_PROMPT.md
│   ├── AGENTS.md · GEMINI.md · CLAUDE.md
│   ├── .claude/
│   │   ├── CLAUDE.md                   ← auto-boot every session ⭐
│   │   └── settings.json
│   ├── AGENT_CARD.md
│   ├── PROJECT.md
│   ├── LAYER_ACCESS.MD
│   ├── LAYER_CONFIG.MD
│   ├── LAYER_HEARTBEAT.MD
│   ├── LAYER_LAST_ITEMS_DONE.MD
│   ├── LAYER_MEMORY.MD
│   ├── LAYER_SHARED_TEAM_CONTEXT.MD
│   ├── LAYER_TASK_LIST.MD
│   ├── SKILLS/
│   └── [your actual project files]
│
└── another-project/                     ← same structure
    └── ...

~/.harness/                              ← global (auto-created)
├── souls/SOUL_*.md                      ← agent identities, travel everywhere
├── agents/AGENTS.md                     ← global team roster
└── skills/                              ← shared skills across all projects
```

---

## DAILY WORKFLOW

1. **Start everything** → double-click `start_all.bat`
2. **Open a project** → open Claude Code in a project folder
3. **Agent auto-boots** → reads `.claude/CLAUDE.md` → prints WHO_AM_I card
4. **Add tasks from phone** → Telegram bot → `/add project | task | PRIORITY`
5. **Watch agents work** → http://localhost:8888/ (2D) or /world3d.html (3D)
6. **Get notifications** → Telegram bot forwards all 📨 entries in real-time

---

## SUMMON COMMANDS (manual boot if .claude/CLAUDE.md not set up)

```
# New project
Read HARNESS_PROMPT.md and run it.

# Returning to existing project
You are [AGENT_ID]. Scenario B.

# Convert existing codebase
Read HARNESS_PROMPT.md and run it.
This is an existing non-Harness project — Scenario C.

# Upgrade old Harness version
Read HARNESS_PROMPT.md and run it.
Upgrade this project to v11.0 — Scenario D.
```

---

*Agentic Harness v11.0 | AgenticHarness.io | By Solomon Christ*
*© Solomon Christ Holdings Inc. — The OPC Stack. One person. Virtual team. Real results.*
