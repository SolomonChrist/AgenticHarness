# Agentic Harness Final Application Design

## Purpose

Agentic Harness is a local-first coordination system for running a mixed team of AI agents, tools, daemons, and humans from one portable workspace.

The final product is not a single model runtime. It is a file-first operating layer that lets any compatible harness join, claim a role, coordinate through markdown, and later be handed to a daemon when that harness has a reliable CLI path.

The result should feel like a small personal operating company:

- the operator talks to `Chief_of_Staff`
- `Chief_of_Staff` coordinates the work
- specialist roles join when needed
- Runner keeps CLI-capable roles alive through timer and event wakeups
- Telegram provides remote human chat
- Visualizer shows the whole workzone

## Product Principles

- Files are the system.
- The operator is always in command.
- Manual first, daemon after proof.
- CLI-capable harnesses are the primary automation path.
- Manual-call harnesses are supported, but not pretended to be daemon-safe.
- Every role can be swapped to another provider when credits, limits, or capability needs change.
- The system should minimize expensive context by using short fresh cycles and only the files needed for the role.
- Infrastructure services are not swarm roles.

## Core Surfaces

### Markdown Control Plane

The markdown files are the shared state that every participant can read and update:

- `AGENTIC_HARNESS.md`: full protocol
- `AGENTIC_HARNESS_TINY.md`: low-context startup protocol
- `ROLES.md`: roles that can be claimed
- `LAYER_CONFIG.md`: current role registry
- `LAYER_TASK_LIST.md`: top-level task board
- `LAYER_SHARED_TEAM_CONTEXT.md`: shared whiteboard
- `LAYER_LAST_ITEMS_DONE.md`: event log
- `_heartbeat/`: role leases
- `_messages/`: role and human inboxes
- `MEMORY/`: long-term human and agent memory
- `Projects/`: project-specific task, context, and artifact folders

### Infrastructure Services

These are daemons, not swarm roles:

- `Runner`: scheduler, wake router, daemon owner for CLI-capable roles
- `TelegramBot`: remote chat bridge between operator and `Chief_of_Staff`
- `Visualizer`: live dashboard and 3D view of roles, daemons, tasks, projects, and recent events

They start through:

```powershell
py service_manager.py start all
```

or:

```powershell
start_all_services.bat
```

## Final First-Run Flow

1. User downloads or copies a fresh Agentic Harness folder.
2. User opens one trusted harness manually.
3. User pastes the regular startup prompt:

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Run normal first-run onboarding: ask my name, create my human memory, set up Runner, and offer Telegram/Visualizer before specialist roles.
```

4. `Chief_of_Staff` claims the role.
5. `Chief_of_Staff` onboards the operator and creates human memory.
6. `Chief_of_Staff` configures Telegram and Visualizer when accepted.
7. User proves the `Chief_of_Staff` role works manually.
8. User daemonizes `Chief_of_Staff`.

Example daemon handoff commands:

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider ollama --model llama3.1 --start-runner
```

After this, the original desktop harness window can be closed. Runner owns fresh CLI cycles for `Chief_of_Staff`.

## Role Lifecycle

### 1. Manual Claim

Every role starts manually once.

The operator opens the chosen harness and gives it the standard role prompt:

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Claim the <ROLE> role if it is available or stale.
```

The role must prove it can:

- create or renew `_heartbeat/<ROLE>.md`
- update `LAYER_CONFIG.md`
- write a join note to `LAYER_SHARED_TEAM_CONTEXT.md`
- log a claim event in `LAYER_LAST_ITEMS_DONE.md`
- read task and message files correctly

### 2. Daemon Handoff

After a role is proven once, the operator runs:

```powershell
py configure_role_daemon.py --role <ROLE> --provider <provider> --model <model> --start-runner
```

Supported daemon providers:

- `claude`
- `opencode`
- `goose`
- `ollama`
- `custom`

Examples:

```powershell
py configure_role_daemon.py --role Researcher --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role QA --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Documentation --provider ollama --model llama3.1 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider custom --name my-cli --command-template "cliname [FLAGS] \"{PROMPT}\" [ARGS]" --model my-model --start-runner
```

### 3. Background Operation

Runner then wakes the role when:

- a timer interval is due
- Telegram sends an operator message
- another role writes a wake request
- a task changes
- a lease goes stale or missing

Each daemon-owned role runs as a short fresh-context CLI cycle, writes results back to files, and exits. This keeps context and credit usage low.

## Manual-Call Harnesses

Some harnesses are valuable but not daemon-safe yet. Antigravity is the main example.

Manual-call role behavior:

- the role can claim a lease
- the role can read and write the same markdown files
- the operator keeps the harness window open
- the operator periodically sends a short update/check prompt
- Runner and the rest of the swarm still see its file updates
- Runner must not pretend it can auto-launch that role unless a proven CLI path exists

Manual-call harnesses are second-class only in automation, not in capability. They remain useful for specialist work such as engineering, UI work, or provider-specific tools.

## Telegram Behavior

Telegram is a human chat surface for `Chief_of_Staff`.

The operator should be able to speak normally:

- "hello"
- "what is the status?"
- "start the researcher"
- "remind me in 2 minutes to eat"
- "wake the engineer"

Telegram must:

- receive only messages from allowed user IDs
- route normal messages to `_messages/Chief_of_Staff.md`
- write wake requests to `Runner/_wake_requests.md`
- forward only clean operator-facing replies
- hide timestamps, raw logs, and internal chatter
- support deterministic reminders without relying on the LLM to remember later

Reminder flow:

1. Telegram detects a phrase like "remind me in 2 minutes to eat".
2. Telegram queues the reminder in `Runner/_reminders.json`.
3. Runner checks reminders every cycle.
4. Runner writes the due reminder to `_messages/human_<HumanID>.md`.
5. Telegram forwards the clean reminder back to the operator.

## Runner Behavior

Runner is the only scheduler and wake router.

Runner responsibilities:

- poll wake requests quickly
- launch daemon-owned CLI roles
- avoid launching manual roles
- avoid treating its own message writes as external wake events
- avoid passing display model labels as provider CLI model IDs
- suppress true launch failures without blocking normal short-lived CLI cycles
- process deterministic reminders
- write daemon runtime state for Visualizer

Runner should prefer correctness and cost safety over aggressive automation.

## Visualizer Behavior

Visualizer is the operator's live map of the workzone.

It should show:

- roles
- role status
- harness ownership
- daemon ownership vs manual-call mode
- current project count
- task counts
- recent events
- Runner status
- Telegram status
- Visualizer status
- wake queue count
- reminder queue state

3D world semantics:

- active working bots: orange
- active idle bots: blue
- stale or blocked bots: red
- unclaimed or manual idle roles: gray
- active tasks appear as bubbles above workers

## Provider And Model Swapping

The application must let the user swap providers when credits, limits, or capability needs change.

Examples:

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider ollama --model llama3.1 --start-runner
```

The same role can be reconfigured to a new provider without changing the control plane.

Any prompt-based CLI can become a daemon provider if its command template includes `{PROMPT}` or `{PROMPT_FILE}`.

Provider-native model handling:

- Claude gets real `claude-*` CLI model IDs only
- OpenCode gets OpenCode-supported model names
- Ollama gets locally installed model names
- blank model means use provider default

## Backup And Portability

To back up a live workspace, preserve:

- markdown control plane files
- `_heartbeat/`
- `_messages/`
- `MEMORY/`
- `Projects/`
- `Runner/ROLE_LAUNCH_REGISTRY.md`
- service config files

Before shipping a clean copy, run:

```powershell
py reset_to_fresh_state.py
```

The shipped folder must look like a first download, not a used workspace.

## Definition Of Done

The final application is production-ready when:

- `Chief_of_Staff` can be manually claimed
- operator onboarding works
- Telegram can chat with `Chief_of_Staff`
- `configure_role_daemon.py` can daemonize `Chief_of_Staff`
- Runner can wake `Chief_of_Staff` from Telegram and timer events
- reminders work deterministically
- specialist roles can be manually claimed
- CLI-capable specialist roles can be daemonized
- manual-call roles remain documented and safe
- Visualizer displays the ecosystem
- reset returns the repo to first-run state

This is the final application shape.
