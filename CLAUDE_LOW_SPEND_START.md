# CLAUDE LOW-SPEND START

Use this when Claude Code credits are limited.

## Starter Prompt

```text
Read AGENTIC_HARNESS_TINY.md first.
This is a fresh Agentic Harness install.
Claim the Chief_of_Staff role if it is available.
Low-spend mode: do not read the full protocol unless blocked, do not auto-launch Claude worker roles, and keep setup replies short.
```

## Setup Policy

- Use Claude only for the initial `Chief_of_Staff` setup unless the operator explicitly approves more Claude work.
- Low-spend mode must still perform normal first-run operator onboarding.
- `Chief_of_Staff` should ask for the operator's name, working/update style, and Telegram/Visualizer preference before worker-role setup or project intake.
- `Chief_of_Staff` should write `HUMANS.md`, `MEMORY/humans/<HumanID>/ALWAYS.md`, and `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` during that first-run setup.
- Start infrastructure with `start_all_services.bat` or `py service_manager.py start all`.
- After infrastructure starts, daemonize `Chief_of_Staff` with `configure_role_daemon.py` and verify with `py production_check.py` before telling the operator they can close Claude Code.
- Register specialist roles as manual-first until they prove themselves once.
- Prefer local or cheaper CLI harnesses for `Researcher`, `Engineer`, QA, and other worker roles.
- Treat Antigravity and other GUI-only harnesses as manual-call systems.
- Do not add `Runner`, `TelegramBot`, or `Visualizer` to `ROLES.md`; they are infrastructure services.
- Do not create `_messages/Runner.md`, `_messages/TelegramBot.md`, or `_messages/Visualizer.md` briefings.

## Minimum Context For Claude

Claude should read only:

- `AGENTIC_HARNESS_TINY.md`
- `ROLES.md`
- `_heartbeat/Chief_of_Staff.md` if it exists
- `LAYER_CONFIG.md`
- the relevant current task blocks in `LAYER_TASK_LIST.md`
- latest useful lines from `LAYER_LAST_ITEMS_DONE.md`
- `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md`
- active operator memory only after the operator record exists

Avoid reading large docs, generated artifacts, visualizer vendor files, full event history, or unrelated project files during setup.

## What Good Looks Like

- Claude claims `Chief_of_Staff`.
- Claude onboards the operator briefly, starting with `What is your name? (ex. Firstname Lastname)`.
- Claude creates the human/operator record and memory.
- Claude configures Runner, Telegram, and Visualizer infrastructure.
- Claude starts infrastructure with `py service_manager.py start all` or tells the operator to use `start_all_services.bat`.
- Claude runs or gives the exact `configure_role_daemon.py` command, then confirms `py production_check.py` passes.
- Claude asks which non-Claude/local/manual harnesses should own worker roles.
- Claude does not start `Researcher`, `Engineer`, or QA on Claude unless explicitly approved.
