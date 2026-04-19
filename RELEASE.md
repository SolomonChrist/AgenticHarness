# Agentic Harness Release Checklist

Run this before publishing a zip, handing the folder to a user, or treating the repo as production-ready.

## Clean The Workspace

```powershell
py service_manager.py stop all
py reset_to_fresh_state.py
```

## Validate The Release

```powershell
py ship_check.py
```

The ship check must pass before release.

## Manual Review

- Confirm `TelegramBot/.env.telegram` does not exist.
- Confirm `TelegramBot/.env.telegram.template` contains no real token.
- Confirm `_heartbeat/`, `_messages/`, and `Projects/` are empty.
- Confirm `Runner/_generated_prompts/` has no prompt files.
- Confirm the public entrypoint is `START_HERE.md`.
- Confirm `COMMANDS.md` includes all stable commands.
- Confirm `FINAL_APPLICATION_DESIGN.md` matches the intended product contract.

## Stable Public Interfaces

- `py service_manager.py start all`
- `py service_manager.py stop all`
- `py service_manager.py status all`
- `py configure_role_daemon.py --role <ROLE> --provider <claude|opencode|goose|ollama|custom> --model <MODEL> --start-runner`
- `py reset_to_fresh_state.py`
- `py ship_check.py`
- `GET http://127.0.0.1:8787/api/state`
