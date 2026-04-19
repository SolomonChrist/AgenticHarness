# Agentic Harness Commands

## Start, Stop, And Status

```powershell
py service_manager.py start all
py service_manager.py stop all
py service_manager.py status all
```

Windows helpers:

```powershell
start_all_services.bat
stop_all_services.bat
status_all_services.bat
```

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
