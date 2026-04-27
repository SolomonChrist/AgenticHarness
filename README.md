# Agentic Harness

Markdown-first infrastructure for multi-agent swarms.

Agentic Harness is a meta harness: a portable coordination layer that lets many different harnesses, bots, workers, and humans operate inside the same system through a shared set of files.

This project is built around one core belief:

**the files are the system**

That means the orchestration layer stays:

- local-first
- portable
- inspectable
- backup-friendly
- provider-agnostic
- resilient to restarts and harness swaps

Website: [AgenticHarness.io](https://agenticharness.io)  
Vision / OPC framing: [SolomonChrist.com](https://solomonchrist.com)

## Maintainer Fresh-State Reset

When you update this repo, test changes locally, or prepare a new handoff, return the folder to first-run state before shipping it:

```powershell
py reset_to_fresh_state.py
```

That reset is intended to make the workspace look like a fresh download by removing transient runtime state, clearing live coordination surfaces, and restoring the core bootstrap markdown files plus Runner templates to their clean defaults.

## What Agentic Harness Is

Agentic Harness is not a single vendor runtime.

It is not locked to one model, one tool, or one company.

It is a shared protocol for coordination.

If a system can read and write markdown files, it can participate.

That means you can mix:

- Claude Code
- OpenClaw
- Antigravity
- local custom harnesses
- simple utility agents
- human operators

inside one working swarm.

## The Current Direction

The current direction intentionally simplifies the system.

Older versions explored larger runtimes, dashboards, and more embedded behavior. The current design pulls the center of gravity back to the control plane itself:

- one entry file
- a handful of core markdown files
- role-based coordination
- lease-based worker ownership
- long-term markdown memory per role and per human
- human checkout flow
- one optional runner/daemon for liveness
- optional transport and visualization layers outside the core

The goal is not to make the system more complicated.

The goal is to make it durable, understandable, and easy to carry into any project.

## The Vision

The broader vision behind Agentic Harness is the same one reflected on AgenticHarness.io:

- one person can coordinate a virtual team
- specialized agents can operate like departments or staff roles
- the operator stays in command
- different tools can join the same system
- work continues across sessions, restarts, and role handoffs

In practice, this can look like:

- one `Chief_of_Staff` / MasterBot
- one Researcher
- one Engineer
- one Documentation worker
- one QA worker
- one human operator

Or a smaller swarm.

Or a much larger one.

The point is not agent count.

The point is that all workers share one control plane and can continue the same work without being trapped inside one harness product.

## The Core Idea

Every harness starts by reading:

- `AGENTIC_HARNESS.md`

If a harness has a very small context window, it may start with:

- `AGENTIC_HARNESS_SMALL_CONTEXT.md`

If that is still too large, use:

- `AGENTIC_HARNESS_TINY.md`

If Claude Code credits are limited, use:

- `CLAUDE_LOW_SPEND_START.md`

That file keeps Claude focused on initial `Chief_of_Staff` setup and avoids auto-spawning Claude worker roles.

That file tells the harness:

- what this system is
- which files matter
- how roles are claimed
- how leases work
- how messaging works
- how projects are structured
- how humans are handled
- how the swarm should continue work

From there, all workers speak the same file protocol.

## How It Works

1. Point any compatible harness at a project folder containing the core files.
2. It reads `AGENTIC_HARNESS.md`.
3. It reads `ROLES.md` and checks `_heartbeat/` for live or stale roles.
4. It claims an open or stale role.
5. It reads the task list, shared context, memory, and recent events.
6. It begins working.
7. It writes its progress back into the same markdown system.

The active `Chief_of_Staff` / MasterBot is the main orchestrator.

That role is responsible for:

- talking to the operator
- managing top-level orchestration
- recommending which roles are needed
- routing work
- covering missing specialist roles when necessary

## Fresh Install Flow

On a fresh install:

- only `Chief_of_Staff` exists by default
- the first harness claims `Chief_of_Staff`
- on the first run, `Chief_of_Staff` should onboard the operator and build the initial operator memory
- it should write or update `HUMANS.md`, `MEMORY/humans/<HumanID>/`, and its own `MEMORY/agents/Chief_of_Staff/ALWAYS.md`
- if `Runner/` is present, `Chief_of_Staff` should perform the first-pass Runner setup during onboarding
- after Telegram/Visualizer setup, `Chief_of_Staff` must daemonize itself with `configure_role_daemon.py` or tell the operator the exact command
- `py service_manager.py start runner` starts the scheduler only; it does not daemonize `Chief_of_Staff`
- only after `py production_check.py` passes is it safe to close the original desktop harness window
- optional add-ons like `TelegramBot/` and `Visualizer/` should be introduced only when the operator asks for them
- when an add-on like Telegram is explicitly configured, `Chief_of_Staff` should try to start it or immediately provide the exact command to start it
- after onboarding is complete, it asks the operator what they want to do
- it recommends any additional roles needed

Recommended role bring-up policy:

- CLI harnesses are the primary automation path
- manual-call systems are valid, but secondary
- each specialist role should be launched manually once on the chosen harness first
- only after that proof should Runner own that role on cron/interval wakeups
- Claude Code is the easiest bootstrap and deep-work harness. The always-on Chief front door should stay cheap and file-first, for example with n8n or a custom CLI that only reads and writes markdown and routes work.
- after setup, recurring role work should run through `py Runner\scheduled_role_runner.py --role <ROLE>` or the built-in Runner daemon using the same preflight checks
- the preflight reads leases, tasks, role messages, operator intake, wake requests, provider cooldowns, and Daily All Hands state before any model call
- adding a `TODO` or `IN_PROGRESS` task with `Owner Role: <ROLE>` to `LAYER_TASK_LIST.md` or `Projects/<Project>/TASKS.md` is enough for the next scheduled check to find manually added work
- if a harness does not have a reliable CLI cycle path yet, register it as manual and document the human steps
- `Runner/`, `TelegramBot/`, and `Visualizer/` are infrastructure services, not swarm roles

Final daemon handoff pattern:

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider ollama --model llama3.1 --start-runner
```

Custom CLI handoff pattern:

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider custom --name my-cli --command-template "cliname [FLAGS] \"{PROMPT}\" [ARGS]" --model my-model --start-runner
```

Use the same pattern for `Researcher`, `Engineer`, `QA`, `Documentation`, or any other CLI-capable role after that role has completed one successful manual claim.

One-shot scheduled checks:

```powershell
py Runner\scheduled_role_runner.py --role Chief_of_Staff
py Runner\scheduled_role_runner.py --role Engineer --dry-run
py Runner\daily_all_hands.py
py role_jobs.py status
py role_jobs.py dashboard
py role_jobs.py dashboard --watch 2
py service_manager.py status all
```

`Daily All Hands` is enabled by default every 24 hours. It lets quota-paused or idle roles re-check their situation and report/recover without making the operator manually wake every bot. When Runner detects provider login, quota, rate-limit, or credit failure, it pauses that provider path and creates a Chief-owned task asking for replacement harness setup or quota recovery.

`role_jobs.py dashboard` is the CLI dashboard code. It is the fast color view for roles, leases, harnesses, work, and on/off state. Use `py role_jobs.py dashboard --watch 2` when you want a live refresh loop.

Recommended infrastructure launcher on Windows:

```powershell
start_all_services.bat
```

Fast Chief chat setup:

```powershell
py ChiefChat\setup_chief_chat.py
py service_manager.py start core
py service_manager.py status all
```

`ChiefChat` is the always-on, low-cost conversation layer for Telegram, Visualizer, console chat, and future transports. It reads and writes `_messages/CHAT.md`, uses `MEMORY/agents/Chief_of_Staff/SOUL.md` for voice, and calls the configured cheap model path in `ChiefChat/CHIEF_CHAT_CONFIG.md`. Claude Code/OpenCode remain the recommended first-run and deep-work harnesses; ordinary Telegram chat should not spend Claude Code quota.

This keeps the system lightweight and avoids preloading unnecessary structure.

## Telegram Chat Mode

Telegram is meant to feel like a normal chat with the active `Chief_of_Staff`.

When a message arrives from Telegram, the bridge writes it into `_messages/CHAT.md` and the legacy `_messages/Chief_of_Staff.md` compatibility inbox, then triggers `ChiefChat`. ChiefChat writes the reply to the canonical chat ledger and the legacy `_messages/human_<HumanID>.md` outbox so older harnesses and transports still work.

Telegram should only send clean operator-facing replies and major milestones. It should not forward timestamps, internal role logs, event stream lines, or raw swarm chatter.

Production chat defaults are intentionally responsive: `POLL_INTERVAL_SECONDS=2`, `TELEGRAM_ACK_AFTER_SECONDS=0`, `TELEGRAM_TYPING_INTERVAL_SECONDS=4`, `TELEGRAM_REPLY_WAIT_SECONDS=20`, and `TELEGRAM_WAIT_FOR_REPLY_ON_MESSAGE=YES`. That means Telegram should show a typing indicator immediately while ChiefChat works, then forward the final Chief reply when it writes the ledger/outbox.

If Telegram is active but `ChiefChat` is not running, Telegram should say so clearly and provide `py service_manager.py start chief-chat` instead of pretending the background responder is ready.

If Telegram is active but Runner itself is not alive, Telegram should say so clearly and provide `py service_manager.py start runner`. A bridge-only acknowledgement is not considered a working Chief chat.

When replying through markdown, existing `_messages/human_<HumanID>.md` files must be appended or updated. Do not use a create-only `Write(...)` operation on an existing outbox file.

Safe helper commands are available:

```powershell
py send_human_reply.py "Hello Solomon, I am online."
py wake_role.py --role Chief_of_Staff --reason telegram_message
```

## Research And Web Questions

`Chief_of_Staff` is expected to answer normal operator questions, including questions that require web or Google-style research.

- ChiefChat uses a source-first path for ordinary web/current-info questions: create a durable `TASK-WEB-*` task, gather readable source evidence with Playwright when enabled, then answer from that evidence.
- Weather requests use a direct Open-Meteo lookup so the operator receives actual current conditions instead of a progress-only "checking now" reply.
- If browser extraction or the cheap model fails, ChiefChat should still send the best extracted evidence and leave the task open for a web-capable role.
- Harness records should note whether a provider is online, web/search-capable, browser/tool-capable, local-only, or manual-only.
- Data organization and life-operations projects are expected first-use cases; `Chief_of_Staff` may recommend roles like `Researcher`, `Data Organizer`, `Documentation`, `Operations`, or `Engineer`.

## Existing Project Adoption

Agentic Harness can also be placed around an existing project.

Recommended flow:

1. Create a fresh Agentic Harness root.
2. Put the existing project inside `Projects/<project-slug>/`.
3. Start a `Chief_of_Staff` harness.
4. Let it inspect the adopted project.
5. Let it recommend the roles required.
6. Add only the roles you actually need.

This makes the harness a coordination layer around real work instead of forcing everything into a proprietary runtime.

## The Core Files

These files are the control plane.

### `AGENTIC_HARNESS.md`

The entry file.

Every harness reads this first.

It defines:

- the operating model
- boot order
- lease and takeover rules
- messaging conventions
- project structure
- human checkout behavior

### `AGENTIC_HARNESS_SMALL_CONTEXT.md`

A compact bootstrap entry for low-context harnesses.

Use it when a model cannot reliably ingest the full main spec.

It contains:

- minimum role-claim rules
- minimum lease rules
- minimum file read order
- messaging basics
- small-context join behavior

### `AGENTIC_HARNESS_TINY.md`

An emergency bootstrap file for extremely small context windows.

Use it when even the small-context file is too much for the harness.

It contains only:

- minimal role-claim rules
- minimal lease rules
- minimal file read order
- minimal continue-working behavior

### `PROJECT.md`

The global mission and direction for the harness root.

Use it to define:

- what this harness root is for
- what success looks like
- constraints
- current focus

### `LAYER_ACCESS.md`

Authority and write rules.

Use it to define:

- who may write which files
- what `Chief_of_Staff` may control
- what role agents may update
- operator override authority

### `LAYER_CONFIG.md`

Swarm configuration and registry.

Use it to track:

- the active `Chief_of_Staff` role
- lease timing rules
- the role registry
- archive policy
- path conventions

The registry should be kept in sync with live lease files.

### `LAYER_MEMORY.md`

Durable memory.

Use it for information that should survive across sessions:

- decisions
- policies
- important discoveries
- user preferences
- long-term project knowledge

Do not use it for routine chatter.

This is shared memory only.

Role-specific and human-specific long-term memory lives in `MEMORY/`.

### `LAYER_TASK_LIST.md`

The top-level task board.

Use it for:

- main tasks
- task status
- operator requests
- human-required work markers

### `LAYER_SHARED_TEAM_CONTEXT.md`

The team whiteboard.

Use it for:

- handoffs
- short coordination
- context snapshots
- team discussion
- status notes

High-contention rule:

- prefer append-only updates over full-file rewrites
- only one role should rewrite a structured file at a time
- if another role just updated a shared structured file, re-read it before applying your own change
- treat the first successful manual claim of a role on a chosen harness as the proof step before Runner owns that role on a timer

### `LAYER_LAST_ITEMS_DONE.md`

The operational event log.

Use it to record:

- role claims
- task starts
- completions
- handoffs
- notifications
- operator interventions
- message events

This is what lets new or returning workers understand what happened last and continue from there.

### `ROLES.md`

The intended role list.

Use it to define:

- which roles exist
- what each role is for
- what capabilities are expected
- which roles may write which kinds of work

Live occupancy is not decided here.

Live occupancy is decided by the lease files in `_heartbeat/`.

`ROLES.md` uses `Default Availability` as design-time intent only.

If a role is currently held, that will appear in:

- `_heartbeat/<Role>.md`
- `LAYER_CONFIG.md`

### `HUMANS.md`

Human registry.

Use it to track:

- human IDs
- names
- roles
- contact methods
- escalation preferences

It also points to the human memory files used by `Chief_of_Staff`.

Human IDs should use:

- full first and last name in CamelCase
- plus a random 4-digit suffix

Example:

- `SolomonChrist4821`

## Supporting Folders

### `_heartbeat/`

One file per live role.

These are lease files, not static metadata.

They show:

- who holds the role
- which harness claimed it
- what task it is working on
- last renewal time
- lease expiry time

If a lease expires, another bot may take over the role.

A role is only fully joined when:

- the lease file exists
- the registry reflects the holder
- the shared context has a join note
- the event log has a role-claim entry

### `_messages/`

Direct message files.

Use these for:

- bot-targeted messages
- human-targeted replies
- Telegram bridge communication

Examples:

- `_messages/Chief_of_Staff.md`
- `_messages/Researcher.md`
- `_messages/human_SolomonChrist4821.md`

### `_archive/last_items_done/`

Monthly archive storage for older event log entries.

### `MEMORY/`

Long-term markdown memory store.

Use this for:

- role-specific memory
- operator/human memory
- always-available standing context
- recent dated memories
- archived memory summaries older than 30 days

Recommended structure:

- `MEMORY/agents/<Role>/ALWAYS.md`
- `MEMORY/agents/<Role>/ONBOARDING_STATUS.md`
- `MEMORY/agents/<Role>/RECENT/YYYY-MM-DD.md`
- `MEMORY/agents/<Role>/ARCHIVE/YYYY-MM-summary.md`
- `MEMORY/humans/<HumanID>/ALWAYS.md`
- `MEMORY/humans/<HumanID>/RECENT/YYYY-MM-DD.md`
- `MEMORY/humans/<HumanID>/ARCHIVE/YYYY-MM-summary.md`

How it works:

- every role keeps its own memory lane
- a new harness taking over a role reads that role memory before normal work
- `Chief_of_Staff` reads the operator's human memory before normal operator-facing work
- `Chief_of_Staff` reads `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` to see whether first-run onboarding has already happened
- `ALWAYS.md` stores things that should be remembered every session
- `RECENT/` stores dated short-term memory files
- after 30 days, recent memory should be summarized into `ARCHIVE/`
- archive summaries remain readable as long-term memory

### `Projects/`

Every major request or client project should become its own subproject here.

Recommended structure:

- `Projects/<project-slug>/PROJECT.md`
- `Projects/<project-slug>/TASKS.md`
- `Projects/<project-slug>/CONTEXT.md`
- `Projects/<project-slug>/ARTIFACTS/`

### `SKILLS/`

Reusable patterns and learned behaviors.

If a worker discovers a reusable workflow, prompt pattern, or operational method, it should be stored here so capability compounds over time.

## Bots, Leases, and Humans

Bots use leases.

Humans use checkout.

### Bot Lease Model

Each active bot role writes to:

- `_heartbeat/<Role>.md`

That file acts as a renewable lease.

If the lease expires, another bot may claim the role.

This makes the system robust when:

- a harness crashes
- a session closes
- a machine restarts
- a different harness takes over

### Weak Harnesses

Some harnesses cannot run a timed background loop.

That is fine.

They can still participate by renewing their lease:

- on each meaningful file write
- through a wrapper
- through a local supervisor
- on every meaningful file write if they cannot maintain a timer loop

If a role notices that its own lease is stale, renewing the lease becomes the highest-priority action before normal work continues.

### Human Checkout Model

Humans should not use heartbeat or lease semantics.

When a task needs a human:

- mark it `WAITING_ON_HUMAN` if nobody has accepted it yet
- mark it `HUMAN_CHECKOUT` once a named human owns it

Track things like:

- `Checked Out By`
- `Expected Follow-Up`
- `Last Human Contact At`
- `Escalate After`
- `Contact Method`

## Role Memory And Operator Memory

This is the long-term continuity layer.

Every role should be able to remember over time, even if a different harness takes over later.

That means:

- `Researcher` should inherit prior researcher memory
- `Engineer` should inherit prior engineering memory
- `Chief_of_Staff` should inherit prior operator-facing memory

`Chief_of_Staff` specifically should remember the operator through:

- `MEMORY/humans/<HumanID>/ALWAYS.md`
- `MEMORY/humans/<HumanID>/RECENT/`
- `MEMORY/humans/<HumanID>/ARCHIVE/`

It should also keep an onboarding marker in:

- `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md`

This is where preferences, tone, recurring priorities, known constraints, and important relationship context should live.

Every role should also have:

- `MEMORY/agents/<Role>/ALWAYS.md`
- `MEMORY/agents/<Role>/RECENT/`
- `MEMORY/agents/<Role>/ARCHIVE/`

This lets any replacement harness read the role memory and continue with more context than just the current task list.

## Chief_of_Staff First-Run Onboarding

The first time `Chief_of_Staff` takes over a fresh install, it should not rely on manual setup by the operator.

It should:

1. detect whether `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` exists and says onboarding is complete
2. if not, start operator onboarding itself
3. learn who the operator is
4. learn how the operator prefers to work
5. create or update the operator record in `HUMANS.md`
6. write operator memory into `MEMORY/humans/<HumanID>/`
7. write standing `Chief_of_Staff` role memory into `MEMORY/agents/Chief_of_Staff/ALWAYS.md`
8. mark onboarding complete in `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md`

Future `Chief_of_Staff` replacements should:

- read onboarding status
- load the operator memory
- skip rerunning full onboarding unless the memory is missing or needs repair

Recommended onboarding tone:

- conversational
- warm
- concise
- professional
- human

Recommended first onboarding question:

```text
What is your name? (ex. Firstname Lastname)
```

After that, `Chief_of_Staff` should continue naturally and learn the operator's goals, preferences, update style, approval style, and working habits without sounding like a robotic intake form.

## Optional Add-Ons

### Telegram Bridge

`TelegramBot/` is an optional add-on.

It is not part of the core control plane.

Its job is simple:

- let you talk to the active MasterBot from Telegram
- write your messages into `_messages/Chief_of_Staff.md`
- forward replies from `_messages/human_<HumanID>.md`
- preserve the same natural conversational style you would get in the desktop harness, because Telegram is only the transport layer
 
This is useful when the chosen harness does not natively support Telegram or remote messaging.

### Visualizer

`Visualizer/` is an optional add-on.

It is also not part of the core control plane.

Its job is to visualize the swarm through:

- 3D view
- 2D view
- VR view

It should read the same markdown files and remain a visual layer, not the source of truth.

## Why This Matters

Agentic Harness is trying to solve a practical problem:

how do you keep a multi-agent system usable when tools change, providers change, sessions end, computers restart, and work still needs to continue?

The answer here is:

- keep the control plane simple
- keep it file-based
- keep it local-first
- keep it readable by both humans and machines

## The Simplicity Rule

If a new feature makes the system harder to understand than the files themselves, reject it.

The files are the infrastructure.

## Recommended First Test

1. Copy this folder into a fresh project location.
2. Start one harness.
3. Tell it:

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
```

4. Let that first harness become `Chief_of_Staff`.
5. Add additional harnesses only after the role structure is clear.

That is the normal minimal boot prompt.

The rest should be driven by the markdown protocol itself, including first-run onboarding if it has not already been completed.

## First-Time User Experience

Recommended first experience:

1. create a brand-new folder
2. copy Agentic Harness into that folder
3. use one harness you already trust
4. let that harness become `Chief_of_Staff`
5. let `Chief_of_Staff` walk you through onboarding, memory, and Runner setup

This is the safest way to learn the system before pointing it at important live work.

Windows cleanup note:

- If you are trying to delete an old Agentic Harness test folder and Windows says files are still in use, you may still have background Python processes from `Runner`, `TelegramBot`, or `Visualizer`.
- To see what is actually alive before guessing, run:

```powershell
py swarm_status.py
py production_check.py
```

- `swarm_status.py` shows always-on daemons, daemonized roles, last role-cycle launch times, role-cycle PIDs, wake queue count, recent events, and per-role launch logs.
- If you still need to delete the folder, close any obvious terminal windows first, then use:

```powershell
taskkill /F /IM python.exe
```

- After that, try deleting the old folder and copying a fresh install again.

Assumptions for first-time users:

- you have at least one harness available
- you may only have one harness at first
- you may be using a cloud harness such as Claude Code, Codex, or Antigravity
- or you may be using a private/local harness such as Ollama or LM Studio

Recommended first boot:

- normal harnesses: use `AGENTIC_HARNESS.md`
- very small local/offline harnesses: use `AGENTIC_HARNESS_TINY.md`

The system is designed so that the first `Chief_of_Staff` should do the setup work after reading the file protocol.

That includes:

- operator onboarding
- human memory creation
- `Chief_of_Staff` memory setup
- Runner discovery and setup
- initial harness catalog creation
- initial role launch registry setup
- optional add-on offer during onboarding, with setup only if you accept

The intended result of Runner setup is not just "daemon is running."

The intended result is:

- roles that have confirmed working launch methods should auto-launch or auto-nudge on schedule
- those roles should re-check their messages and assigned work on each wake cycle
- the operator should not have to manually type `check status` just to keep the swarm moving
- for Claude Code roles, the preferred always-on pattern is short scheduled `claude -p` automation cycles rather than expecting one open terminal window to stay autonomous forever
- `Chief_of_Staff` should be the one that gets Runner to this state during onboarding; users should not need to invent a separate Runner prompt after first boot
- when new specialist roles join, `Chief_of_Staff` should register them into the Runner immediately so they become part of the scheduled swarm instead of staying permanent side sessions
- if a role joins through a harness that does not yet have a proven non-interactive launch path, it should be registered as manual for now instead of being mislabeled as a Claude auto-cycle
- on a fresh install, `Chief_of_Staff` should not jump ahead to “what project do you want to do?” or “here are your Researcher/Engineer prompts” until Runner setup has been completed and the add-on offer has happened
- `DRY_RUN` is only a brief verification mode; the normal onboarding outcome should be an `ACTIVE` Runner in that same session once the launch plan is confirmed

Urgent work should not wait for the next normal interval.

Examples:

- a Telegram message arrives for `Chief_of_Staff`
- `Chief_of_Staff` dispatches urgent work to `Researcher`
- `Engineer` flags a stale lease or blocker that needs immediate follow-up

In those cases, the message sender should write an immediate wake request so Runner starts or nudges the target role right away.

This is not meant to be Claude-only.

The broader goal is:

- one Runner
- many harness families
- each role registered with the command or wrapper that actually works on that machine
- scheduled wake cycles across Claude Code, OpenCode, Ollama, Goose, Gemini, Codex, Antigravity, and other compatible harnesses

The operator should not need to manually prebuild those files just to get started.

The expected first-run order is:

1. `Chief_of_Staff` claims the role
2. operator onboarding finishes
3. Runner is discovered, configured, and started or the exact start command is given
4. Telegram is proactively offered if `TelegramBot/` exists
5. Visualizer is proactively offered if `Visualizer/` exists
6. only then does `Chief_of_Staff` move into specialist-role setup and project intake

If a fresh install reaches role-launch prompts before Runner and the add-on offer have been addressed, that first-run experience is incomplete.

## First Boot Prompts

These prompts are meant to help users get started quickly with a fresh Agentic Harness install.

Prompt style rule:

- When `Chief_of_Staff` gives you a prompt for another harness, it should default to the shortest prompt that can work.
- The receiving harness should learn the rest from the file protocol, not from a giant pasted checklist.
- Only use verbose/debug prompts when you explicitly ask for them.

### Chief of Staff Prompt

Use this for the first harness you launch. For most users, this is all that should be needed:

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
```

The onboarding, lease updates, registry writes, join note, event log entry, and next actions should all be handled by `Chief_of_Staff` after reading the file protocol.

If `Runner/` is present, `Chief_of_Staff` should treat it as part of the core system and own the first-pass Runner setup as part of the same onboarding flow.
After that setup, `Chief_of_Staff` should start the Runner if the local harness can execute local commands.
If you explicitly asked for it to be started, `Chief_of_Staff` should prefer actually launching it in the background instead of only printing the command.
Only if it cannot run it directly should it fall back to giving the exact start command.

If `TelegramBot/` or `Visualizer/` are present, `Chief_of_Staff` should proactively offer those add-ons during onboarding and let you say yes or no.
If you accept one of them, `Chief_of_Staff` should guide the setup, then start it when possible.
If you explicitly asked for it to be started, `Chief_of_Staff` should prefer actually launching it in the background instead of only printing the command.
Only if it cannot run it directly should it fall back to giving the exact start command.

Recommended onboarding tone for that moment:

- Telegram = remote chat with the active MasterBot when you are away from the computer
- Visualizer = a live visual world for seeing roles, tasks, and swarm activity
- `Chief_of_Staff` should explain those simply, explicitly mention that the live Visualizer system exists, and ask if you want either one set up now

### Specialist Role Prompt Pattern

When `Chief_of_Staff` asks you to launch a specialist, the default prompt style should stay short and reusable.

Use this pattern:

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Claim the <ROLE> role if it is available or stale.
```

Examples:

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Claim the Researcher role if it is available or stale.
```

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Claim the Engineer role if it is available or stale.
```

That same 3-line pattern should stay the default for future roles too. `Chief_of_Staff` should not fall back to long boot-checklist prompts unless you explicitly ask for a verbose/debug version.

### Compact Prompt For Small-Context Models

Use this only if a harness cannot comfortably read the full main spec but can still handle the compact file:

```text
Read AGENTIC_HARNESS_SMALL_CONTEXT.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
```

### Tiny Prompt For Very Small-Context Models

Use this when a harness has a very small context window:

```text
Read AGENTIC_HARNESS_TINY.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Still run normal first-run onboarding: ask my name, create my human memory, and offer Telegram/Visualizer before specialist roles.
```

This is the preferred first boot path for very small local/offline harnesses such as some Ollama or LM Studio setups.

### Existing System Specialist Prompt

Use this for additional harnesses after `Chief_of_Staff` has already created or approved the roles:

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Take the role of <ROLE> if it is open or stale.
```

### Generic Research Role Prompt

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Take the role of Researcher if it is open or stale.
```

### Generic Engineer Role Prompt

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Take the role of Engineer if it is open or stale.
```

### Generic Documentation Role Prompt

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Take the role of Documentation if it is open or stale.
```

### Verbose Debug Prompt

Use a longer prompt only if a specific harness is failing to follow the file protocol and you need to be more explicit.

### Example: LM Studio

```text
Read AGENTIC_HARNESS_TINY.md first.
Take role: Researcher if open or stale.
Claim the role, update your lease, write a short join note, write an event log line, then continue the current work.
Renew your lease on meaningful writes and report progress through the markdown files.
Do not stop for plan approval unless blocked or a real operator decision is required.
Do not treat the role as fully joined until the lease, registry, join note, and event log are all updated.
Do not adopt TelegramBot, Visualizer, or any optional add-on as project work unless the operator explicitly assigned it.
```

### Example: Antigravity

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Take the role of Engineer if it is open or stale.
Then continue the work already in progress.
If you claim the role, renew your lease on meaningful writes and complete the assigned engineering work through the markdown files.
Do not stop for plan approval unless blocked or a real operator decision is required.
Do not treat the role as fully joined until the lease, registry, join note, and event log are all updated.
Do not adopt TelegramBot, Visualizer, or any optional add-on as project work unless the operator explicitly assigned it.
```

### Telegram-Connected Chief of Staff Behavior

If you are using the optional Telegram bridge, the active `Chief_of_Staff` should also follow this rule:

```text
Watch _messages/Chief_of_Staff.md for operator messages.
Reply to the operator by writing to _messages/human_<HumanID>.md.
Treat the Telegram layer as transport only. You remain the system orchestrator.
```

When Telegram is active, do not leave operator-facing questions or status updates only in the local harness window.

If the operator is remote, `Chief_of_Staff` should write those updates and questions to `_messages/human_<HumanID>.md` so the Telegram bridge can forward them externally.

## Mixed Harness Examples

Agentic Harness is meant to support mixed swarms such as:

- Claude Code as `Chief_of_Staff`
- LM Studio as a Researcher or Documentation role
- Antigravity as an Engineer or Operations role

Each harness can bring its own strengths as long as it follows the same markdown protocol.

## Telegram Setup Shortcut

For Telegram, the intended flow is:

1. the user gets the bot token from `@BotFather`
2. the user gets their Telegram user ID from `@userinfobot`
3. the user gives those two values to `Chief_of_Staff`
4. `Chief_of_Staff` writes `TelegramBot/.env.telegram`
5. the user starts the bridge with:

```powershell
py -m pip install requests python-dotenv
python -m pip install requests python-dotenv
py TelegramBot\\telegram_bot.py
python TelegramBot\\telegram_bot.py
```

That keeps the setup simple and lets the active `Chief_of_Staff` do the file configuration work.

Recommended instruction to give `Chief_of_Staff`:

```text
Configure the Telegram bridge for this install.
Use the Telegram bot token and Telegram user ID I provide.
Write the correct values into TelegramBot/.env.telegram.
Use the current harness root for HARNESS_ROOT.
Use the operator Human ID from HUMANS.md for HUMAN_ID.
Use POLL_INTERVAL_SECONDS=2, TELEGRAM_ACK_AFTER_SECONDS=0, TELEGRAM_TYPING_INTERVAL_SECONDS=4, and TELEGRAM_REPLY_WAIT_SECONDS=90.
After writing the file, continue using Telegram as transport only by reading _messages/Chief_of_Staff.md and replying through _messages/human_<HumanID>.md.
```

## Runner Layer

Agentic Harness also supports one optional `Runner/` layer.

Purpose:

- keep the swarm alive
- wake harnesses on interval
- relaunch roles when needed
- monitor stale leases
- support persistent, interval, and manual/human-run execution modes

The Runner is not the source of truth.

It only handles liveness.

The files remain the source of truth.

Execution modes:

- `persistent` = the harness stays running and the Runner monitors it
- `interval` = the Runner wakes the harness every X minutes
- `manual` = the role is expected to be run manually by a human or operator-driven harness

Human-run roles are valid too.

Example:

- the operator uses Claude Code manually
- claims a role like `HumanRunner`
- reports completed work back into the markdown system

That still fits the Agentic Harness model.

The Runner layer should also remember how this machine launches harnesses.

Recommended pattern:

- `Chief_of_Staff` asks the operator which harnesses are installed
- `Chief_of_Staff` checks for common harness families such as Claude Code, OpenCode, Ollama, Goose, Antigravity, Google CLI, Codex, Manus, and n8n
- confirmed harnesses are recorded in `Runner/HARNESS_CATALOG.md`
- role-specific launch methods are recorded in `Runner/ROLE_LAUNCH_REGISTRY.md`

That way a future request like:

- "Make a research bot using Claude Code and Haiku"

can be translated into a remembered launch entry without forcing the operator to repeat the same command details every time.

Important limitation:

- the Runner can only relaunch a harness automatically if the role registry contains a real working launch command for that harness on that machine
- if a harness needs a special wrapper to accept a prompt non-interactively, that wrapper command should be stored in `Runner/ROLE_LAUNCH_REGISTRY.md`
- for auto-managed roles, the Runner should also leave a short wake/check instruction in `_messages/<Role>.md` so the relaunched harness knows what to do next
- until a working launch command exists, the role should remain manual
- even with a working launch command, a specialist role should stay unarmed for scheduled automation until it has completed one successful manual first claim on the chosen harness for this install
- for local infrastructure daemons, prefer `py service_manager.py start|stop|status <runner|telegram|visualizer|all>` over ad hoc background shell syntax

## Runner Setup Shortcut

Fastest path:

1. start `Chief_of_Staff`
2. let it detect and record the harnesses it can confirm on this machine
3. let it ask you only about any additional or custom harnesses it could not confirm itself
4. let it fill:
   - `Runner/HARNESS_CATALOG.md`
   - `Runner/ROLE_LAUNCH_REGISTRY.md`
5. keep `Runner/RUNNER_CONFIG.md` in `DRY_RUN`
6. start the daemon
7. inspect what it would launch before switching to live mode

This is intended to be driven by `Chief_of_Staff` during first-run setup. The operator should not have to manually build the Runner configuration from scratch.

Recommended instruction to give `Chief_of_Staff`:

```text
Set up the Runner for this install.
First, check this machine and local environment for common harnesses you know how to look for.
Then update Runner/HARNESS_CATALOG.md with what you can confidently confirm.
After that, ask me only about any other harnesses or custom commands I use that were not already detected or confirmed.
Next, update Runner/ROLE_LAUNCH_REGISTRY.md with the actual role-to-harness launch entries we want to use.
Use Chief_of_Staff as the first role to configure.
Keep Runner/RUNNER_CONFIG.md in DRY_RUN mode for the first pass.
Do not guess launch commands if you are unsure. Ask me to confirm them.
```

If you have already manually launched a working swarm and want to convert that into the first remembered Runner configuration, use this:

```text
Set up the Runner now.

Use the current live swarm as the first known working configuration:
- Chief_of_Staff = Claude Code (Haiku 4.5)
- Researcher = Claude Code
- Engineer = Claude Code

Update Runner/HARNESS_CATALOG.md with the confirmed harnesses on this machine.
Update Runner/ROLE_LAUNCH_REGISTRY.md with launch entries for Chief_of_Staff, Researcher, and Engineer.
Keep Runner/RUNNER_CONFIG.md in DRY_RUN mode.
Do not switch to active mode yet.
After that, tell me exactly how to start the Runner daemon and what it would try to launch.
```

## In One Line

Agentic Harness is a markdown-first meta harness for running a real multi-agent system across many harness types through one shared, local-first control plane.

## Safety And Recovery Docs

If your biggest worries are lock-in, restarts, backups, or recovery, start here:

- `START_HERE.md`
- `SYSTEM_MAP.md`
- `BACKUP_AND_RECOVERY.md`
- `RECOVERY_CHECKLIST.md`
- `PAIN_POINTS_AND_SOLUTIONS.md`
- `PAIN_POINTS_AND_SOLUTIONS.html`


