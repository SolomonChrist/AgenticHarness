# Agentic Harness Commands

## Start, Stop, And Status

```powershell
py service_manager.py start all
py service_manager.py stop all
py service_manager.py status all
py swarm_status.py
```

Windows helpers:

```powershell
start_all_services.bat
stop_all_services.bat
status_all_services.bat
```

Important: these commands start the infrastructure services only. They do not daemonize `Chief_of_Staff`. After first-run onboarding, run the daemon handoff command below before closing the desktop harness.

## First Manual Claim Prompt

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Run normal first-run onboarding: ask my name, create my human memory, set up Runner, and offer Telegram/Visualizer before specialist roles.
```

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
py configure_role_daemon.py --role Chief_of_Staff --provider ollama --model llama3.1 --start-runner
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
py configure_role_daemon.py --role Documentation --provider ollama --model llama3.1 --start-runner
```

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
