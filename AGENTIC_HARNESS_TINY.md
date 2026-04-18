# AGENTIC HARNESS TINY

For very small context windows only.

Use this when a harness cannot reliably read `AGENTIC_HARNESS.md` or `AGENTIC_HARNESS_SMALL_CONTEXT.md`.

## Do Only This

1. Take one role only.
2. Check `ROLES.md` and `_heartbeat/` to see if that role is open or stale.
3. Claim it in `_heartbeat/<Role>.md`.
4. Update `LAYER_CONFIG.md` if needed.
5. Write one short join line to `LAYER_SHARED_TEAM_CONTEXT.md`.
6. Write one short role-claim line to `LAYER_LAST_ITEMS_DONE.md`.
7. Do not treat the role as fully joined until `_heartbeat/`, `LAYER_CONFIG.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and `LAYER_LAST_ITEMS_DONE.md` all match.
8. Read `LAYER_TASK_LIST.md`.
9. Continue the current assigned work.
10. Renew your lease every 5 minutes, or on every meaningful write if you cannot keep time.
11. If your lease is stale, renew it before doing anything else.
12. While active, re-check `_messages/<Role>.md`, `LAYER_TASK_LIST.md`, and current project context on each lease renewal or meaningful work step.
13. Do not ask for plan approval unless blocked or a real operator decision is needed.
14. Do not create new projects unless explicitly told to.
15. During bootstrap, do not adopt `TelegramBot/`, `Visualizer/`, or any optional add-on as project work unless the operator explicitly assigned it.
16. Read `MEMORY/agents/<Role>/ALWAYS.md` if it exists before normal work.
17. If you are `Chief_of_Staff`, read `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` if it exists.
18. If you are `Chief_of_Staff` and the operator is known, read `MEMORY/humans/<HumanID>/ALWAYS.md` if it exists before operator-facing work.
19. If you are `Chief_of_Staff` and onboarding status is missing or incomplete, run first-run operator onboarding, write operator memory, then continue.

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
