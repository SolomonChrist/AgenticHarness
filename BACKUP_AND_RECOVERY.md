# BACKUP AND RECOVERY

This is the minimum safety model for Agentic Harness.

## What To Back Up

Back up these areas:

1. Core control plane
- root markdown files
- `_heartbeat/`
- `_messages/`
- `_archive/`
- `MEMORY/`
- `SKILLS/`

2. Projects
- `Projects/`

3. Runner
- `Runner/`

4. Optional add-ons only if you use them
- `TelegramBot/`
- `Visualizer/`

5. Secrets separately
- `.env` files
- Telegram token files
- API keys
- OAuth credentials

Do not rely on only one copy.

## Best Practical Backup Layout

Keep:

- one working local copy
- one synced cloud copy
- one offline or external-drive copy for recovery

## If Your Computer Dies

To restore:

1. restore the folder
2. restore secrets/env files
3. open the folder in a trusted harness
4. boot `Chief_of_Staff`
5. let it read:
   - memory
   - task board
   - leases
   - event log
6. restart Telegram and Runner if used

## What Not To Confuse

- project work = `Projects/`
- orchestration state = core markdown files
- long-term human/role knowledge = `MEMORY/`
- liveness = `Runner/`

If you back up only project code and not the control plane or memory, recovery will be much harder.

## Recovery Goal

A future harness should be able to reopen the folder and continue the work without needing the original vendor, model, or session history.
