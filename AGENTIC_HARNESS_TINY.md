# AGENTIC HARNESS TINY

For very small context windows or low-spend setup runs.

Use this when a harness cannot reliably read `AGENTIC_HARNESS.md` or `AGENTIC_HARNESS_SMALL_CONTEXT.md`, or when Claude Code credits must be protected.

## Low-Spend Rules

- Do not read `AGENTIC_HARNESS.md` unless this tiny file is insufficient for the immediate task.
- Do not read full files when only the first section, latest lines, or a specific role block is needed.
- Do not print long file contents back to the operator.
- Do not auto-launch specialist roles on Claude.
- Use Claude for `Chief_of_Staff` setup only unless the operator explicitly approves a Claude worker role.
- Prefer local/cheaper CLI harnesses for `Researcher`, `Engineer`, QA, and other specialists.
- Keep replies short and actionable.
- Do not add `Runner`, `TelegramBot`, or `Visualizer` as swarm roles. They are infrastructure services, not role-holding agents.
- To start infrastructure on Windows, run `py service_manager.py start all` or tell the operator to double-click `start_all_services.bat`.
- Starting services is not enough for production chat. Before the operator closes the first Chief window, run `py configure_role_daemon.py --role Chief_of_Staff --provider <provider> --model <model> --start-runner`, then verify with `py production_check.py`.

## Universal Task Contract

Agentic Harness exists to help the operator overcome any task by combining the
right role, harness, tool, and local context. Do not turn the system into a
single-purpose shortcut. When the operator asks for something, infer the needed
capability, then either do it directly, use available CLI/local tools, configure
and wake a daemon-capable specialist, or give the shortest honest fallback if
blocked. Do not wait for manual specialist setup when a safe daemon default is
already registered.

## Do Only This

1. Take one role only.
2. Check `ROLES.md` and `_heartbeat/` to see if that role is open or stale.
3. Claim it in `_heartbeat/<Role>.md`.
4. Update `LAYER_CONFIG.md` if needed.
5. Write one short join line to `LAYER_SHARED_TEAM_CONTEXT.md`.
6. Write one short role-claim line to `LAYER_LAST_ITEMS_DONE.md`.
7. Do not treat the role as fully joined until `_heartbeat/`, `LAYER_CONFIG.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and `LAYER_LAST_ITEMS_DONE.md` all match.
8. Read only the relevant current task blocks from `LAYER_TASK_LIST.md`.
9. Continue the current assigned work.
10. Renew your lease every 5 minutes, or on every meaningful write if you cannot keep time.
11. If your lease is stale, renew it before doing anything else.
12. While active, re-check only new lines or relevant sections from `_messages/<Role>.md`, `LAYER_TASK_LIST.md`, and current project context on each lease renewal or meaningful work step.
13. Do not ask for plan approval unless blocked or a real operator decision is needed.
14. Do not create new projects unless explicitly told to.
15. During bootstrap, do not adopt `TelegramBot/`, `Visualizer/`, or any optional add-on as project work unless the operator explicitly assigned it.
16. Read `MEMORY/agents/<Role>/ALWAYS.md` if it exists before normal work.
17. If you are `Chief_of_Staff`, read `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` if it exists.
18. If you are `Chief_of_Staff` and the operator is known, read `MEMORY/humans/<HumanID>/ALWAYS.md` if it exists before operator-facing work.
19. If you are `Chief_of_Staff` and onboarding status is missing or incomplete, run first-run operator onboarding, write operator memory, configure infrastructure services, then hand off worker roles to non-Claude or manual-first harnesses unless the operator explicitly approves Claude workers.
20. If the operator asks to set up Telegram, Visualizer, or Runner, do not create roles for them. Start or configure the services with `service_manager.py` and report the exact URL/status.

## Chief Of Staff First-Run Onboarding

Tiny mode is low-context, not no-onboarding.

If you are `Chief_of_Staff` and `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` is missing or not `COMPLETE`, do this before project intake or specialist prompts:

1. Claim `Chief_of_Staff` first.
2. Ask: `What is your name? (ex. Firstname Lastname)`
3. Ask one short follow-up for preferred working style and update style.
4. Ask whether the operator wants Telegram remote chat configured now if `TelegramBot/` exists.
5. Tell the operator the Visualizer exists if `Visualizer/` exists, and ask whether they want it started/configured now.
6. Create a Human ID using `FirstnameLastname` plus 4 random digits.
7. Update `HUMANS.md`.
8. Write `MEMORY/humans/<HumanID>/ALWAYS.md`.
9. Update `MEMORY/agents/Chief_of_Staff/ALWAYS.md` with operator preferences.
10. Mark `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` as `COMPLETE`.
11. Only after onboarding and infrastructure handling, move to specialist roles or project intake.
12. Do not say the operator can close the desktop harness until `py production_check.py` passes.

Keep the questions short and natural. Do not skip the name/memory setup just because this is tiny mode.

## Minimal Files

Read only these:

- `AGENTIC_HARNESS_TINY.md`
- `ROLES.md`
- `_heartbeat/<Role>.md` if it exists
- `LAYER_CONFIG.md`
- `LAYER_TASK_LIST.md`
- `LAYER_SHARED_TEAM_CONTEXT.md`
- latest lines from `LAYER_LAST_ITEMS_DONE.md`
- `MEMORY/agents/<Role>/ALWAYS.md` if it exists
- `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` if you are `Chief_of_Staff`

Do not read `README.md`, `SYSTEM_MAP.md`, `BACKUP_AND_RECOVERY.md`, `RECOVERY_CHECKLIST.md`, `PAIN_POINTS_AND_SOLUTIONS.*`, or full project artifacts unless directly needed for the current user request.

## Infrastructure Is Not A Role

These folders are services:

- `Runner/`
- `TelegramBot/`
- `Visualizer/`

Do not add them to `ROLES.md`.
Do not create `_heartbeat/Runner.md`, `_heartbeat/TelegramBot.md`, or `_heartbeat/Visualizer.md`.
Do not create long briefing files for them in `_messages/`.

Use this instead:

```powershell
py service_manager.py start all
py service_manager.py status all
py production_check.py
```

Or tell the operator to double-click:

```text
start_all_services.bat
```

## Lease Fields

Write at least:

- `Role`
- `Status: ACTIVE`
- `Claimed By`
- `Harness`
- `Provider`
- `Model`
- `Session ID`
- `Last Renewal`
- `Lease Expires At`
- `Current Project`
- `Current Task`
