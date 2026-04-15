# Agentic Harness Redesign Transfer

## Purpose

This document is the authoritative redesign spec and transfer prompt for rebuilding Agentic Harness from the ground up.

It is written to replace the current direction of:

- explicit inbox/outbox command-and-control framing
- UI-first orchestration
- terminal-chat-dependent always-on bots
- brittle per-harness behavior hidden behind one-off glue

The new design must be:

- simple
- bot-native
- markdown-native
- API-backed
- portable
- resilient
- understandable
- always-on where it matters

This document defines:

- the product vision
- the system boundaries
- the core abstractions
- the filesystem contract
- the provider model
- the bot model
- the MasterBot model
- the communication model
- the backup/restore model
- the phased implementation plan
- the transfer prompt for future implementation work

---

## Executive Summary

Agentic Harness is a fragmentation solver.

The human operator has:

- many projects
- many folders
- many agentic harnesses
- many bots
- many LLM providers
- many tools
- many long-running contexts

Without a unifying layer, everything fragments:

- work is scattered
- memory is scattered
- capabilities are scattered
- costs are scattered
- sessions are scattered
- no single bot knows what exists
- no single interface shows what is alive

Agentic Harness solves that by introducing:

- one Human Operator
- one always-on MasterBot
- any number of always-on worker bots
- one API as the system backbone
- markdown-native shared state
- portable bot definitions
- one control surface for the operator

The human talks to MasterBot.
MasterBot coordinates the bot ecosystem.
Worker bots do the specialized work.
The API observes, stores, synchronizes, and surfaces state.

This system should ultimately support the demonstration and operation of:

- full virtual departments
- persistent project teams
- human judgment over AI execution
- large-scale operations with lower administrative overhead

That aligns directly with the presentation framing:

**The Autonomous Enterprise: Scaling Operations Through AI Swarms and Human Judgment**

---

## Product Definition

Agentic Harness is an organization, management, and coordination system for multiple real agentic harness bots.

It is not itself the worker.

It is the combination of:

- a programmatic always-on MasterBot
- a markdown-native shared state model
- a registry of live bots
- a task and communication backbone
- a dashboard/API interface for the human operator
- a portable bot-definition system

The goal is to let a human operator run an entire ecosystem of bots the same way they would run a human executive team.

This should be strong enough to support:

- personal life operations
- digital second-brain operations
- content and marketing operations
- business operations
- research and analysis teams
- internal virtual departments

---

## Product Sentence

Agentic Harness is a markdown-native, API-backed operating layer that gives one human operator a single always-on MasterBot and a reusable ecosystem of live worker bots that can coordinate, deliberate, and execute work across all projects.

The simplest teaching version is:

- the bot is the files you own
- the engine is the current model or harness attached to that bot
- changing the engine does not change the bot

---

## Core Vision

### The Human Operator

The user is the Human Operator of the whole system.

The Human Operator:

- defines the MasterBot
- creates or integrates worker bots
- defines project areas
- gives high-level direction
- reviews important outcomes
- resolves blocked human-only steps
- controls backup, restore, and portability

The Human Operator should not need to think about:

- raw process wiring
- internal transport details
- one-off terminal commands
- where a given worker is currently running
- which bot is best for a task

The system should reduce fragmentation, not create more of it.

### MasterBot

MasterBot is the chief of staff.

MasterBot must be:

- always-on
- programmatic
- durable
- policy-aware
- memory-bearing
- operator-facing
- capable of coordinating worker bots
- capable of being the last-resort worker if nobody else can do the task

MasterBot is not a browser form.
MasterBot is not a fake registry entry.
MasterBot is a real persistent bot runtime with:

- an LLM provider
- a bot identity
- a soul
- memory
- policies
- a folder
- a heartbeat
- project awareness

MasterBot must preserve continuity even if the runtime engine changes.

That means the same MasterBot should survive:

- provider swaps
- harness swaps
- cost changes
- local fallback modes

without losing:

- identity
- soul
- memory
- policies
- project continuity

### Worker Bots

Worker bots are real bots running in real harnesses.

Examples:

- Claude Code
- OpenCode
- OpenClaw
- custom command-driven local bots
- later: LM Studio-backed local specialists
- later: provider-specific research or tool bots

Each worker bot has:

- its own folder
- its own bot definition
- its own skills
- its own strengths
- its own weaknesses
- its own harness/runtime
- its own tools
- its own model/provider settings

### Persistent Bot Organization

The system should be treated as a persistent bot organization.

That means:

- the Human Operator talks only to MasterBot
- MasterBot converts operator intent into structured work
- worker bots continuously inspect available work
- bots evaluate tasks based on their real capabilities
- bots claim, collaborate, hand off, and complete tasks
- when the full task list is done, MasterBot reports back

This is not a collection of unrelated automations.
It is an operating organization composed of durable specialized bots.

### Provider-independent bot identity

This is a foundational rule.

A bot is not:

- Claude
- OpenAI
- OpenRouter
- LM Studio
- OpenClaw
- Claude Code
- any single provider or harness

Those are only engines.

The real bot is:

- its identity
- its soul
- its memory
- its learned skills
- its policies
- its current project context
- its task history
- its artifacts
- its relationships to other bots and projects

So the real bot lives in the files the operator owns.

Changing the engine does not change the bot.

This means every bot must be able to survive:

- vendor bans
- model changes
- budget changes
- API migrations
- local or offline fallback scenarios

The operator must always remain in control of:

- the bots
- the memory
- the files
- the projects
- the orchestration logic
- the backup and restore
- the continuity

### Owned intelligence

This system should be teachable with a simple distinction:

- the model is the engine
- the bot is the owned system

Another way to say it:

- you are not renting a bot
- you are renting or attaching an engine
- the owned bot lives in your files

The bot is the chassis.
The current provider or harness is the engine currently attached to it.

### Agent Swarm Behavior

The system must support bots operating like a team.

That means:

- bots can inspect shared tasks
- bots can advertise their fit for tasks
- bots can claim tasks
- bots can hand off tasks
- bots can ask for help
- bots can collaborate on work
- bots can report completion to MasterBot

This swarm behavior must still be simple and legible.

---

## Design Principles

### 1. Bot-native, not harness-dominating

Agentic Harness must not make bots feel like they are being remotely controlled by a hidden command infrastructure.

Bots should experience the system as:

- project files
- notes
- tasks
- team communication
- policies
- status files

This is important both for simplicity and for compatibility with bot runtimes that object to explicit command-and-control framing.

### 2. Markdown-native state

The bot-facing truth should be markdown files and small JSON status files in normal folders.

The API should observe and synchronize that state.

The system should not rely on bots conceptually accepting:

- inbox queues
- hidden orchestration buses
- remote control framing

### 2a. Clean separation of bot files and project files

This is a non-negotiable design rule.

All bot-specific items live with the bot.
All project-specific items live with the project.

#### Bot-specific state

These belong in the bot's own infrastructure:

- soul
- identity
- role policies
- memory
- learnings
- skills
- harness/runtime profile
- model/provider profile
- heartbeat
- status
- local working notes for the bot itself

#### Project-specific state

These belong in the project's folder structure:

- task list
- kanban
- next action
- shared team communication
- artifacts
- research notes
- decisions
- humans involved
- project policies

This split keeps:

- bots portable
- projects durable
- roles clear
- backups understandable

### 2b. Keep it simple enough to teach

The entire system should be explainable to a novice in plain language.

The teaching model should be:

1. you create a MasterBot
2. you create or integrate worker bots
3. each bot has its own bot files
4. each project has its own project files
5. MasterBot coordinates the work
6. bots read and update files
7. you keep ownership even if you swap engines

Avoid extra abstraction unless it helps the operator act.

### 3. Programmatic Master, harness-native workers

MasterBot should be a true programmatic daemon/service.

Worker bots can continue to be harness-native:

- Claude Code
- OpenCode
- OpenClaw
- custom local harnesses

This separates:

- stable orchestration
- from interactive or provider-specific worker behavior

### 3a. Hot-swapping and degraded mode

The system must support graceful runtime substitution.

That means a bot can move between:

- strong cloud providers
- cheaper cloud providers
- local-first providers
- offline fallback engines

without losing identity.

This should support:

- hot-swapping provider
- hot-swapping harness
- degraded fallback mode
- stronger upgrade mode
- no loss of continuity across swaps

Degraded mode is a feature, not a failure.

If premium cloud access disappears, a bot should still remain available using a weaker local engine rather than disappearing entirely.

The quality may fall.
The bot should not vanish.

### 4. Filesystem as durable truth

The filesystem should be the durable state layer.

Bots and projects should be portable because their definitions live in files.

### 5. Backup the bot, not just the app

The durable asset is the bot definition plus its working memory and skills.

### 6. Operator simplicity above all

The operator should mostly do three things:

1. define MasterBot
2. integrate or create worker bots
3. talk to MasterBot

Everything else should be secondary.

---

## Non-Goals

Do not optimize first for:

- a flashy UI
- simulated city or world metaphors
- fragile multi-hop routing hierarchies
- hidden command buses presented to bots
- lots of providers at once
- lots of frontends at once
- full autonomy before observability

Do not begin by trying to solve:

- every harness in the market
- every provider
- full human-staff workflows
- enterprise access control

Build the smallest truthful system that can actually run.

---

## System Boundary

Agentic Harness consists of four layers.

### Layer 1. Human Operator Layer

The person uses:

- Dashboard
- API
- later Telegram

This layer must be simple and operator-first.

### Layer 2. Master Layer

A real always-on MasterBot service that:

- reads operator input
- maintains master memory
- updates markdown state
- reasons about tasks and available bots
- coordinates worker bots
- reports back to the human

### Layer 3. Worker Layer

Real worker bots with their own harness runtimes.

### Layer 4. Backbone Layer

The API and filesystem synchronization layer.

This layer:

- stores canonical state
- reads/writes markdown and JSON status
- backs up and restores bot definitions
- exposes live status to UI/API

---

## Why The Previous Approach Failed

The old direction exposed the harness to bots as:

- a command-and-control system
- explicit inbox/outbox queues
- remote task execution infrastructure

That caused at least one bot runtime to reject participation on policy grounds.

The redesign avoids that by making the bot-facing layer look like normal project collaboration:

- read project notes
- read current tasks
- read policies
- update status
- update team communication
- write artifacts

Another important lesson:

the bot should not need to "understand the harness" as a higher authority.

It should only need to understand:

- its own bot definition
- the project files
- the current work state
- the team communication files

The API and dashboard can understand the broader system.
The bot only needs to understand its immediate operating environment.

The API still exists, but the bot does not need to understand itself as participating in a hidden C2 system.

---

## Minimal Supported Harnesses

For the restart, support exactly four harness types:

- `claude-code`
- `opencode`
- `openclaw`
- `custom`

Behavior:

- Claude Code is the first fully working worker integration
- OpenCode is second
- OpenClaw is third
- Custom is a generic shell-command adapter

Do not add more harness types until these are stable.

---

## Provider Model

Separate harness type from model/provider.

### Master Provider

MasterBot should be provider-driven, not terminal-chat-driven.

Initial supported Master providers:

- `openai`
- `lmstudio`

Why:

- OpenAI gives the fastest stable path to a real always-on orchestration brain
- LM Studio gives a local/offline path

MasterBot should not depend on Claude Code as its permanent daemon runtime.
Claude Code is better positioned as a worker harness.

MasterBot should be designed so that the same bot identity can move between providers without being "reborn."

The preferred provider path should support:

- normal mode using a strong hosted provider
- degraded mode using a local fallback provider
- future hot-swaps without rewriting the bot

### Worker Provider

Worker bots may use:

- harness-default models
- explicit selected models
- custom model names

For Claude Code workers:

- support `haiku`
- `sonnet`
- `opus`
- `other`

For custom harnesses:

- allow full command input
- allow explicit model override if relevant

---

## Core Objects

### Human Operator

Fields:

- `operator_id`
- `display_name`
- `language`
- `preferences`

### MasterBot

Fields:

- `bot_id`
- `name`
- `role = master`
- `harness_type` or `provider_type`
- `model`
- `folder`
- `status`
- `heartbeat_at`
- `skills`
- `personality`
- `movement_style`
- `policy_level`
- `trusted_secrets_scope`

### Worker Bot

Fields:

- `bot_id`
- `name`
- `role`
- `harness_type`
- `model`
- `folder`
- `status`
- `heartbeat_at`
- `skills`
- `movement_style`
- `strengths`
- `weaknesses`
- `cost_profile`
- `speed_profile`
- `quality_profile`
- `tool_access`
- `preferred_projects`

Each worker bot must also maintain explicit self-knowledge about:

- what harness it runs on
- what model/provider it uses
- what tools it can access
- what skills it has developed over time
- what it is unusually good at
- what it is bad at
- what kinds of tasks it should avoid

Without this structured self-knowledge, task routing quality will degrade.

`movement_style` is part of bot identity so the same bot can be represented consistently in:

- future 3D environments
- dashboards
- visual swarms
- embodied visualizations

It should stay simple and identity-oriented.

### Project

Fields:

- `project_id`
- `title`
- `folder`
- `zone`
- `status`
- `owner_bot_id` optional
- `active_tasks`

### Task

Fields:

- `task_id`
- `title`
- `description`
- `project_id`
- `created_by`
- `priority`
- `status`
- `preferred_bot_id` optional
- `claimed_by_bot_id` optional
- `handoff_history`
- `artifacts`

---

## Filesystem Contract

The filesystem is the durable truth.

### Root structure

```text
AgenticHarness/
  MasterBot/
  Bots/
  Projects/
  System/
  Backups/
```

### MasterBot folder

```text
MasterBot/
  bot_definition/
    Soul.md
    Identity.md
    Memory.md
    Learnings.md
    Skills.md
    RolePolicies.md
    Status.md
    Heartbeat.md
    ProviderProfile.json
    RuntimeProfile.json
  workspace/
    TEAM_COMMUNICATION.md
    MASTER_TASKS.md
    MASTER_BOARD.md
    OPERATOR_NOTES.md
```

### Worker bot folder

```text
<WorkerBotFolder>/
  bot_definition/
    Soul.md
    Identity.md
    Memory.md
    Learnings.md
    Skills.md
    RolePolicies.md
    Status.md
    Heartbeat.md
    HarnessProfile.json
    RuntimeProfile.json
  workspace/
    WORKING_NOTES.md
    TASKS.md
    TEAM_COMMUNICATION.md
    ARTIFACTS.md
```

### Project folder

```text
Projects/
  <ProjectName>/
    KANBAN.md
    NEXT_ACTION.md
    NOTES.md
    ARTIFACTS.md
    DECISIONS.md
    TEAM_COMMUNICATION.md
    HUMANS.md
    PROJECT_POLICIES.md
    RESEARCH.md
    CONTEXT.md
```

### System folder

```text
System/
  GLOBAL_POLICIES.md
  LIVE_BOTS.md
  SYSTEM_STATUS.md
  ROUTING_RULES.md
```

---

## Bot-Facing File Contract

This is the central design change.

Bots should not be told:

- "pull from inbox"
- "reply through outbox"
- "participate in a hidden harness"

Bots should instead be told:

- read your `bot_definition` files
- read the relevant project files
- read the team communication file
- update your status and notes as you work
- record outputs in artifacts

The core startup instruction should always be conceptually simple:

- read your bot definition
- read the project context
- read team communication
- inspect current tasks
- update files as you work

That should be true for any harness.

The contract must remain simple enough that any harness can follow it.

### Minimum files a bot should read on startup

1. `bot_definition/Identity.md`
2. `bot_definition/Soul.md`
3. `bot_definition/RolePolicies.md`
4. `bot_definition/Status.md`
5. relevant `TEAM_COMMUNICATION.md`
6. relevant `NEXT_ACTION.md`
7. relevant `PROJECT_POLICIES.md`

### Minimum files a bot should write to

1. `bot_definition/Status.md`
2. `bot_definition/Heartbeat.md`
3. `workspace/WORKING_NOTES.md`
4. project `TEAM_COMMUNICATION.md`
5. project `ARTIFACTS.md`
6. project `KANBAN.md` if it owns the task

---

## Communication Model

### Operator to Master

The operator talks to MasterBot through:

- dashboard
- API
- later Telegram

MasterBot then updates markdown state.

### Master to Team

MasterBot writes proposals, requests, and decisions into:

- `MASTER_TASKS.md`
- project `TEAM_COMMUNICATION.md`
- project `NEXT_ACTION.md`

MasterBot should also maintain a high-level cross-project summary in:

- `MASTER_BOARD.md`

This allows the operator to understand the overall state of the organization quickly.

### Bot to Bot

Bots collaborate through:

- project `TEAM_COMMUNICATION.md`
- optionally bot-local `workspace/TASKS.md`

This file is append-only or append-mostly and should be human-readable.

### Bot to Master

Bots signal back by updating:

- `TEAM_COMMUNICATION.md`
- `ARTIFACTS.md`
- `KANBAN.md`
- `Status.md`

MasterBot and the API interpret these changes.

---

## Swarm Execution Model

The target system behavior is:

- the user discusses goals with MasterBot
- MasterBot turns those goals into projects and tasks
- all live bots inspect available work
- bots compare the work against their harness, model, tools, and skills
- the best-fit bot or bots take the work
- bots collaborate until all tasks are done
- MasterBot summarizes and reports back to the user

This must feel like a human executive team, not a static queue processor.

The end goal is not just "many bots."
The end goal is a set of virtual departments that can operate continuously with:

- clear scope
- specialized archetypes
- shared context
- human judgment at key review points

### What each bot should consider

Each bot should be able to evaluate tasks using:

- harness capability
- model capability
- tool access
- skill inventory
- domain strength
- speed expectation
- cost expectation
- quality expectation
- current availability
- current workload

### Task selection priorities

When a task appears, selection should follow this order:

1. explicit Human Operator preference
2. explicit MasterBot assignment
3. required tool compatibility
4. required skill compatibility
5. harness suitability
6. model suitability
7. current availability
8. expected quality
9. expected speed
10. expected cost

This ensures:

- human preference wins
- MasterBot can direct when necessary
- otherwise the swarm behaves rationally

### Claiming model

Bots should be able to:

- self-nominate
- claim work
- split work into stages
- request assistance
- hand work off
- collaborate on subtasks

All of this must remain legible in markdown state.

### Collaboration examples

#### Example: Website build

- MasterBot publishes a website task
- WebBot recognizes it has the best fit
- WebBot claims the task
- WebBot may break the work into subparts using its own harness-native strengths
- WebBot updates `TEAM_COMMUNICATION.md` and `KANBAN.md`
- when complete, WebBot records outputs in `ARTIFACTS.md`
- MasterBot notices completion and reports back

#### Example: Research plus writing handoff

- MasterBot publishes a market analysis task
- ResearchBot claims research collection
- ResearchBot discovers report writing is not its strength
- ResearchBot requests help in `TEAM_COMMUNICATION.md`
- WriterBot claims the writing stage
- ResearchBot records the handoff context
- WriterBot produces the final report and updates `ARTIFACTS.md`
- MasterBot reports completion to the operator

#### Example: Multi-bot accounting support

- MasterBot creates a task to gather information requested by an accountant
- Google-oriented bot retrieves email and document references
- MoneyBot supplies bank and transaction data
- DriveBot supplies mileage and vehicle information
- MasterBot checks whether all conditions are satisfied
- if not, MasterBot returns to the operator for missing human-only inputs
- once the missing information arrives, MasterBot coordinates final completion

This is the intended day-to-day operating pattern.

### Virtual department model

Bots should be groupable into virtual departments such as:

- Research
- Writing
- Operations
- Sales
- Social Media
- Finance
- Legal
- Second Brain
- Real Estate
- Investment
- Customer Support

Each department may contain:

- one lead bot
- one or more specialist bots
- a department communication file
- a department task backlog

MasterBot coordinates across departments, not just across single bots.

---

## Tasking Model

### Master creates or updates tasks

When the operator requests work, MasterBot:

1. determines relevant project(s)
2. updates `MASTER_TASKS.md`
3. writes a team request into the relevant `TEAM_COMMUNICATION.md`
4. may set or update `NEXT_ACTION.md`

MasterBot should be responsible for ensuring that the task list is complete enough for the swarm to act.

That means:

- splitting large goals into smaller tasks
- identifying missing context
- publishing the work in a way bots can evaluate
- revising tasks when new information arrives

### Claiming

Bots inspect tasks and team communication.

Claim preference order:

1. explicit human preference
2. explicit MasterBot assignment
3. best capability fit
4. best quality
5. best speed
6. best cost

Claiming should be visible in markdown:

- the bot appends a claim note to `TEAM_COMMUNICATION.md`
- the task is moved in `KANBAN.md`
- `NEXT_ACTION.md` is updated if appropriate

### Multi-bot completion rule

The system should assume many tasks are multi-stage, not single-owner forever.

A task may pass through:

- research
- analysis
- writing
- implementation
- review
- communication

Different bots may own different stages.

MasterBot is responsible for:

- tracking stage completion
- detecting blocked stages
- publishing follow-up tasks when needed
- deciding when the task is truly complete

### Collaboration and handoff

If a bot cannot finish alone:

- it posts a help request in `TEAM_COMMUNICATION.md`
- another bot can claim the next stage
- the first bot records handoff notes

This allows swarm behavior without hidden control semantics.

---

## Heartbeat and Liveness

Every bot needs liveness.

### Heartbeat model

Each bot has:

- `bot_definition/Heartbeat.md`
- `bot_definition/Status.md`

`Heartbeat.md` contains:

- bot id
- last updated timestamp
- current mode
- current task reference if any

`Status.md` contains:

- current human-readable status
- current project focus
- blockers
- last meaningful action

### Keepalive model

Some harnesses may benefit from periodic keepalive behavior, but this must be separate from the bot-facing conceptual model.

The system may run a helper process that:

- updates freshness
- ensures the runtime is available
- optionally reopens a known harness window or process

But the canonical bot-facing output is still markdown state.

### Scheduled wake-up model

The preferred 24x7 pattern is:

- a scheduler wakes the bot every 5 minutes
- the bot reads its bot definition and project files
- if no work exists, it updates heartbeat and exits
- if work exists, it claims or continues it
- if it is already working, the next scheduled wake sees the active lease and exits

This should work across:

- Windows Task Scheduler
- cron
- Linux timers or services
- n8n scheduled workflows

This is preferred over requiring a permanently open chat window.

Local-first scheduling matters for more than privacy.

It also provides:

- latency sovereignty
- resilience during cloud outages
- continuity when API credits run dry
- continuity during vendor disruptions

---

## Always-On MasterBot

MasterBot must be a true daemon, not an open chat window.

### MasterBot responsibilities

- maintain operator conversation context
- maintain global memory
- watch project and bot markdown files
- detect live bots
- interpret team communication
- create and route tasks
- notify the operator
- track completion and blockers
- protect secrets and high-value memory

### MasterBot runtime architecture

MasterBot should run as a Python daemon/service with:

- provider adapter
- filesystem watcher
- scheduler
- markdown parser/writer
- API client/server integration

### Initial provider support

- `openai`
- `lmstudio`

### Why programmatic MasterBot

A terminal UI harness is too brittle for:

- 24x7 operation
- persistence
- recovery
- proactive scheduling
- file watching
- notifications

MasterBot should be built like an actual service.

It must preserve continuity across provider swaps.

MasterBot should also support fallback execution when cloud access is unavailable.

That fallback may be weaker, but it should allow the organization to remain online.

---

## Worker Integration Model

### Claude Code

Claude Code is the first worker harness to fully support.

The goal is not to make Claude Code think it is under a remote controller.

The goal is to make it operate in a folder containing:

- project notes
- bot definition
- current next actions
- status files

Claude should be prompted as:

- a collaborator working from local project files
- not a bot pulling from a hidden central queue

### OpenCode

Same folder contract.
Same bot_definition model.
Same markdown communication model.

### OpenClaw

Same folder contract.
Same markdown communication model.

### Custom

Custom bots are any folder plus command.

The system writes the same file contract there and launches the custom command if configured.

---

## Backup and Restore

### What is durable

The durable units are:

- every `bot_definition/` folder
- project markdown files
- MasterBot markdown files
- system markdown and settings files

### Backup rule

When the user clicks backup, back up:

- `MasterBot/bot_definition/`
- every worker `bot_definition/`
- `Projects/*/*.md`
- `System/*.md`
- provider/runtime profile JSON files

### Restore rule

Restore should be GUI-guided.

The user maps:

- bot name -> target folder
- project name -> target folder
- MasterBot -> target Master folder

This makes bots:

- portable
- reusable
- transferable
- potentially saleable

---

## Security and Secret Handling

MasterBot is the strictest holder of sensitive coordination state.

Secrets should not be spread casually across worker bots.

MasterBot may maintain:

- credential references
- human contact references
- sensitive policy notes

But actual secrets should ideally be:

- referenced from a secrets store
- or injected securely

Do not encode raw secrets casually into markdown files.

---

## Dashboard Design

The dashboard should be extremely simple.

### Main operator view

Only show:

1. `Talk to Master`
2. `Conversation`
3. `Live Bots`
4. `Current Projects`
5. `Alerts / Waiting / Blocked`

### Secondary views

Only if needed:

- `Bot Setup`
- `Bot Editor`
- `Backup / Restore`
- `System Status`

### Bot card behavior

Clicking a bot should show:

- current status
- folder path
- harness type
- model
- strengths
- current task
- last heartbeat
- edit definition
- open folder
- start runtime if supported

### Bot editing

The operator should be able to directly edit:

- `Soul.md`
- `Identity.md`
- `RolePolicies.md`
- `Memory.md`
- `Skills.md`
- runtime/provider settings

---

## API Role

The API is the backbone, not the bot-facing controller.

The API should:

- index filesystem state
- expose bot status
- expose projects and tasks
- accept operator messages
- let MasterBot and UI write structured updates
- manage backup and restore
- manage process launch where appropriate

The API should not be the thing the bot conceptually reports obedience to.

---

## Recommended MVP

Do not rebuild everything at once.

### MVP Goal

Get one truthful system working:

- one programmatic MasterBot
- one worker bot integration
- markdown-native state
- basic tasking
- basic backup

### MVP stack

- MasterBot provider: `openai`
- optional local provider: `lmstudio`
- worker harness: `claude-code`
- filesystem state: markdown + small JSON metadata
- dashboard: simple

### MVP behaviors

1. user talks to Master
2. Master updates `MASTER_TASKS.md`
3. Master writes request into project `TEAM_COMMUNICATION.md`
4. live bots inspect the task and determine fit
5. the best-fit Claude worker claims the task
6. Claude worker reads relevant files and works
7. Claude worker updates `TEAM_COMMUNICATION.md`, `ARTIFACTS.md`, `Status.md`
8. if needed, Claude worker requests assistance or hands off
9. Master notices progress and reports back

If this works cleanly, expand.

The MVP should still preserve the long-term direction:

- one operator
- one MasterBot
- multiple worker bots
- markdown-native collaboration
- future virtual departments

---

## Phased Build Plan

## Phase 0. Redesign freeze

Stop patching the old generator.

Deliverables:

- this redesign doc
- clear architectural scope
- no more incremental glue on the old C2 design

## Phase 1. Filesystem schema

Build only:

- folder structure
- `bot_definition/` schema
- project markdown schema
- system markdown schema

Deliverables:

- canonical file templates
- parser/writer helpers
- backupable layout
- clear split between bot-owned state and project-owned state

## Phase 2. Programmatic MasterBot

Build MasterBot daemon with:

- OpenAI provider adapter
- LM Studio provider adapter
- memory loading
- markdown reading/writing
- heartbeat
- operator message handling

Deliverables:

- always-on MasterBot service
- `Heartbeat.md`
- `Status.md`
- live dashboard presence
- project and team markdown interpretation

## Phase 3. Simple dashboard

Build only:

- talk to Master
- conversation feed
- live bots list
- project list
- alert status
- bot editor

No complexity beyond that.

## Phase 4. Claude worker integration

Build first real worker adapter using markdown-native collaboration.

Deliverables:

- initialize Claude worker folder
- Claude-specific launch helper
- Claude reads local bot/project files
- updates markdown outputs

## Phase 5. Swarm coordination

Add:

- task claiming rules
- team communication parsing
- handoff rules
- basic scoring for fit, speed, cost, quality
- department-level grouping
- multi-bot deliberation through markdown communication
- cross-project status summarization for MasterBot

## Phase 6. Backup and restore

Add:

- full bot_definition backup
- GUI restore mapping
- portable bundle export

## Phase 7. Additional worker harnesses

Add in order:

1. OpenCode
2. OpenClaw
3. Custom harness

---

## Scoring Model For Task Assignment

Each candidate bot can be scored on:

- human preference
- master preference
- skill fit
- tool fit
- harness capability
- model capability
- expected speed
- expected cost
- current availability

Simple weighting:

- explicit human preference: absolute override
- explicit Master assignment: very high weight
- skill fit: high
- tool fit: high
- quality fit: medium-high
- speed fit: medium
- cost fit: medium
- availability: required

MasterBot should use this model, but bots can also self-nominate in `TEAM_COMMUNICATION.md`.

This scoring model should be visible and editable, not hidden in code only.

Store the baseline routing rules in:

- `System/ROUTING_RULES.md`

and the computed live bot summary in:

- `System/LIVE_BOTS.md`

---

## Example Workflow

### Scenario: tax support request

1. User tells MasterBot:
   - get me the report my accountant asked for

2. MasterBot:
   - creates a task in `MASTER_TASKS.md`
   - writes request to relevant project `TEAM_COMMUNICATION.md`
   - updates `NEXT_ACTION.md`

3. A Google-oriented bot inspects the request and takes the email/data retrieval stage.

4. It writes findings and limitations into `TEAM_COMMUNICATION.md`.

5. MoneyBot sees the remaining bank-data gap and claims the next stage.

6. It writes back completed bank data notes.

7. DriveBot sees mileage is still needed and supplies that.

8. MasterBot notices QuickBooks access is still blocked and returns to the operator.

9. Operator supplies the missing human-only info.

10. MasterBot updates the records and asks EmailBot to prepare a draft.

11. EmailBot updates `ARTIFACTS.md` and `TEAM_COMMUNICATION.md`.

12. MasterBot tells the user the draft is ready.

This is the target behavior.

---

## What Success Looks Like

The system is successful when:

- the operator talks only to MasterBot
- MasterBot is truly always-on
- worker bots are truly portable
- bots can collaborate through normal project files
- the API is invisible as a controller but powerful as a backbone
- backups are bot-definition centric
- adding a new bot is simple
- the system is understandable after one session
- it can credibly demonstrate "virtual departments" in a live talk or demo

It should also be strong enough to support the broader ecosystem vision behind:

- `The Agentic Operator`
- `SolomonChrist.com`
- `AgenticHarness.io`
- Skool delivery and training tiers

The product and the teaching system should reinforce each other.

---

## Positioning Notes

The system should be positioned as:

- operator-owned
- API-first
- markdown-native
- provider-flexible
- open-source
- local-first compatible
- suitable for virtual departments and swarms
- provider-independent
- platform-independent
- capable of degraded local fallback
- suitable for strong visualizations

It should not be positioned as:

- a subscription loophole wrapper
- a browser hack
- a hidden control framework for trapped chat sessions

The long-term comparison point is closer to:

- a living collaborative workspace with evolving memory and multi-format outputs

But Agentic Harness goes further by emphasizing:

- open-source ownership
- portable bots
- bot-to-bot teamwork
- MasterBot-centered command
- filesystem-native durability
- owned intelligence
- engine-swapping without identity loss
- local-first resilience
- latency sovereignty

This is the right strategic lane for the post-ban, cost-conscious, operator-owned era.

### Messaging language

The external messaging should stay simple:

- Your Bots
- Your Files
- Your Projects
- Your Continuity
- Your Choice of Engines

This is the clearest way to explain the value.

---

## Multi-Builder Protocol

The system must be buildable by multiple implementation systems without losing coherence.

Primary builders:

- Codex
- Google Antigravity

Both builders must treat this document as the architectural source of truth.

### Shared build rules

Any builder working on Agentic Harness must:

1. read this redesign document first
2. preserve the markdown-native operator-owned design
3. avoid reintroducing bot-facing command-and-control framing
4. preserve the bot-vs-project file split
5. keep the system simple enough to teach to a novice
6. update the spec first if architecture changes

### Required handoff discipline

Every implementation session should leave behind:

- what changed
- why it changed
- what assumptions were made
- what remains incomplete
- what files are now source of truth

### Required shared handoff files

The rebuild should maintain:

- `AGENTIC_HARNESS_RESTART_TRANSFER.md`
- `BUILD_STATUS.md`
- `NEXT_STEPS.md`
- `OPEN_QUESTIONS.md`

These should stay concise and current so either builder can continue immediately.

### Builder transfer prompt

Use this with Codex or Antigravity:

> Read `AGENTIC_HARNESS_RESTART_TRANSFER.md` first and treat it as the architectural source of truth. Preserve the markdown-native bot/project model, provider-independent bot identity, scheduled wake-up heartbeat model, and programmatic MasterBot design. If you need to change the architecture, update the spec first. Keep the system simple, operator-owned, portable, and teachable.

---

## Implementation Guardrails

Never regress into:

- fake “online” states with no real runtime
- brittle one-shot terminal sessions pretending to be 24x7
- bot-facing hidden queue language
- a form-heavy dashboard that makes the operator act like a sysadmin
- too many harnesses before one works end to end

Always prefer:

- markdown-native collaboration
- explicit durable files
- small number of trustworthy abstractions
- real liveness
- visible status
- portable bots

---

## Transfer Prompt

Use this prompt to start the rebuild:

> Rebuild Agentic Harness from scratch according to the redesign spec in `AGENTIC_HARNESS_RESTART_TRANSFER.md`.
>
> The system must be a markdown-native, API-backed operating layer for one Human Operator, one always-on programmatic MasterBot, and many always-on worker bots.
>
> The MasterBot is the chief of staff and the operator-facing brain. Worker bots are real harness-native runtimes. The API is the backbone, not the bot-facing controller.
>
> Build the filesystem schema first, then the programmatic MasterBot, then the simple dashboard, then one real Claude Code worker integration, then swarm coordination, then backup/restore, then other harnesses.
>
> Do not use explicit inbox/outbox command-and-control framing in bot-facing files. Bots should collaborate through normal markdown project files such as `TEAM_COMMUNICATION.md`, `KANBAN.md`, `NEXT_ACTION.md`, `ARTIFACTS.md`, and bot-local definition files under `bot_definition/`.
>
> Start with only these harness types: `claude-code`, `opencode`, `openclaw`, and `custom`.
>
> Start with only these Master providers: `openai` and `lmstudio`.
>
> Optimize for a truthful, simple, always-on system that actually works rather than a broad or flashy one.

---

## Final Recommendation

Start over cleanly.

Do not continue patching the current explicit bridge model.

Build:

1. a programmatic MasterBot
2. markdown-native shared state
3. a simple operator dashboard
4. one true Claude worker
5. then swarm behavior

That is the cleanest path to the vision.
