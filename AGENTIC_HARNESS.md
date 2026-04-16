# AGENTIC HARNESS

Agentic Harness is a file-first meta-harness for autonomous agent swarms.

The system is the files. Any harness, agent, or worker that can read and write markdown files can participate.

Read this file first. Then read the other core files in the order defined below.

## Small-Context Bootstrap

If your context window is very small, prioritize only these rules first:

- Claim only one role and do not act before claiming it in `_heartbeat/<Role>.md`.
- After claiming a role, update the registry if needed, write a short join note to `LAYER_SHARED_TEAM_CONTEXT.md`, and write a role-claim event to `LAYER_LAST_ITEMS_DONE.md`.
- Renew your lease every 5 minutes while active, or on every meaningful write if you cannot keep time reliably.
- If your own lease is stale, renew it before doing anything else.
- Read the current top-level task list before opening new work.
- Continue the active milestone or workstream before asking for a new direction.
- Use `_messages/<Role>.md` for direct coordination when possible.
- Use `Projects/<project-slug>/CONTEXT.md` for project-local coordination.
- Do not create new projects, optional add-on work, or side initiatives unless the operator or `Chief_of_Staff` explicitly asked for them.
- If blocked by a real decision, ask briefly. Otherwise continue.

## Purpose

- Provide one universal coordination layer across any harness system.
- Keep orchestration portable, inspectable, and easy to back up.
- Allow role-based swarms to survive restarts, model swaps, and harness changes.
- Keep the system simple enough that the files alone remain the source of truth.

## Source Of Truth

These files are the control plane:

1. `AGENTIC_HARNESS.md`
2. `PROJECT.md`
3. `LAYER_ACCESS.md`
4. `LAYER_CONFIG.md`
5. `LAYER_MEMORY.md`
6. `LAYER_TASK_LIST.md`
7. `LAYER_SHARED_TEAM_CONTEXT.md`
8. `LAYER_LAST_ITEMS_DONE.md`
9. `ROLES.md`
10. `HUMANS.md`

Supporting directories:

- `_heartbeat/`
- `_messages/`
- `_archive/last_items_done/`
- `Projects/`
- `SKILLS/`

## Core Operating Model

- One active `Chief_of_Staff` role orchestrates the swarm.
- On a fresh install, `Chief_of_Staff` is the only default role.
- The human/operator may also update `LAYER_TASK_LIST.md` directly.
- Roles are defined in `ROLES.md`.
- `ROLES.md` defines intended roles and desired availability, not live occupancy.
- Live role occupancy is determined by one renewable lease file per role in `_heartbeat/`.
- If a role lease expires, another bot may take over that role.
- If an older bot returns and sees a fresher claimant for its role, it must stand down.
- Main work is tracked in `LAYER_TASK_LIST.md`.
- Project-specific sub-tasks live inside `Projects/<project-slug>/TASKS.md`.
- Team discussion and handoffs go in `LAYER_SHARED_TEAM_CONTEXT.md`.
- Durable memory goes in `LAYER_MEMORY.md`.
- Every meaningful action is logged in `LAYER_LAST_ITEMS_DONE.md`.
- Reusable patterns should be written into `SKILLS/` so expertise compounds across sessions.

## First-Run Behavior

On a fresh install:

- Only the `Chief_of_Staff` role should exist by default.
- The first harness should claim `Chief_of_Staff`.
- The `Chief_of_Staff` should ask the operator what they want to do.
- The `Chief_of_Staff` should then create or recommend the additional roles needed for the work.

On an existing-project install:

- Create a fresh Agentic Harness root.
- Place the existing project inside `Projects/<project-slug>/`.
- The first `Chief_of_Staff` should inspect that project structure and contents.
- The `Chief_of_Staff` should recommend which roles are needed.
- The operator decides which roles to add to `ROLES.md`.

## Work Until Done

The swarm should keep working until the requested outcomes are completed.

- Claim a task.
- Work it until done.
- Mark it complete.
- Log the result.
- Claim the next available task.

Do not ask between tasks unless genuinely blocked or the operator must decide something that changes project direction, scope, or real-world intent.

If there is an active milestone, validation pass, or assigned workstream already in progress, continue that work first before asking for a new direction.

Blocked work:

- Mark the work blocked.
- Log the reason.
- Ask for help in `LAYER_SHARED_TEAM_CONTEXT.md` if needed.
- Move to the next available task instead of idling.

Human-required work:

- Mark it as human-needed.
- Log a notification event.
- Continue with the next available task.

Context pressure:

- If a harness is reaching context limits, it should save a concise resume snapshot to the relevant context file and continue cleanly in the next session.

## Boot Order For Any Harness

Every harness or agent joining this system must do the following:

1. Read `AGENTIC_HARNESS.md`.
2. Read `LAYER_ACCESS.md`.
3. Read `ROLES.md`.
4. Inspect `_heartbeat/` to determine which roles are active and which are stale.
5. Ask the operator which role to take unless the role was explicitly assigned.
6. If the chosen role is stale or open, claim it by writing `_heartbeat/<Role>.md`.
7. Read `PROJECT.md`.
8. Read `LAYER_CONFIG.md`.
9. Read `LAYER_TASK_LIST.md`.
10. Read `LAYER_SHARED_TEAM_CONTEXT.md`.
11. Read recent items from `LAYER_LAST_ITEMS_DONE.md`.
12. Write a short online/join note to `LAYER_SHARED_TEAM_CONTEXT.md`.
13. Write a role-claim event to `LAYER_LAST_ITEMS_DONE.md`.
14. Begin work according to the claimed role.

After claiming a role, do not stop to ask for permission to perform routine system updates such as:

- registry update
- join note
- event log entry
- task status update
- direct message write

Proceed unless blocked by missing information or a real operator decision.

## Lease And Takeover Rules

Each active bot role writes to exactly one file:

- `_heartbeat/<Role>.md`

These files should be treated as renewable leases with heartbeat-style refreshes.

Required lease renewal interval:

- Every 5 minutes while active.
- If the harness cannot reliably run a timer, renew on every meaningful write.

Required fields:

- `Role`
- `Status`
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

Session types:

- `persistent`
- `session`
- `manual`

Renewal methods:

- `self`
- `wrapper`
- `supervisor`
- `event-driven`

Expiry rule:

- If `Lease Expires At` is in the past, the role may be claimed by another bot.
- A role must never continue normal work while its own lease is stale.

Takeover rule:

- The new bot writes a fresh lease and becomes the active holder of the role.
- If the previous bot returns and sees a fresher claim for the same role, it must stop acting in that role and exit the system or wait for reassignment.

Weak harness rule:

- If a harness cannot run a timer loop, it may renew the lease on each file-touching action.
- If a harness cannot self-renew at all, a local wrapper or supervisor on the user's machine should renew the lease while the session is active.
- Meaningful write actions include task updates, project file updates, context writes, event log writes, message writes, and artifact creation.

Stale self-repair rule:

- If a role sees that its own lease is stale or nearing expiry, lease renewal becomes its highest-priority action before any other work.
- After renewing, it may continue normal work.

Stale peer rule:

- If a role notices another role is stale, it should log the condition to `LAYER_LAST_ITEMS_DONE.md`.
- If the stale role is `Chief_of_Staff`, also write a direct note to `_messages/Chief_of_Staff.md`.
- If the stale role remains stale past the expiry threshold, another suitable bot may take over according to the lease rules.

## Permissions

- Only the active `Chief_of_Staff` may create, reprioritize, or close top-level tasks in `LAYER_TASK_LIST.md`.
- Other role agents may create and complete sub-tasks inside their assigned project folders.
- The human/operator may override any file in the system at any time.

## Projects

Each major request becomes its own subproject under `Projects/`.

Expected project structure:

- `Projects/<project-slug>/PROJECT.md`
- `Projects/<project-slug>/TASKS.md`
- `Projects/<project-slug>/CONTEXT.md`
- `Projects/<project-slug>/ARTIFACTS/`

Top-level files remain the swarm-wide control plane.

Existing projects may also be adopted into Agentic Harness by placing them inside `Projects/` and letting the first `Chief_of_Staff` inspect and plan around them.

Project-creation boundary:

- Only create a new project folder when the operator or `Chief_of_Staff` has explicitly requested that project.
- Do not autonomously adopt optional add-ons such as `TelegramBot/` or `Visualizer/` into `Projects/` unless that work was explicitly assigned.
- Specialist roles should focus on assigned tasks inside existing workstreams instead of inventing new project lanes.

## Messaging

Shared discussion:

- `LAYER_SHARED_TEAM_CONTEXT.md`

Direct role-targeted messaging:

- `_messages/<Role>.md`

Use direct message files for role-specific instructions that should not clutter the shared whiteboard.

Notification entries intended for Telegram or remote operator attention should be logged in `LAYER_LAST_ITEMS_DONE.md` with a clear `NOTIFY` marker.

High-contention rule:

- `LAYER_SHARED_TEAM_CONTEXT.md` is shared and may be edited by multiple live roles.
- Keep entries short and append-only whenever possible.
- Use `_messages/<Role>.md` for direct coordination when multiple workers are active at once.
- Use `Projects/<project-slug>/CONTEXT.md` for project-local collaboration to reduce collisions in the global shared context file.

## Humans In The Loop

Humans do not use bot-style role leases.

Humans use task checkout.

When a task requires a human:

- mark the task as `WAITING_ON_HUMAN` if no person has accepted it yet
- mark the task as `HUMAN_CHECKOUT` once a named human owns it
- track follow-up and escalation dates rather than heartbeat

Recommended fields for human-owned work:

- `Checked Out By`
- `Checked Out At`
- `Expected Follow-Up`
- `Last Human Contact At`
- `Escalate After`
- `Contact Method`
- `Reason`

Human IDs should use:

- full first name and last name in CamelCase
- followed by a random 4-digit identifier

Example:

- `SolomonChrist4821`

Human contact details should be stored in `HUMANS.md`.

Direct human messaging files should use:

- `_messages/human_<HumanID>.md`

## Telegram Executive Assistant

The ideal state is that the active `Chief_of_Staff` acts as the operator's Executive Assistant.

If the chosen harness does not natively provide remote messaging, use the optional Telegram EA layer.

Telegram should:

- run on the user's own system
- read and write the same markdown control plane
- allow the operator to talk to the `Chief_of_Staff` remotely
- allow remote task creation and status checks
- act only as a transport bridge if the chosen harness does not natively support remote messaging

## Memory

`LAYER_MEMORY.md` is durable team and project memory.

Write only information that should persist across sessions:

- decisions
- policies
- user preferences
- important discoveries
- workflow facts
- long-term project knowledge

Do not use memory for routine chatter.

## Event Log

`LAYER_LAST_ITEMS_DONE.md` is the operational event bus.

Log:

- role claims
- role releases
- task starts
- task completions
- task blocks
- handoffs
- direct messages
- memory writes
- archive rollovers
- operator interventions
- notifications

Archive older entries monthly into `_archive/last_items_done/YYYY-MM.md`.

## Chief Of Staff Fallback Rule

If no specialist exists for a task:

- The `Chief_of_Staff` should attempt the work when practical.
- The `Chief_of_Staff` must log that it is covering a missing role.
- The `Chief_of_Staff` should notify the operator which role should be added to improve future execution.

## Mixed Harness Support

Agentic Harness is designed to support mixed swarms.

Examples:

- Claude Code as `Chief_of_Staff`
- LM Studio as a local Researcher or Documentation role
- Antigravity as an Engineer or Operations role

Different harnesses may have different strengths and different runtime limits.

That is acceptable as long as they follow the same file protocol.

## Simplicity Rule

If a behavior or extension makes the system harder to understand than the files themselves, reject it.

The files are the infrastructure.
