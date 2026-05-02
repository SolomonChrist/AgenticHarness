# ChiefChat

ChiefChat is the fast operator chat service for `Chief_of_Staff`.

It is intentionally separate from Claude Code and Runner. Telegram, Visualizer,
console chat, and future transports write to `_messages/CHAT.md`; ChiefChat
reads that ledger, uses a cheap configurable model for normal replies, and
writes clean operator-facing responses back to the same ledger plus the legacy
human outbox.

ChiefChat also includes the active operator's human memory in its prompt. It
reads the active human ID from `HUMANS.md`, then loads that person's
`MEMORY/humans/<HumanID>/ALWAYS.md` and recent memory folder when present. This
keeps ordinary "you know who I mean" conversations from losing important people,
preferences, or standing personal context.

## Interaction Layer

ChiefChat is still true to Agentic Harness: markdown files remain the source of
truth, and deeper work is still delegated to roles/harnesses. The live chat path
now adds a small OpenClaw-like interaction layer around that file-first core:

- each operator message is classified before any model call
- deterministic file/status/web actions happen first when possible
- each action writes a compact trace to `ChiefChat/data/activity.md`
- weak web replies such as "I'm checking now" are rejected when evidence exists
- web answers fall back to source evidence instead of pretending
- complex work is captured or routed to role tasks before Chief says it was done

This gives the operator the feeling of an active assistant without making
ordinary Telegram chat depend on Claude Code, OpenClaw, or another heavy harness.

Useful commands:

```powershell
py ChiefChat\setup_chief_chat.py
py service_manager.py start chief-chat
py service_manager.py status chief-chat
py ChiefChat\chief_chat_service.py --once
py ChiefChat\chief_chat_service.py --status
py ChiefChat\chief_chat_service.py --cleanup-stale-web-tasks
```

Supported chat providers:

- `openai-compatible` for LM Studio or any compatible local endpoint
- `ollama`
- `opencode`
- `fake` for local validation only

## Deterministic Actions

ChiefChat treats common operator commands as a control-plane action, not as
plain chat. The local model can make the response sound human, but it is not
trusted to claim state changes.

The built-in action skills live under `ChiefChat/skills/`:

- `task_management`: cancel, complete, reopen, assign, and annotate tasks
- `reminders`: personal checklist and reminder entries
- `role_routing`: route/wake roles and bot aliases
- `web_research`: create `TASK-WEB-*` traces and gather source evidence

For task mutations, ChiefChat writes to `LAYER_TASK_LIST.md` or
`Projects/*/TASKS.md`, appends an audit note, then replies with verified before
and after counts plus changed task IDs. If no task matched, it says that no
files changed.

Examples:

```text
Remove those web requests
Complete TASK-ABC
Reopen TASK-ABC
Assign TASK-ABC to Engineer
Wake Mary
Add note to TASK-ABC: keep this as priority one
```

Stale web/current-info tasks can be cleaned without Telegram:

```powershell
py ChiefChat\chief_chat_service.py --cleanup-stale-web-tasks
```

## Context Budget

ChiefChat is the cheap always-on front door, so its prompt is intentionally
compact. It includes small excerpts from the Chief soul, Chief always memory,
active human memory, recent chat, and system status instead of full logs.

Tune this in `ChiefChat/CHIEF_CHAT_CONFIG.md`:

```text
Chief Soul Max Chars: 1200
Chief Always Memory Max Chars: 900
Human Memory Max Chars: 1200
Human Recent Files: 2
Human Recent File Max Chars: 500
Recent Chat Max Chars: 1400
Reply Max Tokens: 450
Chief Interaction Mode: bounded-action-loop
Action Loop Max Steps: 4
Activity Log Enabled: YES
Activity Log Max Entries: 200
```

If ChiefChat starts sounding forgetful, raise the specific budget that is too
low. If local model calls get expensive or slow, lower `Recent Chat Max Chars`
first, then human recent memory.

Web/current-info requests use a source-first path. ChiefChat creates a durable
`TASK-WEB-*` task, gathers clean web evidence with Playwright, then asks the
cheap model to answer only from that evidence. Weather requests use a direct
Open-Meteo lookup so a message like `check the weather in Toronto` returns the
actual current conditions instead of a "checking now" placeholder. If the cheap
model fails or only sends a progress update, ChiefChat replies with the extracted
source evidence and leaves the task open for deeper follow-up.

ChiefChat should not try to bypass sites that block automation. If sources such
as Yelp or Tripadvisor restrict automated access, ChiefChat skips opening those
pages, uses safer official/alternate source results when available, and leaves
the `TASK-WEB-*` task open for manual or specialist follow-up.

Task intake is protected from the web path. If the operator says things like
`add these tasks`, `put this in the task list`, `figure out which team members
we need`, or `delegate these items`, ChiefChat writes `TASK-INTAKE-*` items to
`LAYER_TASK_LIST.md`, creates wake requests for the recommended owner roles, and
only then confirms the routing. Lists that contain words like "research",
"Google Drive", or "AI news" are still treated as backlog/delegation requests
when the operator asked for task capture.

ChiefChat runs an intent gate before using the cheap chat model or browser
path. The current high-level intents are presence, model identity, task intake,
single-task capture, role creation, role routing, weather, web/current-info, and
status, named-human handoff, freeform work capture, and normal chat. This
matters because human conversation like "today was a lot, help me think" should
stay a normal Chief conversation, while "what events are happening in Toronto
tonight?" should use the web evidence path.

Role and bot aliases are resolved before human handoffs. If a bot/harness is
named `Mary` but holds the `Knowledge_Architect` role, put that alias in the
role files or heartbeat with fields such as `Name: Mary`, `Bot Name: Mary`, or
`Agent Name: Mary`. ChiefChat will route "check with Mary" to the role task
flow before falling back to `HUMANS.md`. Humans are only used when no matching
role or bot alias exists.

For operational truthfulness, ChiefChat has deterministic write paths for common
operator commands:

- "make sure this is in the task list" captures the previous operator message
  as a real `TASK-CHIEFCHAT-CAPTURE-*` item before confirming.
- "add the Strategist role" creates a real role entry in `ROLES.md` and
  `Runner/ROLE_LAUNCH_REGISTRY.md`, leaves `Automation Ready: NO`, and creates a
  `TASK-ROLE-SETUP-*` item so the operator can choose a harness.
- Backlog triage tasks created from task intake are marked
  `WAITING_ON_HUMAN`, because the Chief should prioritize them with the
  operator rather than relaunching itself repeatedly.
- "Status update" replies from the files: task counts, owners, wake requests,
  role readiness, and visible tasks. It should not claim a role is executing
  unless the file layer proves it.
- Freeform work requests like "I need you to go through my lead list..." become
  durable `TASK-CHIEFCHAT-CAPTURE-*` items before Chief confirms action.
- Named-human handoffs like "Ask Mary to help with Obsidian" create
  `TASK-HUMAN-ASSIST-*` records and clearly say whether the contact route is
  known. Chief should not say the human was contacted unless a transport or
  manual confirmation records it.

Location incident requests, such as "I am at Bloor and Bathurst and there is a
huge lineup, what is going on?", should trigger situational investigation mode:
normalize speech-to-text location errors, fan out across events, venue schedules,
news, Reddit/Twitter-like public traces, and nearby likely venues, then answer
with a sourced best guess and confidence instead of saying it cannot see the
street.

ChiefChat should be truthful about its own runtime. When asked what model it is
using, it reports the live ChiefChat provider/model first and distinguishes that
from deeper Runner role models such as Claude Code. It also asks a quick
clarifying question for ambiguous places instead of guessing, and it only says a
task was routed after writing the task and wake-request files.

Claude Code and other heavy harnesses should still be used for bootstrap,
coding, research, and deep work. ChiefChat is the always-on conversation and
orchestration path.
