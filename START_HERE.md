# START HERE

Agentic Harness is designed to be safe to try in a brand-new folder first.

## First-Time Setup

1. Create a fresh folder.
2. Copy Agentic Harness into that folder.
3. Open one harness you already trust.
4. Paste:

```text
Read AGENTIC_HARNESS.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
```

If your harness has a very small context window, use:

```text
Read AGENTIC_HARNESS_TINY.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
```

## What Should Happen Next

`Chief_of_Staff` should:

- onboard you
- create your human/operator memory
- if `Runner/` is present, set up the Runner during onboarding and leave it in `DRY_RUN` first
- after Runner setup, try to start it or give you the exact command immediately
- if you later ask for optional add-ons like Telegram or Visualizer, guide you through those setups step by step
- if one of those add-ons is fully configured, try to start it or give you the exact command immediately
- recommend additional roles only when needed

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

Those are the “how do I recover / what do I back up / what is this system” docs.
