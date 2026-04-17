# AGENTIC HARNESS SMALL CONTEXT

Use this file for harnesses with small context windows.

If a harness cannot comfortably read `AGENTIC_HARNESS.md`, it may read this file first, join the system, and then read only the minimum additional files it needs for its assigned role.

## Purpose

Join Agentic Harness with the minimum possible instructions.

## Minimum Rules

1. Do not act until you claim exactly one role.
2. Read `ROLES.md` and inspect `_heartbeat/` to find whether your intended role is open or stale.
3. Claim your role by writing `_heartbeat/<Role>.md`.
4. After claiming:
   - update `LAYER_CONFIG.md` registry if needed
   - write a short join note to `LAYER_SHARED_TEAM_CONTEXT.md`
   - write a role-claim event to `LAYER_LAST_ITEMS_DONE.md`
   - do not treat the role as fully joined until all four surfaces match
5. Read `LAYER_TASK_LIST.md` and continue the active work already in progress.
6. Renew your lease every 5 minutes while active.
7. If you cannot run a timer, renew on every meaningful write.
8. If your own lease is stale, renew it before doing anything else.
9. Do not stop for plan approval unless you are blocked or need a real operator decision.
10. Do not create new projects or side initiatives unless the operator or `Chief_of_Staff` explicitly requested them.
11. During bootstrap, do not adopt `TelegramBot/`, `Visualizer/`, or any optional add-on as project work unless the operator explicitly assigned it.
12. Read `MEMORY/agents/<Role>/ALWAYS.md` if it exists before normal work.
13. If you are `Chief_of_Staff`, read `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` if it exists.
14. If you are `Chief_of_Staff` and the operator is known, read `MEMORY/humans/<HumanID>/ALWAYS.md` if it exists before operator-facing work.
15. If you are `Chief_of_Staff` and onboarding status is missing or incomplete, run first-run operator onboarding, write operator memory, then continue.

## Minimum Files To Read

Read these in order:

1. `AGENTIC_HARNESS_SMALL_CONTEXT.md`
2. `LAYER_ACCESS.md`
3. `ROLES.md`
4. `_heartbeat/<Role>.md` if it exists
5. `LAYER_CONFIG.md`
6. `LAYER_TASK_LIST.md`
7. `LAYER_SHARED_TEAM_CONTEXT.md`
8. Recent entries from `LAYER_LAST_ITEMS_DONE.md`
9. `MEMORY/agents/<Role>/ALWAYS.md` if it exists
10. `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` if you are `Chief_of_Staff`
11. `MEMORY/humans/<HumanID>/ALWAYS.md` if you are `Chief_of_Staff` and the operator is known

## Role Claim Template

Write `_heartbeat/<Role>.md` with at least:

- `Role`
- `Status: ACTIVE`
- `Claimed By`
- `Harness`
- `Provider`
- `Model`
- `Session ID`
- `Session Type`
- `Renewed By`
- `Claimed At`
- `Last Renewal`
- `Lease Expires At`
- `Current Project`
- `Current Task`

## Meaningful Writes

If you cannot keep time reliably, renew your lease whenever you:

- update a task
- update project files
- write shared context
- write the event log
- write a direct message
- create an artifact

## Messaging

- Use `_messages/<Role>.md` for direct role messages.
- Use `_messages/human_<HumanID>.md` for human replies when instructed.
- Use `Projects/<project-slug>/CONTEXT.md` for project-local collaboration.

## Human Rule

Humans do not use leases.

Tasks needing a human should use:

- `WAITING_ON_HUMAN`
- `HUMAN_CHECKOUT`

Human details and human memory live in:

- `HUMANS.md`
- `MEMORY/humans/<HumanID>/`

## Optional Telegram Rule

If the optional Telegram bridge is in use and you are `Chief_of_Staff`:

- watch `_messages/Chief_of_Staff.md`
- reply in `_messages/human_<HumanID>.md`

## Mixed Harness Rule

Different harnesses may have different limits.

That is acceptable.

Follow the file protocol, keep messages short, and continue the current workstream.
