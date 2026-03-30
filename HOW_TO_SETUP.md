# 🦂 Agentic Harness — Complete Setup Guide
# By Solomon Christ | AgenticHarness.io
# Version 11.0

Welcome to the OPC Stack. One person. Virtual team. Real results.
This guide gets you from zero to a running AI agent team in under 30 minutes.

---

## WHAT YOU'RE BUILDING

```
MyAIProjects/                        ← your top-level folder
├── TelegramBot/                     ← your 24/7 Executive Assistant
├── VirtualWorlds/                   ← 2D/3D/VR world to watch your agents
├── ai-SecondBrain/                  ← your first project (your personal agent)
├── AI-CPA-Financials/               ← example: a financial agent project
└── (more projects as you grow)

~/.harness/                          ← global Harness data (auto-created)
├── souls/                           ← all agent identity files (shared across projects)
├── agents/                          ← AGENTS.md global roster
└── skills/                          ← reusable skills across projects
```

**Access your agents via:**
- Claude Code (directly in terminal)
- Telegram bot on your phone (any time, anywhere)
- 2D RPG world map at `http://localhost:8888`
- 3D night city view at `http://localhost:8888/world3d.html`
- WebXR VR on your headset at `http://localhost:8888/worldvr.html`
- Unity/Unreal C# data feed at `http://localhost:8888/api/world/unity`

---

## PART 1 — INSTALL THE TOOLS (one time)

### 1. Claude Code
Download and install from: https://claude.com/product/claude-code

Claude Code is the terminal-based AI that powers your agents.
It's what actually does the work when your agents run.

### 2. VS Code
Download from: https://code.visualstudio.com

### 3. VS Code Extensions
Open VS Code → Extensions panel (Ctrl+Shift+X) → install these:
- **Claude Code** — integrates Claude into VS Code
- **Pixel Agents** — visual agent monitoring in VS Code

Restart VS Code after installing.

### 4. Python 3 (for World Server + Telegram Bot)
Download from: https://python.org/downloads
⚠️ Windows: check **"Add Python to PATH"** during installation.

### 5. Node.js (optional — only needed if you use the TypeScript bot)
Download from: https://nodejs.org

---

## PART 2 — CREATE YOUR PROJECT STRUCTURE (5 minutes)

### Step 1: Create your top-level folder
```
Windows: C:\Users\YourName\MyAIProjects\
Mac/Linux: ~/MyAIProjects/
```

Inside it, create your first project folder:
```
MyAIProjects/
└── ai-SecondBrain/
```

### Step 2: Open in VS Code
File → Open Folder → select `MyAIProjects`
Click "Yes, I trust the authors"

### Step 3: Download HARNESS_PROMPT.md
Visit AgenticHarness.io → Download `HARNESS_PROMPT.md`
Place it inside `ai-SecondBrain/`:
```
MyAIProjects/
└── ai-SecondBrain/
    └── HARNESS_PROMPT.md
```

---

## PART 3 — START YOUR FIRST AGENT (10 minutes)

### Step 1: Open terminal in VS Code
Terminal → New Terminal

### Step 2: Navigate to your project
```bash
cd ai-SecondBrain
```

### Step 3: Login to Claude Code
```bash
claude
/login
```
Use your Claude Pro subscription ($20/month at claude.ai).

### Step 4: Switch to Haiku model (cost-efficient for agents)
```
/model
```
Select `claude-haiku-4-5` (fast, cheap, great for agents)

### Step 5: Initialize your first agent
Paste this (customize the name):
```
I want you to go to my ai-SecondBrain project and read 
HARNESS_PROMPT.md. You are to be my personal agent —
my Second Brain. I am calling you [YOUR_BOT_NAME].
```

The agent will:
1. Read HARNESS_PROMPT.md
2. Detect Scenario C (existing folder, no Harness yet)
3. Set up all 10 LAYER files
4. Create `.claude/CLAUDE.md` (so future sessions auto-boot)
5. Ask you 9 questions to understand the project
6. Print its WHO_AM_I card

**Example WHO_AM_I card:**
```
🤖 SecondBrain-Sage-01 · 🧠 Sage · ai-SecondBrain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Remember everything. Miss nothing."
Score: 0pts · TRUSTED · 0 tasks done

📋 5 TODO · 0 ACTIVE · 0 DONE
▶ ACTIVE:  none
⏰ NEXT:   Set up first milestone

Summon: "You are SecondBrain-Sage-01. Scenario B."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What do you need?
```

### Step 6: Next time you open this project
Just open Claude Code in the project folder.
It auto-reads `.claude/CLAUDE.md` → auto-boots Harness → prints WHO_AM_I card.
**You never have to paste the prompt again.**

---

## PART 4 — SETUP TELEGRAM (5 minutes)

Your 24/7 Executive Assistant on your phone.

### Step 1: Create a Telegram bot
1. Open Telegram on your phone
2. Search `@BotFather`
3. Send `/newbot`
4. Follow prompts — give it a name and username
5. Copy the **token** BotFather gives you (looks like `1234567890:ABC...`)

### Step 2: Get your Telegram user ID
1. Search `@userinfobot` in Telegram (all lowercase)
2. Send `/start`
3. Copy the **Id:** number from the response

### Step 3: Set up the bot files
```bash
# Navigate to your projects root
cd MyAIProjects

# Create TelegramBot folder
mkdir TelegramBot
cd TelegramBot
```

Copy `telegram_bot.py`, `.env.telegram.template`, and `start_telegram.bat` into this folder.

### Step 4: Configure credentials
```bash
# Windows
copy .env.telegram.template .env.telegram
notepad .env.telegram

# Mac/Linux
cp .env.telegram.template .env.telegram
nano .env.telegram
```

Fill in:
```
TELEGRAM_BOT_TOKEN=your_token_from_botfather
TELEGRAM_ALLOWED_USER_IDS=your_id_from_userinfobot
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects
BOT_NAME=My Assistant
OWNER_NAME=YourFirstName
```

### Step 5: Install Python dependencies
```bash
pip install requests python-dotenv
```

### Step 6: Start the bot
```bash
# Windows: double-click start_telegram.bat
# OR from terminal:
python telegram_bot.py
```

### Step 7: Test it
Open Telegram → find your bot → send `/start`

You should see a welcome message with all your projects listed.

### Step 8: Keep it running
- Windows: double-click `start_telegram.bat` (auto-restarts on crash)
- Mac/Linux: add to system startup or run in a `screen`/`tmux` session
- The bot only works while your computer is on

---

## PART 5 — SETUP THE VIRTUAL WORLD (5 minutes)

Watch your agents in 2D, 3D, and VR.

### Step 1: Create VirtualWorlds folder
```
MyAIProjects/
└── VirtualWorlds/
    ├── world_server.py
    ├── world.html
    ├── world3d.html
    ├── worldvr.html
    ├── install.py
    └── install.bat
```

Download these files from AgenticHarness.io.

### Step 2: Install dependencies
```bash
cd VirtualWorlds
python install.py
```

Or on Windows: double-click `install.bat`

### Step 3: Configure
Open `.env` in VirtualWorlds and set:
```
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects
```

### Step 4: Start the world server
```bash
python world_server.py
```

Or double-click `start_world.bat`

### Step 5: Open in browser
- 2D world: http://localhost:8888
- 3D world: http://localhost:8888/world3d.html
- VR: http://localhost:8888/worldvr.html (requires WebXR headset)

### LAN access (view from any device on your network)
```bash
ipconfig  # Windows — find your IPv4 address (e.g. 192.168.1.100)
ifconfig  # Mac/Linux
```
Then use: http://192.168.1.100:8888 on any device on your network.

---

## PART 6 — ADD MORE PROJECTS

Every new project follows the same pattern:

```bash
# 1. Create folder inside MyAIProjects
mkdir MyAIProjects\NewProject

# 2. Copy HARNESS_PROMPT.md into it
copy HARNESS_PROMPT.md MyAIProjects\NewProject\

# 3. Open Claude Code in that folder
cd MyAIProjects\NewProject
claude

# 4. Tell Claude to initialize (one time only)
"Read HARNESS_PROMPT.md and run it. You are [AgentName]."
```

The agent handles the rest. The world server and Telegram bot
automatically discover the new project on their next poll.

---

## PART 7 — DAILY WORKFLOW

### Morning
1. Turn on computer
2. Start Telegram bot: double-click `start_telegram.bat`
3. Start world server: double-click `start_world.bat`
4. Open Telegram → your bot sends "Online. Watching X projects."

### Adding tasks from phone
```
/add ai-SecondBrain | Review the Q2 report | HIGH
```
or just:
```
Add a HIGH task to my SecondBrain project to review the Q2 report
```

### Waking an agent
```
/wake ai-SecondBrain
```
Bot shows: "Open Claude Code and paste: `You are SecondBrain-Sage-01. Scenario B.`"

### Checking status
```
/status → full system overview
/projects → per-project status
/agents → all agents + summon commands
/tasks → all task queues
```

### Agent working autonomously
Once woken, the agent works until done and notifies you via Telegram when:
- A task is complete
- Something is blocked
- It needs your input
- A milestone is reached

---

## STANDARD FOLDER STRUCTURE (after full setup)

```
MyAIProjects/
│
├── TelegramBot/                     ← your EA bot
│   ├── telegram_bot.py
│   ├── .env.telegram                ← your credentials (gitignored)
│   ├── .env.telegram.template
│   ├── start_telegram.bat
│   └── data/
│
├── VirtualWorlds/                   ← world server
│   ├── world_server.py
│   ├── world.html
│   ├── world3d.html
│   ├── worldvr.html
│   ├── .env
│   └── start_world.bat
│
├── ai-SecondBrain/                  ← project 1
│   ├── HARNESS_PROMPT.md
│   ├── AGENT_CARD.md
│   ├── PROJECT.md
│   ├── LAYER_ACCESS.MD
│   ├── LAYER_CONFIG.MD
│   ├── LAYER_HEARTBEAT.MD
│   ├── LAYER_LAST_ITEMS_DONE.MD
│   ├── LAYER_MEMORY.MD
│   ├── LAYER_SHARED_TEAM_CONTEXT.MD
│   ├── LAYER_TASK_LIST.MD
│   ├── AGENTS.md
│   ├── .claude/
│   │   ├── CLAUDE.md                ← auto-boot file
│   │   └── settings.json
│   ├── SKILLS/
│   └── [your project files]
│
└── AI-CPA-Financials/               ← project 2
    └── (same structure)

~/.harness/                          ← global (auto-created)
├── souls/
│   ├── SOUL_SecondBrain-Sage-01.md
│   └── SOUL_MaxMoney-Guardian-01.md
├── agents/
│   └── AGENTS.md                    ← global roster
└── skills/
    └── [shared skills]
```

---

## SUMMON COMMANDS REFERENCE

Every agent has a summon command shown in the Telegram `/agents` output.
To wake an agent, open Claude Code in their project folder and paste it:

```
You are [AGENT_ID]. Scenario B.
```

Example:
```
You are SecondBrain-Sage-01. Scenario B.
```

The agent boots, reads LAYER files, prints its WHO_AM_I card,
checks for any `.harness_wake` file, and starts working.

---

## TROUBLESHOOTING

**Agent doesn't boot automatically**
→ Check .claude/CLAUDE.md exists in the project folder
→ If not: open Claude Code in the folder and paste:
  `Read HARNESS_PROMPT.md and run it.`

**Telegram bot can't find projects**
→ Check HARNESS_PROJECTS_PATH in .env.telegram
→ Path must point to the PARENT folder containing project subfolders
→ Windows: use forward slashes or escaped backslashes

**World server shows no projects**
→ Check .env in VirtualWorlds: HARNESS_PROJECTS_PATH
→ Projects must have LAYER_HEARTBEAT.MD inside them

**No agents showing in world**
→ Soul files must be in ~/.harness/souls/ (run harness_migrate.py)
→ OR session must have run at least once to create SOUL_*.md

**"Model not found" error in Claude Code**
→ Run /model and select claude-haiku-4-5 (current Haiku model string)

---

## YOU'RE ALL SET

Your Agentic Harness is running. You have:
- ✅ One or more agents working in project folders
- ✅ A Telegram EA bot keeping you connected from your phone
- ✅ A virtual world to watch your team at work
- ✅ A task system that routes work to the right agent

Welcome to the OPC Stack.
One person. Virtual team. Real results.

AgenticHarness.io | SolomonChrist.com
© Solomon Christ Holdings Inc.
