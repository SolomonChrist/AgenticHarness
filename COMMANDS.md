# Agentic Harness Commands

## Start, Stop, And Status

```powershell
py start.py
start.bat
py dashboard.py
dashboard.bat
py ChiefChat\setup_chief_chat.py
py service_manager.py start core
py service_manager.py start all
py service_manager.py stop all
py service_manager.py status all
py swarm_status.py
```

`py start.py` is the simplest normal startup command. It starts services, prints status, runs `production_check.py`, and checks whether the configured local model server is reachable. `start.bat` is the double-click wrapper. `py dashboard.py` opens the live CLI dashboard; `dashboard.bat` is the double-click wrapper.

`core` starts ChiefChat, Runner, and Telegram when Telegram is configured. ChiefChat is the fast Telegram/Visualizer/console conversation layer; Runner is for scheduled role work and heavier harness launches.

## Fast Chief Chat

```powershell
py ChiefChat\setup_chief_chat.py
py service_manager.py start chief-chat
py service_manager.py status chief-chat
py ChiefChat\chief_chat_service.py --once
py ChiefChat\chief_chat_service.py --status
```

Normal Telegram chat should go through ChiefChat and `_messages\CHAT.md`, not through Claude Code. Configure the cheap model path in `ChiefChat\CHIEF_CHAT_CONFIG.md` with `openai-compatible`, `ollama`, `opencode`, or `fake` for local validation.

## CLI-First Scheduled Role Checks

Use these from Runner, Windows Task Scheduler, cron, or any local scheduler. They perform cheap file/lease/task checks before any provider call.

```powershell
py Runner\scheduled_role_runner.py --role Chief_of_Staff
py Runner\scheduled_role_runner.py --role Engineer --dry-run
py Runner\daily_all_hands.py
py Runner\daily_all_hands.py --dry-run
```

Core job board without Visualizer:

```powershell
py role_jobs.py status
py role_jobs.py dashboard
py role_jobs.py dashboard --watch 2
py dashboard.py
py dashboard.py --once
py role_jobs.py enable Chief_of_Staff
py role_jobs.py disable Engineer
```

Backup and restore:

```powershell
py backup_restore.py backup --mode bots-only
py backup_restore.py backup --mode bots-projects
py backup_restore.py backup --mode full-system-git-history
py backup_restore.py restore --source C:\path\to\backup.zip --target C:\restore\AgenticHarness
py backup_restore.py restore --source C:\path\to\backup.bundle --target C:\restore\AgenticHarness
```

Suggested Windows Task Scheduler action:

```powershell
Program: py
Arguments: Runner\scheduled_role_runner.py --role Chief_of_Staff
Start in: C:\path\to\AgenticHarness
```

The run is skipped without inference when the role is disabled, already leased, not automation-ready, blocked by cooldown, or has no actionable work. Manually adding a task with `Owner Role: <ROLE>` and `Status: TODO` or `Status: IN_PROGRESS` to `LAYER_TASK_LIST.md` or `Projects\<Project>\TASKS.md` is enough for the next scheduled check to find it.

`Daily All Hands` is enabled by default every 24 hours through `Runner/RUNNER_CONFIG.md`:

```text
Daily All Hands Enabled: YES
Daily All Hands Interval Hours: 24
Daily All Hands Quota Retry: YES
```

If a provider reports quota, rate-limit, or login failure, Runner pauses automatic launches for that provider path and creates/updates a `Chief_of_Staff` task to help the operator configure a replacement harness or wait for quota recovery.

## n8n Folder Mirror

Use this when n8n needs to work from a Google Drive synced copy of the same
Agentic Harness files:

```powershell
py n8n_harness\setup_folder_mirror.py
py n8n_harness\folder_mirror.py --config n8n_harness\mirror_config.local.json
```

Direct start without saved setup:

```powershell
py n8n_harness\folder_mirror.py --left "C:\path\to\AgenticHarness" --right "G:\My Drive\AgenticHarness_MainSystem"
```

Deletion propagation is off by default. Add `--delete` only after the initial
mirror has been checked.

Windows helpers:

```powershell
py start.py
start_all_services.bat
stop_all_services.bat
status_all_services.bat
```

`start_all_services.bat` now calls `py start.py --open-dashboard`. Use `py start.py --core` when you want only ChiefChat, Runner, and Telegram.

Important: these commands start the infrastructure services only. They do not daemonize `Chief_of_Staff`. After first-run onboarding, run the daemon handoff command below before closing the desktop harness.

## First Manual Claim Prompt

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Run normal first-run onboarding: ask my name, create my human memory, set up Runner, and offer Telegram/Visualizer before specialist roles.
```

After daemon handoff, use Visualizer as the default local chat and dashboard. Telegram is optional remote/mobile access.

## Existing Role Claim Prompt

```text
Read AGENTIC_HARNESS.md first.
This is an existing Agentic Harness system.
Claim the <ROLE> role if it is available or stale.
```

## Daemonize Chief Of Staff

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

After handoff, verify:

```powershell
py production_check.py
```

Only close the original desktop harness after this reports `PRODUCTION CHECK PASSED`.

## Daemonize Any CLI-Capable Role

```powershell
py configure_role_daemon.py --role Researcher --provider opencode --model minimax-m2.5-free --start-runner
py configure_role_daemon.py --role QA --provider claude --model claude-haiku-4-5-20251001 --start-runner
py configure_role_daemon.py --role Engineer --provider codex --model gpt-5.4 --start-runner
py configure_role_daemon.py --role Researcher --provider gemini --model gemini-2.5-flash --start-runner
py configure_role_daemon.py --role Documentation --provider ollama --model llama3.1 --start-runner
```

Built-in provider keys:

- `claude`
- `opencode`
- `gemini`
- `codex`
- `goose`
- `ollama`
- `deepagents`
- `openclaw`

For ordinary current-information work, ChiefChat should create a `TASK-WEB-*` record, gather source evidence with Playwright when enabled, and answer from that evidence through the cheap model. Weather uses the direct Open-Meteo fast path. Use a web-capable role or heavier harness when the source extraction is incomplete or the task needs deeper research.

## Register A Custom CLI Provider

```powershell
py configure_role_daemon.py --role Chief_of_Staff --provider custom --name my-cli --command-template "cliname [FLAGS] \"{PROMPT}\" [ARGS]" --model my-model --start-runner
```

Supported placeholders:

- `{PROMPT}`
- `{PROMPT_FILE}`
- `{ROLE}`
- `{WORKDIR}`
- `{MODEL}`

## Reset And Ship Check

```powershell
py reset_to_fresh_state.py
py ship_check.py
```

## Live Production Check

```powershell
py production_check.py
```

Use this after first-run setup and after daemon handoff. It tells you whether Telegram has a real background `Chief_of_Staff` responder or only a bridge.

## Swarm Status

```powershell
py swarm_status.py
```

Use this when you want to know what is actually alive. It shows Runner, Telegram, Visualizer, daemonized roles, last role launch time, role-cycle PID, launch log path, wake queue count, and recent events.

## Operator Control Phrases

These work through Telegram and Visualizer chat when the local services are running:

```text
What harness and model are you on?
Reset yourself with Claude Code Sonnet.
Use Claude Code Haiku for Researcher.
Spawn Engineer with OpenCode minimax-m2.5-free.
```

CLI-capable role changes are applied directly to `Runner/ROLE_LAUNCH_REGISTRY.md` through `configure_role_daemon.py`, then Runner wakes the role.

## Safe Messaging Helpers

Use these instead of create-only `Write(...)` or shell redirection when a harness needs to reply or wake another role:

```powershell
py send_human_reply.py "Hello Solomon, I am online."
py wake_role.py --role Chief_of_Staff --reason telegram_message
py wake_role.py --role Researcher --reason task_assigned
```
