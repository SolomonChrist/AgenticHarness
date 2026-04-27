# START HERE

Agentic Harness is designed to be safe to try in a brand-new folder first.

## Maintainer Reset Rule

Before shipping updates, publishing a zip, or handing this folder to a new user, reset it back to first-run state:

```powershell
py reset_to_fresh_state.py
```

That reset is expected to:

- clear runtime artifacts, logs, caches, locks, generated prompts, and daemon state files
- empty `_heartbeat/`, `_messages/`, `Projects/`, and `_archive/last_items_done/`
- remove old human/operator runtime memory while keeping the shipped templates
- restore the control-plane markdown files and Runner templates to their clean first-run defaults

The goal is that every shipped update should behave like a fresh download, not like a previously used workspace.

## First-Time Setup

Agentic Harness starts in two phases:

- **Phase 1: manual onboarding in your chosen harness.** Open Claude Code, OpenCode, Goose, Codex CLI, Gemini CLI, or another trusted harness in this folder and let it claim `Chief_of_Staff`.
- **Phase 2: operate from Visualizer.** After onboarding and daemon handoff, Visualizer is the default local command center. Telegram is optional remote/mobile chat if you configure it.

1. Create a fresh folder.
2. Copy Agentic Harness into that folder.
3. Open one harness you already trust.
4. Paste:

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Run normal first-run onboarding.
```

If your harness has a very small context window, use:

```text
Read AGENTIC_HARNESS_TINY.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Still run normal first-run onboarding: ask my name, create my human memory, and offer Telegram/Visualizer before specialist roles.
```

If you are using Claude Code and want the lowest practical token spend, use:

```text
Read AGENTIC_HARNESS_TINY.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Low-spend mode: do not read the full protocol unless blocked, do not auto-launch Claude worker roles, keep setup replies short, but still run normal operator onboarding.
```

See `CLAUDE_LOW_SPEND_START.md` before running a Claude-based setup.

## What Should Happen Next

`Chief_of_Staff` should:

- onboard you
- create your human/operator memory
- explain that Visualizer is the default local command center after setup
- offer Telegram as an optional remote chat add-on, not a required dependency
- if `Runner/` is present, set up the Runner during onboarding as a built-in core step
- Runner is not an optional add-on; it is part of the core bring-up when `Runner/` exists
- leave Runner in `DRY_RUN` only long enough to verify the launch plan, then move it to `ACTIVE` real always-on wake behavior in that same onboarding flow
- after that, start the Runner or give you the exact command immediately if local execution is not possible
- automatically register newly joined specialist roles into the Runner so they become scheduled swarm members, not one-off manual side sessions
- if `TelegramBot/` or `Visualizer/` are present, proactively offer those add-ons during onboarding so you can accept or decline them
- if you accept Telegram or Visualizer, guide you through that setup step by step
- if one of those add-ons is fully configured, start it or give you the exact command immediately if local execution is not possible
- recommend additional roles only when needed

Important:

- on a fresh install, `Chief_of_Staff` should not jump straight from onboarding into project intake or specialist launch prompts
- Runner bring-up must happen first if `Runner/` exists
- the Telegram offer must happen if `TelegramBot/` exists
- the Visualizer offer must happen if `Visualizer/` exists
- only after those core first-run steps are handled should `Chief_of_Staff` ask what you want to work on next or hand you specialist prompts
- when specialist prompts are needed, they should stay short and follow the same reusable 3-line pattern with only the role name changed
- CLI-capable roles should be treated as the primary automation path
- manual-call systems should be documented as secondary roles that can still participate, but they are not the first daemon-owned target
- every specialist role should be manually proven once on its chosen harness before Runner owns that role on timer
- `Runner/`, `TelegramBot/`, and `Visualizer/` are infrastructure services, not swarm roles; do not add them to `ROLES.md`
- use `py service_manager.py start all` or `start_all_services.bat` to start those services

The goal is that confirmed roles should auto-launch or auto-nudge on schedule so the system keeps moving without you having to manually tell each harness to check status.

The operator should not have to invent a separate Runner prompt after onboarding. `Chief_of_Staff` should own that step by default.

Default specialist prompt pattern:

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Claim the <ROLE> role if it is available or stale.
```

For Claude Code roles, the preferred built-in pattern is short scheduled Claude work cycles rather than depending on one open terminal window to stay autonomous forever.

Preferred infrastructure launcher on Windows:

```powershell
start_all_services.bat
```

That launcher starts Runner and Visualizer through `service_manager.py`, opens Visualizer in your browser, and starts Telegram only when real Telegram credentials are configured.

Starting services is not the same thing as daemonizing `Chief_of_Staff`. `py service_manager.py start runner` starts the scheduler only. It does not create the background Chief brain unless `Chief_of_Staff` has also been registered with `configure_role_daemon.py`.

## Chief Of Staff Daemon Handoff

After `Chief_of_Staff` has completed the first manual setup and onboarding, you can hand that role to the Runner daemon so the original desktop harness window can be closed.

Windows helper:

```powershell
configure_chief_daemon.bat
```

Direct command examples:

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider gemini --model gemini-2.5-pro --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider codex --model gpt-5.4 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider goose --model claude-4-sonnet --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider ollama --model llama3.1 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider deepagents --model gpt-5.4 --start-runner
py configure_role_daemon.py --role Chief_of_Staff --provider openclaw --model default-agent --start-runner
```

Built-in provider keys are `claude`, `opencode`, `gemini`, `codex`, `goose`, `ollama`, `deepagents`, and `openclaw`. You should not need to explain these command shapes during onboarding; Agentic Harness already knows the non-interactive launch patterns and records your chosen model/profile.

For a Chief that should answer weather, web, and current-info questions directly, choose a web-capable online provider. Claude daemon cycles enable Chrome integration when available, Codex daemon cycles enable live search, and Gemini/OpenCode/Goose/DeepAgents/OpenClaw depend on their configured provider/tools. Ollama is local/offline by default and should give verification steps or route to a web-capable role for current facts.

Custom CLI example:

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider custom --name my-cli --command-template "cliname [FLAGS] \"{PROMPT}\" [ARGS]" --model my-model --start-runner
```

This records the role in `Runner/ROLE_LAUNCH_REGISTRY.md`, turns Runner `ACTIVE`, and lets Telegram or timer wake requests launch short fresh-context `Chief_of_Staff` CLI cycles.

## CLI-First Scheduled Runs

After daemon handoff, recurring role work should be started by cheap scheduled CLI checks, not by always-on inference.

One role check:

```powershell
py Runner\scheduled_role_runner.py --role Chief_of_Staff
py Runner\scheduled_role_runner.py --role Engineer --dry-run
```

Daily all-hands check:

```powershell
py Runner\daily_all_hands.py
py Runner\daily_all_hands.py --dry-run
```

Core job board without Visualizer:

```powershell
py role_jobs.py status
py role_jobs.py enable Chief_of_Staff
py role_jobs.py disable Engineer
```

The preflight checks local files first:

- role enabled and automation-ready
- lease absent or expired
- assigned actionable task, explicit wake request, direct role message, operator intake for `Chief_of_Staff`, or daily all-hands due
- provider and stale-lease cooldown state

Manual file edits are supported. If you add a `TODO` or `IN_PROGRESS` task to `LAYER_TASK_LIST.md` or `Projects/<Project>/TASKS.md` with `Owner Role: <ROLE>`, the next scheduled check can wake that role without another setup step.

If a provider quota/login failure is detected, Runner pauses that provider path and creates a `Chief_of_Staff` task asking the operator to configure a replacement harness or wait for quota recovery. `Daily All Hands` is enabled by default every 24 hours so recovered quota can be retried automatically.

Verify the handoff before closing your original harness window:

```powershell
py production_check.py
```

If it passes, it is safe to close the desktop harness. If it fails, keep the harness open and run the corrective command it prints.

Use the same pattern for every CLI-capable role after that role has been manually claimed once:

```powershell
py configure_role_daemon.py --role Researcher --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role QA --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Documentation --provider ollama --model llama3.1 --start-runner
```

Production rule:

- first run: a human starts the harness and lets it claim the role once
- after proof: run `configure_role_daemon.py` for that role
- after daemon handoff: Runner owns timer wakes, Telegram wakes, stale lease recovery, and role dispatch wakeups
- if a harness cannot be launched from the command line, keep it manual and document the human call steps in that role's message file
- any prompt-based CLI can be registered with a command template that uses `{PROMPT}`, `{PROMPT_FILE}`, `{ROLE}`, `{WORKDIR}`, and `{MODEL}`
- final setup message: "Telegram and Visualizer are running. I still need daemon handoff before you close this window."

That add-on offer should feel human, not robotic.

Example tone:

- Telegram lets you chat with the active MasterBot when you are away from the computer.
- Visualizer gives you a live visual view of your roles, tasks, and swarm activity.
- `Chief_of_Staff` should briefly explain those, explicitly alert you that the Visualizer system exists, and ask if you want either one set up now.

## Safest Way To Learn The System

Do not point it at your most important live work first.

Instead:

- test in a fresh folder
- get `Chief_of_Staff` working
- test Runner in `DRY_RUN`
- add Telegram only if you want remote messaging
- then move into real projects

## Most Important Files

- `AGENTIC_HARNESS.md` = rules of the system
- `README.md` = user-facing overview
- `LAYER_TASK_LIST.md` = top-level work
- `LAYER_MEMORY.md` = shared memory
- `MEMORY/` = role and human memory
- `Runner/` = optional liveness layer
- `TelegramBot/` = optional remote chat

## If Something Goes Wrong

Open:

- `RECOVERY_CHECKLIST.md`
- `BACKUP_AND_RECOVERY.md`
- `SYSTEM_MAP.md`

Those are the "how do I recover / what do I back up / what is this system" docs.
