# 🦂 Agentic Harness v11.0

**The Universal Standard for Autonomous AI Agent Swarms**

*By Solomon Christ | [AgenticHarness.io](https://AgenticHarness.io) | [SolomonChrist.com](https://SolomonChrist.com)*

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-11.0-orange.svg)](https://github.com/SolomonChrist/AgenticHarness)
[![Works With](https://img.shields.io/badge/works%20with-Claude%20Code%20%7C%20OpenCode%20%7C%20Cursor%20%7C%20Windsurf%20%7C%20Gemini%20%7C%20Any%20Agent-green.svg)](https://github.com/SolomonChrist/AgenticHarness)

</div>

---

## You need one file.

```
HARNESS_PROMPT.md
```

Copy it into any project folder. Paste it into any AI agent. That's Agentic Harness.

```
Read HARNESS_PROMPT.md and run it.
```

The agent detects your situation, sets everything up, and starts working. No configuration. No framework to install. No lock-in. Just a Markdown file that any AI can read.

---

## What happens when you run it

The agent detects one of four situations automatically:

| | Situation | What the agent does |
|-|-----------|---------------------|
| **A** | New empty folder | Creates all files, asks you 9 setup questions, starts building |
| **B** | Existing Harness project | Loads identity, prints WHO_AM_I card, claims top task, works |
| **C** | Existing project (no Harness) | Backs everything up, reads the project, converts it, renames itself |
| **D** | Older Harness version | Detects version, reports changes, migrates to v11.0, continues |

After first boot, the agent writes `.claude/CLAUDE.md` to your project. Claude Code reads it automatically every future session. **You never paste again.**

---

## The ten files every Harness project uses

Plain Markdown. Git-tracked. Any model reads them. Any platform runs them.

| File | Purpose |
|------|---------|
| `SOUL_[AGENT_ID].md` | Agent identity, personality, history. Lives at `~/.harness/souls/` — travels across every project. |
| `PROJECT.md` | Mission, milestones, security level, autonomy mode. |
| `LAYER_ACCESS.MD` | Security gate. Trust tiers. Who can work here. |
| `LAYER_CONFIG.MD` | Agent registry, reputation scores, model budget. |
| `LAYER_MEMORY.MD` | Permanent decisions + retrospectives. Append only. Never delete. |
| `LAYER_TASK_LIST.MD` | Checkbox work queue. Lane locks. Human checkout. |
| `LAYER_SHARED_TEAM_CONTEXT.MD` | Team whiteboard. Handoff notes. Context snapshots. |
| `LAYER_HEARTBEAT.MD` | Liveness signal. Crash detection. Dashboard feed. |
| `LAYER_LAST_ITEMS_DONE.MD` | Every action logged. `📨` entries = notification bus. |
| `AGENT_CARD.md` | WHO_AM_I card. Human-readable. Always current. |

---

## Works with every major agent platform

`AGENTS.md` in this repo is the universal boot file. Copy it into any project.

| File | Platform |
|------|----------|
| `AGENTS.md` | OpenCode · Codex CLI · Cursor · Aider · Zed · Windsurf |
| `.claude/CLAUDE.md` | Claude Code (auto-reads every session) |
| `GEMINI.md` | Gemini CLI · Gemini Code Assist |
| `.cursorrules` | Cursor (legacy) |
| `.windsurfrules` | Windsurf (legacy) |
| `.github/copilot-instructions.md` | GitHub Copilot |

All created automatically by `install.py`. Run it once per machine.

---

## Real results

**ai-SecondBrain** — one afternoon, Scenario C conversion:
```
Tasks completed:  9 (5 M1 + 4 M2)
Code written:     654+ lines TypeScript
Git commits:      11
Token cost:       ~$0.50
Equivalent value: ~$2,000 (1 senior dev × 2 days)
```

**AI-CPA-Financials** — ongoing financial management:
```
Agent:  MaxMoney-Guardian-01 (Guardian archetype, self-selected)
Role:   CFO + financial advisor across 7 entities, 2 jurisdictions
Model:  Claude Haiku 4.5 on $20/month Claude Pro
Result: Full tax strategy, CPA coordination, April 10 deadline managed
Human time: review + sign-off only
```

---

## Security built in

Every project has a security level and a trust tier system:

```
Security levels:
  OPEN    → anyone can join (learning/personal projects)
  MANAGED → listed agents only, approval required (default)
  STRICT  → pre-approved list only (financial/medical/legal)
  LOCKED  → read nothing, write nothing (archived)

Trust tiers:
  🔴 GUEST    → read only
  🟡 TRUSTED  → standard work (read, write, commit)
  🟢 OPERATOR → approve agents, destructive actions
  ⭐ OWNER    → full control (humans default here)
```

Auto-detection: financial, medical, or legal project → agent recommends STRICT.
Reputation auto-promotion at 50 / 150 / 500 points — humans always confirm.

---

## The OPC Stack — optional, powerful

The Harness works with just `HARNESS_PROMPT.md`. Once you're running agents on real projects, you may want the full **OPC Stack** — the operational layer that lets one person run a virtual organization:

### 🌍 VirtualWorlds/ — Watch your agents live

Four rendering modes, one server. Start it once, all four are live.

| Mode | URL | What it shows |
|------|-----|---------------|
| 2D RPG Office | `http://localhost:8888/` | Agents walking, speech bubbles, + TASK panel |
| 3D Night City | `/world3d.html` | Archetype-colored 3D avatars, activity labels |
| VR Headset | `/worldvr.html` | Quest / Pico / Vision Pro immersive |
| Unity / Unreal | `/api/world/unity` | JSON feed, poll every 5 seconds |

Agents appear in the world even when offline — discovered from SOUL files, not just active sessions.

### 📱 TelegramBot/ — Control everything from your phone

One bot. All projects. 24/7 access.

```
/projects   → all project status
/agents     → agent roster + summon commands
/tasks      → all task queues
/add proj | task | HIGH   → queue a task from your phone
/wake project   → get summon command for offline agent
/status     → full system overview

Or just say: "Add a HIGH task to SecondBrain to fix the auth bug"
```

Every `📨` notification your agents write gets forwarded to your phone in real-time.

**The wake protocol:** Add a task from Telegram → `.harness_wake` written to project → agent reads it on next session open → picks up the task immediately.

---

## This repo at a glance

```
AgenticHarness/
│
├── HARNESS_PROMPT.md          ← The protocol. This is all you need.
├── README.md                  ← You're reading it
├── SETUP.md                   ← Step-by-step: Agent → Worlds → Telegram
├── FOLDER_STRUCTURE.md        ← Where everything goes on your machine
│
├── AGENTS.md                  ← Universal platform boot file
├── GEMINI.md                  ← Gemini CLI boot file
├── CLAUDE.md                  ← Claude Code fallback
├── CLAUDE.md.template         ← For .claude/CLAUDE.md auto-boot setup
│
├── project-template/          ← Copy this folder to start any project
│   ├── HARNESS_PROMPT.md
│   ├── AGENTS.md · GEMINI.md · CLAUDE.md
│   └── .claude/
│       ├── CLAUDE.md          ← auto-boot every session
│       └── settings.json      ← pre-approves LAYER file writes
│
├── VirtualWorlds/             ← OPTIONAL: 2D/3D/VR world + dashboard
│   └── [see VirtualWorlds/README.md]
│
├── TelegramBot/               ← OPTIONAL: Personal EA bot
│   └── [see TelegramBot/README.md]
│
└── tools/
    └── harness_migrate.py     ← Migrate existing projects to v11.0
```

---

## Version history

| Version | What changed |
|---------|-------------|
| v11.0 | WHO_AM_I card · global souls · universal platform boot · Telegram EA · 2D/3D/VR worlds · rename protocol · wake protocol · 28 hard rules |
| v10.0 | The OPC Stack · personality archetypes · AGENT_CARD · nightly retrospective · subagents |
| v9.0 | Telegram bot · web dashboard · reputation system |
| v8.0 | Three-scenario auto-detection · BACKUP on conversion · SKILLS/ folder |
| v7.0 | LAYER_ACCESS.MD · trust tiers · approval gate |
| v5.0 | SOUL.md · STANDBY mode · multi-project rotation |
| v1.0 | Initial concept — 6 layers, boot sequence |

---

## The ecosystem

The protocol is open and MIT licensed. The full ecosystem lives at **[AgenticHarness.io](https://AgenticHarness.io)**.

```
OPEN SOURCE (this repo):
  ✅ HARNESS_PROMPT.md v11.0
  ✅ VirtualWorlds (2D/3D/VR/Unity)
  ✅ TelegramBot (Personal EA)
  ✅ Migration tools

COMING AT AGENTICHARNESS.IO:
  → Manifesto
  → Core framework diagram
  → Maturity model (Level 1–5)
  → Official terminology glossary
  → Starter certification
  → Enterprise certification
  → Case studies and proof stack
  → Trainer / partner licensing
```

---

## The origin

This started as frustration — not a framework.

Running AI agents on real projects and hitting the same walls every time: fragmentation (every tool locked you in), context loss (agents forget everything when sessions end), cost (capable models aren't cheap 24/7).

The Harness is what solved those problems for one person running real projects. Every version change traces back to something that broke in production. The complexity is in the system. Your workflow stays simple.

---

## License

MIT — free to use, modify, distribute.

Attribution appreciated: *"Built on Agentic Harness by Solomon Christ — AgenticHarness.io"*

Training materials, certifications, and ecosystem products are separate and owned by **Solomon Christ Holdings Inc.**

---

<div align="center">

**🦂 Agentic Harness v11.0**

*The complexity is in the system. Not in your workflow.*

[AgenticHarness.io](https://AgenticHarness.io) · [SolomonChrist.com](https://SolomonChrist.com) · [GitHub](https://github.com/SolomonChrist/AgenticHarness)

*© Solomon Christ Holdings Inc. All rights reserved.*

</div>
