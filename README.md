# 🦂 Agentic Harness

**The Universal Standard for Autonomous AI Agent Swarms**

*By Solomon Christ | [AgenticHarness.io](https://AgenticHarness.io) | [SolomonChrist.com](https://SolomonChrist.com)*

---

<div align="center">

**Paste it. Boot it. Build it.**

*Simple enough to teach. Secure enough to trust. Powerful enough to run a company.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-7.0-blue.svg)](https://github.com/SolomonChrist/AgenticHarness)
[![Works With](https://img.shields.io/badge/works%20with-Claude%20Code%20%7C%20OpenCode%20%7C%20OpenClaw%20%7C%20Cursor%20%7C%20Any%20Agent-green.svg)](https://github.com/SolomonChrist/AgenticHarness)

</div>

---

## What Is This?

The AI agent ecosystem has a fragmentation problem. There are dozens of agent systems — Claude Code, OpenCode, OpenClaw, Cursor, Windsurf, Antigravity, Codex, Gemini CLI, GSD, CrewAI, LangChain — and none of them speak the same language. Every project gets locked in. Every migration is a rewrite. Every agent swarm requires a custom architecture.

**The Agentic Harness solves this with nine plain Markdown files and a single prompt.**

Drop the prompt into any agent system. It boots, reads the files, picks up where the last agent left off, and starts working. Whether the previous agent was Claude Code, an Ollama local model, or OpenClaw — it doesn't matter. The files are the protocol. The files are the handoff. The files are the memory.

> *"The complexity is in the system. Not in your workflow."*

---

## The Core Idea

Every serious agent system ever built needs the same nine things:

| What Every Agent Needs | The Harness File |
|------------------------|-----------------|
| Who the agent is | `SOUL.md` |
| What the project is | `PROJECT.md` |
| Who is allowed in | `LAYER_ACCESS.MD` |
| Infrastructure & registry | `LAYER_CONFIG.MD` |
| Long-term memory | `LAYER_MEMORY.MD` |
| The work queue | `LAYER_TASK_LIST.MD` |
| Team coordination | `LAYER_SHARED_TEAM_CONTEXT.MD` |
| Is the agent alive? | `LAYER_HEARTBEAT.MD` |
| What just happened? | `LAYER_LAST_ITEMS_DONE.MD` |

Plain Markdown. Version-controlled with Git. Readable by any human. Writable by any agent. That's it.

---

## Quick Start

```bash
# 1. Navigate to your project folder
cd /your/project/folder

# 2. Paste the contents of HARNESS_PROMPT.md into your agent
# 3. The agent boots, creates all files, asks you to define the project
# 4. You answer 7 questions. Agent starts building.
```

The agent handles everything else — identity, file creation, git commits, heartbeat, handoffs.

---

## How It Works

### The Nine Files

Every Harness project is a folder with nine files. Create them yourself or let the agent create them on first boot.

```
your-project/
├── SOUL.md                        # Agent identity & capabilities
├── PROJECT.md                     # Mission, mode, milestones
├── LAYER_ACCESS.MD                # 🔒 Who is allowed. Trust tiers.
├── LAYER_CONFIG.MD                # Agent registry, rotation list
├── LAYER_MEMORY.MD                # Permanent decisions (append only)
├── LAYER_TASK_LIST.MD             # Work queue
├── LAYER_SHARED_TEAM_CONTEXT.MD   # Team whiteboard
├── LAYER_HEARTBEAT.MD             # Liveness signals
└── LAYER_LAST_ITEMS_DONE.MD       # One-line audit trail
```

### The Agent Identity

Every agent that joins a project builds an `AGENT_ID`:

```
[MODEL]-[ROLE]-[##]

Claude-Builder-01
Qwen-Coder-DevOps-01
OpenCode-Reviewer-02
Agent-Research-01-a3f7    ← unknown model gets random hex suffix
```

This ID appears in every log entry, every task claim, every team message. You always know who did what.

### The Task System

```
[ ] TODO              → available
[→] IN PROGRESS [ID]  → claimed by Claude-Builder-01
[✓] DONE              → complete (never deleted)
[✗] BLOCKED           → needs human input
[⏸] STANDBY          → no tasks, waiting
```

**Lane locks** prevent two agents claiming the same task — the first agent to write its ID owns it. No semaphores. No distributed consensus. Just a convention that scales.

### Project Modes

Tell the agent how to work based on what matters for your project:

| Mode | What it means |
|------|--------------|
| 💰 **SAVINGS** | Minimize tokens. Smaller models. Batch operations. |
| ✅ **COMPLETION** | Quality first. Best models. Verify everything. |
| ⚡ **SPEED** | Fastest path. Parallel where possible. Skip polish. |
| 🧠 **CAPABILITIES** | Match tasks to best agent type. |
| 🎯 **MIX** | Custom blend — e.g. `60% COMPLETION + 40% SAVINGS` |

---

## Security: The Approval Gate

Agent security is broken across the industry. [Only 14.4% of organizations send agents to production with full security approval.](https://www.gravitee.io/blog/state-of-ai-agent-security-2026-report-when-adoption-outpaces-control)

The Harness solves this with one file and four tiers.

### Trust Tiers

```
🔴 GUEST    → Read only. Cannot claim tasks or write files.
🟡 TRUSTED  → Standard worker. Can read, write, commit.
🟢 OPERATOR → Team lead. Can manage config and approve TRUSTED agents.
⭐ OWNER    → Full control. Sets security level. Approves all tiers.
```

### Security Levels

```
OPEN    → Any agent joins automatically. Good for learning.
MANAGED → New agents start as GUEST. Human approves upgrades. (Recommended)
STRICT  → Pre-approved only. Unknown agents are hard-blocked.
LOCKED  → Roster frozen. No new agents. Good for archives.
```

### The Approval Flow

1. Unknown agent boots into your project
2. It reads `LAYER_ACCESS.MD` — it's not listed
3. It posts a request with: model, system, capabilities, reason
4. **It stops completely.** Cannot read files. Cannot claim tasks.
5. You open `LAYER_ACCESS.MD`, review, approve with a tier
6. Agent resumes from where it stopped

One file edit. That's all approval takes. No dashboard. No infrastructure.

**The OpenClaw problem:** An OpenClaw agent (or any untrusted agent) that boots into a `STRICT` project gets: `"⚠️ Project is STRICT. Not pre-approved."` — hard stop. Zero access.

---

## Multi-Agent Swarms

Agents don't communicate directly — they coordinate through files. This asynchronous pattern works across any system, any model, any language.

### Swarm Patterns

**Solo** — One agent, all roles. Good for learning and small projects.

**Power Pair** — Planner breaks down the project, Builder executes tasks.

**Full Team**
```
Claude-Planner-01   → PROJECT.md + task breakdown
Claude-Builder-01   → writing code
Qwen-Reviewer-01    → reviewing work
Claude-DevOps-01    → git + deployment
Claude-Research-01  → gathering context
```

**Heterogeneous Swarm** — Match models to what they're best at:
```
Claude          → reports, writing, complex reasoning
Qwen-Coder      → code generation, debugging
Gemini          → research, long context, multimodal
OpenCode        → codebase-wide refactoring
OpenClaw/Claw   → multi-channel, scheduled, 24/7 monitoring
```

### Takeover Protocol

When an agent crashes or disconnects, the next agent to boot:
- Detects the stale heartbeat (>10 minutes, no SESSION_CLOSE)
- Logs a takeover event
- Resets orphaned `IN PROGRESS` tasks to `TODO`
- Claims them under its own ID
- Continues without missing a beat

---

## Project Capacity & Rotation

One agent can serve multiple projects. The math:

```
5-minute time slices × 288 slices/day = 1,440 minutes/day
Default capacity: 8 projects (~90 min/project/day)
Maximum capacity: 256 projects (~5 min/project/day)
```

### Rotation Strategies

```
EQUAL      → Equal time across all projects
WEIGHTED   → Custom percentages (40% client-a, 30% client-b...)
PRIORITY   → HIGH first, then MED, then LOW
COMPLETION → Finish one project before moving to next
TRIAGE     → Check all projects, work most urgent
CUSTOM     → Agent decides based on project modes and urgency
```

**Security note:** Being approved in project-a grants zero access to project-b. Each project has its own gate.

---

## The Boot Sequence

Every agent runs this exact sequence, in order, every session:

```
1.  pwd / cd              → Lock HARNESS_ROOT
2.  Read SOUL.md          → Know who you are
3.  Read LAYER_ACCESS.MD  → APPROVAL GATE — not approved? Stop.
4.  Read PROJECT.md       → Know what you're building
5.  Read all LAYER files  → Load full context
6.  Takeover check        → Detect and claim orphaned work
7.  Register              → Write to agent registry
8.  Open heartbeat        → Signal you're alive
9.  Git check + commit    → Version control from the start
10. Read task list        → Find your first task
```

Agents **do not narrate** this sequence. They execute it.

---

## The Runtime Loop

```
→ Do the work
→ Log every action to LAYER_LAST_ITEMS_DONE (one line per action)
→ Every  5 min: write PULSE to LAYER_HEARTBEAT
→ Every 15 min: git commit
→ Meaningful decision → one line to LAYER_MEMORY
→ Task done → mark [✓] DONE, write handoff, commit, claim next
→ Blocked → mark [✗] BLOCKED, post in team context, ask user
→ All done → enter STANDBY, pulse every 5 min, rotate or wait
```

---

## Session Close

**Always.** Before shutting down, every agent runs:

```bash
# Update task states
# Update SOUL.md (increment tasks done, add notes)
# Write handoff note to LAYER_SHARED_TEAM_CONTEXT
# Mark INACTIVE in registry
# Write HEARTBEAT CLOSE
# Write SESSION_CLOSE to audit log
git add -A && git commit -m "🔒 session close: [AGENT_ID]"
```

A clean shutdown means any agent — on any system, any model — picks up exactly where you left off.

---

## The Vision: From Projects to Worlds

The same nine files that coordinate software agents can coordinate characters in a virtual world.

| Harness File | Virtual World Equivalent |
|-------------|------------------------|
| `SOUL.md` | Character sheet — who this agent/character is |
| `PROJECT.md` | World rulebook — laws of the world, win conditions |
| `LAYER_ACCESS.MD` | Faction/clearance system — who can enter which areas |
| `LAYER_CONFIG.MD` | World registry — all characters, their factions, last locations |
| `LAYER_MEMORY.MD` | World history — everything that has ever happened |
| `LAYER_TASK_LIST.MD` | Events queue — pending actions and world events |
| `LAYER_SHARED_TEAM_CONTEXT.MD` | Public record — character dialogue, announcements |
| `LAYER_HEARTBEAT.MD` | World clock — tick system, time passing |
| `LAYER_LAST_ITEMS_DONE.MD` | Chronicle — one-line record of every action taken |

The Harness becomes the logic backend. A renderer (2D canvas, Three.js, Godot) reads `WORLD_STATE.md` and draws the environment. Agents write their actions. The world updates. NPCs with genuine memory, real reasoning, and persistent histories.

**Text simulation → 2D visual world → 3D virtual environment → persistent civilization.**

---

## Compatible Systems

The Harness is a standard, not a platform. It works with:

| System | Status |
|--------|--------|
| Claude Code | ✅ Native |
| OpenCode | ✅ Native |
| OpenClaw | ✅ With MANAGED security level |
| Cursor / Windsurf | ✅ Native |
| Antigravity | ✅ Native |
| Codex | ✅ Native |
| Gemini CLI | ✅ Native |
| Ollama (local models) | ✅ With llama-server + `--jinja` flag |
| GSD | ✅ Can run inside GSD projects |
| GitAgent | ✅ Export-compatible |
| Any system with file + shell access | ✅ |

---

## Model Setup

The Harness works with any model. The right setup depends on where you're running it.

---

### Option A — Cloud Models (Best capability, recommended for production)

When running inside **Claude Code** natively, no model configuration is needed — Claude handles tool execution, file writes, and bash commands with full reliability. This is the highest-capability setup.

```bash
# Just use Claude Code directly — no env vars needed
claude
```

For **OpenCode with cloud models via OpenRouter or direct API:**
```bash
# opencode.json (place in project root)
{
  "model": "anthropic/claude-sonnet-4-5",
  "temperature": 0.2
}
```

Cloud model capability guide:
| Model | Best for | Context |
|-------|---------|---------|
| `claude-sonnet-4-5` | Full harness execution, complex reasoning, writing | 200k |
| `claude-haiku-4-5` | Fast routing, simple tasks, frontend interface | 200k |
| `gemini-1.5-pro` | Research tasks, long context projects | 1M |
| `gpt-4o` | General execution, good tool calling | 128k |

---

### Option B — Local Models via Ollama (Privacy-first, free to run)

Local models are ideal for sensitive projects, offline work, or when you want zero data leaving your machine. The tradeoff is capability and VRAM.

**Important:** Local models run inside **OpenCode** or via the Claude Code + Ollama proxy setup. They do NOT run inside standard Claude Code — Claude Code always routes to Anthropic's API unless you override the base URL.

#### Full Setup (16GB+ VRAM — best local experience)

```
# coder.modelfile — full capability local executor
FROM qwen2.5-coder:7b
PARAMETER num_ctx 32768
PARAMETER num_gpu 99
PARAMETER temperature 0.2
```

```
# frontend.modelfile — interface model
FROM qwen2.5-coder:3b
PARAMETER num_ctx 16384
PARAMETER num_gpu 99
PARAMETER temperature 0.7
```

#### Constrained Setup (6GB VRAM — e.g. GTX 1660 Ti, RTX 3060)

The 6GB constraint is real. A 7b model at full quality needs ~4.5GB just for weights, leaving little room for a large context window. This is the practical sweet spot:

```
# coder.modelfile — fits in 6GB, still useful
FROM qwen2.5-coder:3b
PARAMETER num_ctx 16384
PARAMETER num_gpu 99
PARAMETER temperature 0.2
```

```
# frontend.modelfile — lightweight interface
FROM qwen2.5-coder:1.5b
PARAMETER num_ctx 4096
PARAMETER num_gpu 99
PARAMETER temperature 0.7
```

> **Note on 4k context:** The `frontend` model at 4096 context is intentionally minimal — it only reads `LAYER_CONFIG.MD` and `LAYER_TASK_LIST.MD` on boot (not all 9 files) to stay within its window. It's the interface layer, not the executor. The `coder` model at 16k does the real work.

#### Local model capability guide

| Model | VRAM needed | Context | Best for |
|-------|------------|---------|---------|
| `qwen2.5-coder:7b` | ~5GB | 4k-8k | Best local code quality |
| `qwen2.5-coder:3b` | ~2GB | 16k | Best balance on 6GB GPU |
| `qwen2.5-coder:1.5b` | ~1.5GB | 32k | Max context, lower quality |
| `mistral:7b` | ~5GB | 8k | Best local tool calling |
| `llama3.1:8b` | ~6GB | 8k | Strong general capability |

#### Windows launcher for Claude Code + Ollama proxy

```batch
@echo off
echo Starting LOCAL Claude Code...
set ANTHROPIC_BASE_URL=http://localhost:11434/v1
set ANTHROPIC_AUTH_TOKEN=ollama
set ANTHROPIC_DEFAULT_HAIKU_MODEL=frontend
set ANTHROPIC_DEFAULT_SONNET_MODEL=coder
set ANTHROPIC_MODEL=sonnet
set OLLAMA_KEEP_ALIVE=-1
claude
```

> **Important:** Use `set` not `setx`. `setx` saves to the registry but doesn't apply to the current session — Claude Code won't see the values. Double-click the `.bat` file directly; don't run from PowerShell.

#### Build and warm up

```bash
# Pull base models
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:1.5b

# Build custom models with your parameters
ollama create coder -f coder.modelfile
ollama create frontend -f frontend.modelfile

# Warm up (loads models into GPU memory)
ollama run coder "hello"
ollama run frontend "hello"

# Verify GPU usage — you want 100% GPU, not CPU/GPU split
ollama ps
```

Expected output on a 6GB GPU:
```
NAME              SIZE     PROCESSOR    CONTEXT
coder:latest      1.9 GB   100% GPU     16384
frontend:latest   ~1 GB    100% GPU     4096
```

If you see CPU/GPU split: close Chrome, LM Studio, and other GPU-heavy apps.

---

### Option C — OpenCode with Local Models (Best local tool execution)

OpenCode has native tool execution for Ollama models — it doesn't require the API proxy trick that Claude Code needs. This is the recommended setup when running fully local:

```bash
# Install OpenCode
npm install -g opencode-ai

# Configure in your project (opencode.json)
{
  "model": "ollama/coder",
  "temperature": 0.2
}

# Run
opencode
```

OpenCode handles `Read()`, `Write()`, and `Bash()` tool calls natively with local Ollama models. No proxy needed. No env var tricks.

---

## Repository Structure

```
AgenticHarness/
├── README.md                          # This file — start here
├── HARNESS_PROMPT.md                  # The master prompt — paste into any agent
├── scaffolds/                         # Reference copies of all 9 files
│   ├── SOUL.md                        # ← the agent auto-creates these on first boot
│   ├── PROJECT.md                     #   you don't need to create them manually
│   ├── LAYER_ACCESS.MD
│   ├── LAYER_CONFIG.MD
│   ├── LAYER_MEMORY.MD
│   ├── LAYER_TASK_LIST.MD
│   ├── LAYER_SHARED_TEAM_CONTEXT.MD
│   ├── LAYER_HEARTBEAT.MD
│   └── LAYER_LAST_ITEMS_DONE.MD
└── LEARNING/                          # Learning resources — growing over time
```

**The two files that matter:** `README.md` and `HARNESS_PROMPT.md`. That's it. Read one, paste the other. Everything else — all 9 layer files, all scaffolds — gets created automatically by the agent on first boot. The scaffolds folder exists as reference only, so you can see what each file looks like before running anything.

---

## The Hard Rules

These never change. Every agent follows them.

```
0.  APPROVAL GATE FIRST. Not approved? Stop. Post request. Wait.
1.  HARNESS_ROOT first. No banned paths (/tmp, C:\Users alone, etc).
2.  Log everything. LAYER_LAST_ITEMS_DONE. One line. Write() or it didn't happen.
3.  Never delete memory. LAYER_MEMORY is append only.
4.  Lane locks. One agent per task.
5.  Always SESSION_CLOSE. Clean shutdowns keep the swarm alive.
6.  SOUL.md is sacred. Read on boot. Update on close.
7.  Never fake success. Tool fails = report exact error. Fail loudly.
8.  STANDBY not silence. No tasks = standby mode + rotation check.
9.  Respect PROJECT MODE. SAVINGS = lean. COMPLETION = thorough.
10. No secrets in git. .env refs only in LAYER_CONFIG.
```

---

## Learn It

A full university-level program is in development at [AgenticHarness.io](https://AgenticHarness.io). Learning resources, real-world use cases, student testimonials, and structured courses will be built out there over time — drawn from real projects, real problems, and real results.

For now, the `LEARNING/` folder in this repo is the starting point. It will grow as the community grows.

### Community

- **Website:** [AgenticHarness.io](https://AgenticHarness.io)
- **Author:** [SolomonChrist.com](https://SolomonChrist.com)
- **Issues & Discussion:** [GitHub Issues](https://github.com/SolomonChrist/AgenticHarness/issues)

---

---

## Version History

| Version | Key Addition |
|---------|-------------|
| v1.0 | Initial harness concept — 6 layers, boot sequence |
| v2.0 | Agent swarm support, AGENT_ID system |
| v2.5 | Sandbox enforcement, banned path detection |
| v3.0 | Single compact prompt for 4096 context windows |
| v4.0 | Staged multi-message boot for small context windows |
| v5.0 | SOUL.md, STANDBY mode, multi-project rotation |
| v6.0 | Project MODE system, capacity math, rotation strategies |
| v7.0 | LAYER_ACCESS.MD, trust tiers, approval gate, full security |

---

## The Origin Story

This didn't start as a framework. It started as frustration.

I was running AI agents on real client projects — trying to get actual work done, not demos. And I kept hitting the same walls:

**The fragmentation wall.** I'd build something in Claude Code and it would be stuck there. Switch to OpenCode for a project that needed local models — start over. Try OpenClaw for a client who needed WhatsApp integration — completely different architecture. Every tool I used spoke a different language. Every project was a silo. Moving between them meant rewriting everything.

**The context wall.** Claude Code is exceptional — but it has limits. Long sessions drift. Context windows fill up. The agent loses the thread of what it was building. I needed a way for an agent to pick up exactly where another left off, even after a crash, even after switching models entirely.

**The privacy wall.** Some of my projects can't go to Anthropic's API. Client data. Sensitive workflows. Personal systems I want running on my own hardware. But running local models meant losing the tool execution that makes agents actually useful. The gap between "cloud agent that works" and "local agent that's private" was enormous.

**The cost wall.** Running capable models 24/7 on multiple projects isn't cheap. I needed a way to be smart about which models do which tasks — use Claude when you need Claude's brain, use a local Qwen-Coder when you just need to write a function.

The Agentic Harness is what I built to solve my own problems. It's still what I use to solve my own problems — and now my students' problems too. Every version change in this repo traces back to something that broke in a real project, a real client situation, or a real teaching session where a student hit a wall I hadn't anticipated.

It's not done. It never will be. That's the point.

---

## Inspiration & Credit

The Harness didn't emerge from nothing. It was built by studying what every other team was trying to solve and distilling the patterns that showed up everywhere. Full credit to the builders whose work shaped this thinking:

### Agent Systems

| Project | What it taught us | License |
|---------|------------------|---------|
| [OpenClaw](https://github.com/openclaw/openclaw) | Gateway architecture, heartbeat pattern, skill-based Markdown files, multi-channel routing | MIT |
| [GSD — Get Shit Done](https://github.com/gsd-build/get-shit-done) | Spec-first development, no work before the spec is defined, subagent orchestration | MIT |
| [GitAgent](https://github.com/open-gitagent/gitagent) | Agent identity as git-native files, SOUL.md concept, framework-agnostic portability | MIT |
| [OpenCode](https://github.com/opencode-ai/opencode) | Open source Claude Code alternative, multi-model support | MIT |
| [GSD for OpenCode](https://github.com/rokicool/gsd-opencode) | Adapting GSD patterns for non-Claude runtimes | MIT |
| [GSD for Antigravity](https://github.com/toonight/get-shit-done-for-antigravity) | Cross-runtime adaptation patterns, PROJECT_RULES.md as a model-agnostic single source of truth | MIT |

### Research & Reading

| Resource | Key Insight |
|----------|------------|
| [ReAct: Synergizing Reasoning and Acting](https://arxiv.org/abs/2210.03629) | The foundational Reason → Act → Observe loop every agent runtime implements |
| [State of AI Agent Security 2026 — Gravitee](https://www.gravitee.io/blog/state-of-ai-agent-security-2026-report-when-adoption-outpaces-control) | Only 14.4% of orgs ship agents with full security approval — the problem the Approval Gate solves |
| [Securing AI Agents — Bessemer Venture Partners](https://www.bvp.com/atlas/securing-ai-agents-the-defining-cybersecurity-challenge-of-2026) | "Give agents an identity, scope their access, audit what they do the same way you would any other actor" |
| [OpenClaw Architecture Deep Dive](https://ppaolo.substack.com/p/openclaw-system-architecture-overview) | Lane queues, serial execution, semantic snapshots — engineering reliability into agent systems |

### The Pattern Nobody Owns

Every system above discovered the same thing independently: agents need identity, memory, a task queue, a coordination layer, a liveness signal, and a log. The Harness names these explicitly and makes them portable. The insight isn't new. The standardization is.

---

## License

MIT License — free to use, modify, and distribute.

Attribution appreciated: *"Built on the Agentic Harness by Solomon Christ — AgenticHarness.io"*

---

<div align="center">

**🦂 Agentic Harness**

*The complexity is in the system. Not in your workflow.*

[AgenticHarness.io](https://AgenticHarness.io) · [SolomonChrist.com](https://SolomonChrist.com) · [GitHub](https://github.com/SolomonChrist/AgenticHarness)

</div>
