# 🌍 Agentic Harness — VirtualWorlds

> **This folder is optional.** Agentic Harness works with just `HARNESS_PROMPT.md`.
> The VirtualWorlds layer lets you *watch* your agents — it adds nothing they need to run.

---

## What this gives you

Four ways to see your agent team working in real-time. All powered by the same LAYER files your agents already write. One server. Start it once.

| Mode | URL | |
|------|-----|-|
| **2D RPG Office** | `http://localhost:8888/` | Pixel agents, speech bubbles, + TASK panel |
| **3D Night City** | `/world3d.html` | 3D archetype avatars, activity labels, WASD navigation |
| **VR Headset** | `/worldvr.html` | Quest / Pico / Vision Pro via WebXR |
| **Unity / Unreal** | `/api/world/unity` | JSON data feed — poll every 5 seconds |
| **Dashboard** | `http://localhost:8765/dashboard.html` | Stats, notifications, human queue, task form |

Agents appear in the world **even when offline** — discovered from SOUL files, not just active sessions.

---

## Setup (10 minutes)

### 1. Copy these files into a `VirtualWorlds/` folder on your machine

```
world_server.py
world.html
world3d.html
worldvr.html
dashboard_server.py
dashboard.html
install.py
install.bat        ← Windows
start_world.bat    ← Windows launcher
start_world.sh     ← Mac/Linux launcher
start_all.bat      ← Windows: starts world + Telegram together
```

### 2. Run the installer

```bash
# Windows — double-click install.bat
# Mac/Linux
python3 install.py
```

### 3. Edit .env — set your projects path

Open `VirtualWorlds/.env` and change one line:

```bash
# Windows:
HARNESS_PROJECTS_PATH=C:\Users\YourName\MyAIProjects

# Mac/Linux:
HARNESS_PROJECTS_PATH=/Users/yourname/MyAIProjects
```

### 4. Start

```bash
# Windows — double-click start_world.bat
# Mac/Linux
./start_world.sh
```

### 5. LAN access (phone, tablet, VR headset)

```bash
# Find your local IP:
Windows: ipconfig      → look for IPv4 Address
Mac:     ifconfig      → look for inet

# Then visit: http://192.168.x.x:8888/
```

---

## How the world discovers agents

The server scans your projects folder for:
1. `SOUL_*.md` files in each project (and in `~/.harness/souls/` globally)
2. `AGENT_CARD.md` — display name, archetype, stats
3. `LAYER_LAST_ITEMS_DONE.MD` — latest action
4. `LAYER_TASK_LIST.MD` — current active task

No agents need to be online for them to appear. The world reflects what the files say.

---

*Part of the Agentic Harness OPC Stack | AgenticHarness.io*
*By Solomon Christ | © Solomon Christ Holdings Inc.*
