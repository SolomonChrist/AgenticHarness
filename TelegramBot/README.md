# 📱 Agentic Harness — Telegram Personal Executive Assistant

> **This folder is optional.** Agentic Harness works with just `HARNESS_PROMPT.md`.
> The Telegram EA bot lets you *control* your agents from anywhere — it adds nothing they need to run.

---

## What this gives you

One Telegram bot. All your Harness projects. 24/7 access from any device.

- **📨 Real-time notifications** — every `📨` entry your agents write arrives on your phone
- **📋 Full visibility** — `/projects` `/agents` `/tasks` on demand
- **➕ Task routing** — add tasks from your phone, routed to the right project
- **⚡ Wake protocol** — task added → `.harness_wake` written → agent picks it up on next boot
- **🗺 Smart routing** — natural language: *"Add a HIGH task to SecondBrain to fix the auth bug"*

Runs on your machine. No cloud servers. Private. Just Python and the Telegram Bot API.

---

## Setup (5 minutes)

### 1. Create your Telegram bot

1. Open Telegram → search **@BotFather** → send `/newbot`
2. Follow prompts → **copy the TOKEN** (looks like `1234567890:ABCdef...`)
3. Open Telegram → search **@userinfobot** → send `/start` → **copy your ID number**

### 2. Copy these files into a `TelegramBot/` folder on your machine

```
telegram_bot.py
.env.telegram.template
start_telegram.bat    ← Windows
start_telegram.sh     ← Mac/Linux
```

### 3. Configure credentials

```bash
# Windows
copy .env.telegram.template .env.telegram

# Mac/Linux
cp .env.telegram.template .env.telegram
```

Edit `.env.telegram` — fill in these fields:

```bash
TELEGRAM_BOT_TOKEN=your_token_from_botfather
TELEGRAM_ALLOWED_USER_IDS=your_id_from_userinfobot
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects
BOT_NAME=My AI Assistant
OWNER_NAME=YourFirstName
```

### 4. Install and start

```bash
pip install requests python-dotenv

# Windows — double-click start_telegram.bat
# Mac/Linux
chmod +x start_telegram.sh
./start_telegram.sh
```

### 5. Test from your phone

Find your bot in Telegram → send `/start`

---

## Commands

```
/start              → welcome message + all commands
/projects           → all project status at a glance
/agents             → full agent roster + summon commands
/tasks              → task queues across all projects
/tasks [name]       → one specific project's tasks
/add [proj] | [task] | [PRIORITY]   → queue a task
/wake [project]     → get summon command for offline agent
/status             → full system summary
```

Or just talk naturally:
```
"What's the status on the CPA project?"
"Add a HIGH task to SecondBrain to fix the login bug"
"Wake my finance agent"
```

---

## The wake protocol

```
You add a task via Telegram:
  1. EA writes task to LAYER_TASK_LIST.MD
  2. EA writes 📨 NOTIFY to LAYER_LAST_ITEMS_DONE.MD
  3. EA writes .harness_wake to project folder

Agent is offline. Time passes.

You open Claude Code in that project:
  → .claude/CLAUDE.md auto-reads → Scenario B boot
  → Agent checks for .harness_wake → found
  → Agent reads wake reason, deletes file, claims queued task
  → Begins work immediately
```

---

## Running on multiple machines

Each machine can run its own EA bot with its own Telegram token.
All bots can report to your single Telegram account via `TELEGRAM_ALLOWED_USER_IDS`.
One phone. Multiple machines. Multiple business units.

---

*Part of the Agentic Harness OPC Stack | AgenticHarness.io*
*By Solomon Christ | © Solomon Christ Holdings Inc.*
