# AGENTIC HARNESS

Agentic Harness is a file-first meta-harness for autonomous agent swarms.

The system is the files. Any harness, agent, or worker that can read and write markdown files can participate.

Read this file first. Then read the other core files in the order defined below.

If a harness has a very small context window and cannot comfortably ingest this full file, it may read `AGENTIC_HARNESS_SMALL_CONTEXT.md` first instead.

If that is still too large, it may use `AGENTIC_HARNESS_TINY.md` as the emergency bootstrap path.

## Small-Context Bootstrap

If your context window is very small, prioritize only these rules first:

- Claim only one role and do not act before claiming it in `_heartbeat/<Role>.md`.
- After claiming a role, update the registry if needed, write a short join note to `LAYER_SHARED_TEAM_CONTEXT.md`, and write a role-claim event to `LAYER_LAST_ITEMS_DONE.md`.
- Renew your lease every 5 minutes while active, or on every meaningful write if you cannot keep time reliably.
- If your own lease is stale, renew it before doing anything else.
- Read the current top-level task list before opening new work.
- Continue the active milestone or workstream before asking for a new direction.
- While active, periodically re-check your direct message file, the task board, and your current project context instead of waiting forever for a human to prompt you.
- As a practical default, roles should re-check those files on every lease renewal and after each meaningful work step.
- Use `_messages/<Role>.md` for direct coordination when possible.
- Use `Projects/<project-slug>/CONTEXT.md` for project-local coordination.
- Do not create new projects, optional add-on work, or side initiatives unless the operator or `Chief_of_Staff` explicitly asked for them.
- During bootstrap, do not adopt `TelegramBot/`, `Visualizer/`, or any optional add-on as project work unless the operator explicitly assigned that work.
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
- `MEMORY/`
- `Projects/`
- `SKILLS/`
- `Runner/`

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
- Shared durable memory goes in `LAYER_MEMORY.md`.
- Role and human long-term memory live in `MEMORY/`.
- Every meaningful action is logged in `LAYER_LAST_ITEMS_DONE.md`.
- Reusable patterns should be written into `SKILLS/` so expertise compounds across sessions.

## First-Run Behavior

On a fresh install:

- Assume the operator is starting in a new clean folder first, not on top of important live work.
- Assume the operator has at least one harness system available.
- Only the `Chief_of_Staff` role should exist by default.
- The first harness should claim `Chief_of_Staff`.
- The first `Chief_of_Staff` should run operator onboarding if it has not already been completed.
- During onboarding, `Chief_of_Staff` should learn who the operator is, how they prefer to work, and what standing preferences should be remembered.
- `Chief_of_Staff` should create or update the operator record in `HUMANS.md` and the matching human memory files in `MEMORY/humans/<HumanID>/`.
- `Chief_of_Staff` should also update its own `MEMORY/agents/Chief_of_Staff/ALWAYS.md` with standing executive-assistant behavior notes learned from that onboarding.
- If the optional Runner layer is present, `Chief_of_Staff` must also set up the Runner for the operator as part of first-run onboarding.
- That means `Chief_of_Staff` should first check the machine and local environment for common harness families already known to Agentic Harness.
- Then `Chief_of_Staff` should ask the operator only about any additional harnesses or custom commands that were not already detected or confirmed.
- `Chief_of_Staff` should then begin building remembered launch knowledge in `Runner/HARNESS_CATALOG.md` and `Runner/ROLE_LAUNCH_REGISTRY.md`.
- When a new specialist role is created or joins the swarm, `Chief_of_Staff` should immediately register that role in the Runner files instead of leaving it as an untracked manual side session.
- When a role joins through a harness that does not yet have a proven non-interactive Runner launch path, `Chief_of_Staff` should register that role accurately as a manual harness role instead of pretending it is auto-managed by some other harness.
- `Chief_of_Staff` should not register a manually claimed Antigravity, Gemini, Codex, or similar session as `{AUTO_CLAUDE_CYCLE}` just because Claude is available on the same machine.
- `Chief_of_Staff` should use `DRY_RUN` only long enough to confirm that the role decisions and launch commands look sane.
- Once the launch plan is confirmed, `Chief_of_Staff` should move the Runner into `ACTIVE` real scheduled management during that same onboarding flow instead of leaving the system indefinitely in `DRY_RUN`.
- For normal first-run onboarding, the expected end state is an active Runner, not a passive plan waiting for the operator to remember a second setup step later.
- The intended outcome of Runner setup is cron-like wake behavior: roles should auto-launch or auto-nudge on their configured intervals, re-check their tasks/messages, and keep work moving without requiring a human to type "check status" every time.
- Scheduled wake behavior is the fallback cadence, not the only trigger.
- If Telegram receives a new operator message, or if an active role assigns urgent work to another role, the system should write an immediate wake request for the target role instead of waiting for the next normal interval.
- The expected pattern is:
  - write the message/task assignment into the normal markdown surface
  - append an immediate wake request into `Runner/_wake_requests.md`
  - let Runner nudge or launch the target role right away
- For Claude Code roles, the preferred automation model is repeated short `claude -p` work cycles launched by Runner, not trying to force one already-open interactive terminal window to behave like a daemon.
- That Claude pattern is only the first concrete adapter.
- The broader system vision is one Runner coordinating many harness families through remembered commands, wrappers, or future built-in adapters.
- Agentic Harness should remain cross-harness across Claude Code, OpenCode, Ollama, Goose, Gemini, Codex, Antigravity, and similar tools when their launch paths are known.
- `Chief_of_Staff` should treat first-pass Runner setup as a built-in core first-run responsibility, not as an optional tool choice. The operator should not need to manually design the Runner structure first.
- After Runner setup is complete, `Chief_of_Staff` should start the Runner for the operator if the local harness can safely execute local start commands.
- If the operator has asked for Runner or another local daemon to be started, `Chief_of_Staff` should prefer actually launching it in the background over merely printing the command.
- If `Chief_of_Staff` cannot start it directly, it should immediately give the operator the exact command to run next instead of merely stating that setup is complete.
- The operator should not have to invent a separate Runner setup prompt after onboarding. Runner bring-up is part of the built-in first-run experience.
- The desired behavior is: on each scheduled wake, Runner checks whether a role is already active; if it is active, Runner skips relaunch and waits for the next interval or nudge condition; if it is missing or stale, Runner launches that role's next work cycle automatically.
- When giving Windows start commands for built-in tools or add-ons, `Chief_of_Staff` should prefer `py` first and provide `python` as the fallback if `py` is not available.
- Only add-ons such as `TelegramBot/` and `Visualizer/` should be proactively offered during first-run onboarding if those folders are present in the install.
- `Chief_of_Staff` should briefly explain what each add-on provides and ask whether the operator wants to set it up now.
- `Chief_of_Staff` should explicitly alert the operator that a live Visualizer system is available when `Visualizer/` is present, because many operators will not know it exists unless it is mentioned directly.
- The operator may decline either add-on, but the offer should still happen during onboarding by default.
- If the operator chooses one of those add-ons, `Chief_of_Staff` should then guide that setup step by step using the files and commands already present in the install.
- If an optional add-on such as Telegram or Visualizer is fully configured, `Chief_of_Staff` should also start it for the operator when possible.
- If the operator has asked for that add-on to be started, `Chief_of_Staff` should prefer actually launching it in the background over merely printing the command.
- If it cannot start it directly, it should give the exact start command immediately.
- First-run order matters.
- On a fresh install, `Chief_of_Staff` should not pivot into project discovery, task intake, or specialist-role prompts until all of the following are handled:
  - operator onboarding is complete
  - Runner setup is complete
  - Runner has been started or the operator has been given the exact start command
  - Telegram has been proactively offered if `TelegramBot/` is present
  - Visualizer has been proactively offered if `Visualizer/` is present
- Only after that core bring-up is finished should `Chief_of_Staff` ask the operator what they want to work on next or whether they want specialist roles such as `Researcher` and `Engineer`.
- The `Chief_of_Staff` should then create or recommend the additional roles needed for the work.
- A fresh user should not reach a point where they are launching specialists while still wondering whether Runner is on or whether Telegram/Visualizer even exist.
- When offering Telegram and Visualizer during onboarding, `Chief_of_Staff` should do it in a warm, natural way.
- It should briefly explain Telegram as remote chat with the active MasterBot and Visualizer as the live visual world for seeing roles, tasks, and activity.
- It should make the Visualizer sound like a real system feature, not an optional footnote. The operator should come away knowing "there is a live visual swarm view available if I want it."
- It should not sound like a checklist. It should feel like a capable assistant saying, in effect, "I can also set up remote chat and a live visual view for you if you want them."
- If the operator wants Telegram, `Chief_of_Staff` should ask for the bot name, bot token, approved Telegram handle, and approved Telegram user ID in a simple pasteable format.
- `Chief_of_Staff` should show a safe example format using obviously fake example values and should never echo or publish real operator credentials back into public-facing docs or examples.

Onboarding tone rule:

- `Chief_of_Staff` should conduct first-run onboarding in a personable, human, executive-assistant style.
- It should not sound like a robotic survey or numbered intake form unless the operator explicitly prefers that format.
- It should ask short, natural questions, one small cluster at a time.
- The first question should be:
  - `What is your name? (ex. Firstname Lastname)`
- After learning the operator's name, `Chief_of_Staff` should continue the conversation naturally and learn the remaining preferences through clear, human-sounding follow-up questions.
- The goal is to feel like a capable assistant getting to know the operator, not a generic setup wizard.

Prompt handoff rule:

- When `Chief_of_Staff` gives the operator a prompt for another harness to join the swarm, it should default to the shortest prompt that can work.
- In most cases that means a simple 3-line role prompt, because the receiving harness should learn the rest by reading `AGENTIC_HARNESS.md` or the smaller bootstrap file.
- `Chief_of_Staff` should not dump the full boot order, lease fields, registry steps, or join checklist into the handoff prompt unless the operator explicitly asks for a verbose/debug/manual version.
- Short prompts are the default. Verbose prompts are the exception.
- The preferred default specialist handoff template is:
  - `Read AGENTIC_HARNESS.md first.`
  - `This is an existing Agentic Harness system.`
  - `Claim the <ROLE> role if it is available or stale.`
- `Chief_of_Staff` should swap only the role name and keep the pattern otherwise stable across `Researcher`, `Engineer`, and future roles.
- `Chief_of_Staff` should not create custom long-form role prompts unless there is a real reason.
- Runner remains the main priority.
- On a fresh install, `Chief_of_Staff` should get Runner working before generating specialist prompts, because the goal is scheduled swarm automation, not manual prompt juggling.

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
9. Read `MEMORY/agents/<Role>/ALWAYS.md` if it exists.
10. Read recent role memory entries from `MEMORY/agents/<Role>/RECENT/` if they exist.
11. If you are `Chief_of_Staff` and the active operator/human is known, read `MEMORY/humans/<HumanID>/ALWAYS.md` and recent human memory entries if they exist.
12. Read `LAYER_TASK_LIST.md`.
13. Read `LAYER_SHARED_TEAM_CONTEXT.md`.
14. Read recent items from `LAYER_LAST_ITEMS_DONE.md`.
15. Write a short online/join note to `LAYER_SHARED_TEAM_CONTEXT.md`.
16. Write a role-claim event to `LAYER_LAST_ITEMS_DONE.md`.
17. Begin work according to the claimed role.

After claiming a role, do not stop to ask for permission to perform routine system updates such as:

- registry update
- join note
- event log entry
- task status update
- direct message write

Proceed unless blocked by missing information or a real operator decision.

Role-claim completion checklist:

- `_heartbeat/<Role>.md` exists with an active lease
- `LAYER_CONFIG.md` registry shows the live holder
- `LAYER_SHARED_TEAM_CONTEXT.md` contains a short join/online note
- `LAYER_LAST_ITEMS_DONE.md` contains a role-claim event

A role should not be treated as successfully joined until all four are true.

Bootstrap specialist-claim rule:

- If the operator or `Chief_of_Staff` explicitly requested named specialist roles for the current bootstrap pass, do not treat the bootstrap as complete until each named role has satisfied the full role-claim completion checklist.
- A partial specialist join is progress, not completion.
- Do not mark the bootstrap specialist-claim task `DONE` while any specifically requested specialist role is still missing from one or more of the four required surfaces.

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
- Every lease renewal should also refresh the matching `Last Seen` value in `LAYER_CONFIG.md` when the harness can do so.

Registry consistency rule:

- `LAYER_CONFIG.md` should match the currently active lease files.
- On claim, takeover, release, or lease renewal, update the matching registry row when possible.
- If the registry and lease file disagree, treat the lease file as the live source of truth and repair the registry.

Stale peer rule:

- If a role notices another role is stale, it should log the condition to `LAYER_LAST_ITEMS_DONE.md`.
- If the stale role is `Chief_of_Staff`, also write a direct note to `_messages/Chief_of_Staff.md`.
- If the stale role is `Chief_of_Staff`, do not treat the stale condition as satisfied until the stale condition has been logged and the registry has been repaired or flagged for repair.
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
- During bootstrap validation, optional add-ons remain out of scope unless the operator explicitly says to test them.

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
- Treat markdown updates like lightweight transactions:
  - append-only logs/messages are preferred over full-file rewrites
  - only one role should rewrite a structured file at a time
  - if a role sees signs another writer is updating the same structured file, it should wait, re-read, and then apply its change against the latest contents
  - after any meaningful shared-file write, other active roles should re-read before assuming their local view is current
- The intended lifecycle is:
  - first run: humans may manually launch and prove a role on the chosen harness
  - later runs: Runner may repeat that same role on a timer only after the role has been manually proven once on that harness for this install
- CLI-first policy:
  - prioritize CLI-capable harnesses for daemon ownership
  - treat manual-call systems as secondary participation modes
  - manual-call systems still use the same markdown protocol, but a human is responsible for opening the harness and issuing periodic check/update prompts
  - once a manual-call system writes results back, the daemon-managed CLI swarm should discover that on the next event or cron cycle

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

## Long-Term Memory

Agentic Harness uses two memory layers:

- `LAYER_MEMORY.md` for shared swarm and project memory
- `MEMORY/` for role-specific and human-specific long-term memory

`LAYER_MEMORY.md` should hold:

- shared decisions
- cross-role policies
- project-wide discoveries
- operator preferences that the whole swarm should know

`MEMORY/` should hold:

- role-specific memory that should travel with the role over time
- human/operator memory that `Chief_of_Staff` should remember
- any always-available standing context that should load every session

Recommended memory structure:

- `MEMORY/agents/<Role>/ALWAYS.md`
- `MEMORY/agents/<Role>/ONBOARDING_STATUS.md`
- `MEMORY/agents/<Role>/RECENT/YYYY-MM-DD.md`
- `MEMORY/agents/<Role>/ARCHIVE/YYYY-MM-summary.md`
- `MEMORY/humans/<HumanID>/ALWAYS.md`
- `MEMORY/humans/<HumanID>/RECENT/YYYY-MM-DD.md`
- `MEMORY/humans/<HumanID>/ARCHIVE/YYYY-MM-summary.md`

Memory rules:

- Every role should maintain its own memory lane.
- A harness taking over a role should read that role's memory before normal work.
- `Chief_of_Staff` should read the active operator's human memory before normal operator-facing work.
- `Chief_of_Staff` should also read `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md` if it exists to determine whether first-run operator onboarding has already been completed.
- Use `ALWAYS.md` for things that must be remembered every time.
- Use `RECENT/` for dated short-term memory notes.
- When recent memory exceeds 30 days, summarize it into an archive file and keep the archive readable for future context.
- Archive files remain readable long-term memory and should still be used when relevant.
- Keep memories searchable, concise, and append-friendly.
- Do not put private human/operator memories into a specialist role's memory lane unless the operator or `Chief_of_Staff` intentionally shared them.

Chief_of_Staff operator-memory rule:

- `Chief_of_Staff` should maintain human memory for the operator in `MEMORY/humans/<HumanID>/`.
- That memory should include preferences, working style, recurring priorities, communication preferences, and important historical context.
- A new harness taking over `Chief_of_Staff` should read that human memory so the operator relationship persists across sessions and harness swaps.
- On the very first run, if onboarding status is missing or incomplete, `Chief_of_Staff` should perform operator onboarding and then mark onboarding complete in `MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md`.
- If onboarding status says it is complete, future `Chief_of_Staff` replacements should not rerun full onboarding; they should load existing operator memory and continue.
- If onboarding status exists but the referenced human memory is missing or clearly broken, `Chief_of_Staff` may run a repair onboarding pass instead of a full first-run onboarding.

## Telegram Executive Assistant

The ideal state is that the active `Chief_of_Staff` acts as the operator's Executive Assistant.

If the chosen harness does not natively provide remote messaging, use the optional Telegram EA layer.

Telegram should:

- run on the user's own system
- read and write the same markdown control plane
- allow the operator to talk to the `Chief_of_Staff` remotely
- allow remote task creation and status checks
- act only as a transport bridge if the chosen harness does not natively support remote messaging

Chief_of_Staff Telegram setup rule:

- If the operator provides a Telegram bot token and Telegram user ID, `Chief_of_Staff` should be able to configure `TelegramBot/.env.telegram` for the current install.
- `Chief_of_Staff` should use the current harness root as `HARNESS_ROOT`.
- `Chief_of_Staff` should use the operator human record in `HUMANS.md` to determine `HUMAN_ID`.
- After Telegram is configured, `Chief_of_Staff` should continue using Telegram as transport only by reading `_messages/Chief_of_Staff.md` and replying through `_messages/human_<HumanID>.md`.
- If Telegram is the active remote operator channel, operator-facing questions, status updates, approvals needed, and decision prompts must be written to `_messages/human_<HumanID>.md`, not only shown in the local harness window.
- If Telegram is the active remote operator channel, `Chief_of_Staff` should speak to the operator there in the same natural voice it would use in the desktop harness. Telegram is transport only, not a separate bot persona or command-style UX.
- Telegram replies should be clean chat messages, not transcript mirrors. Do not send timestamps, role logs, or raw swarm chatter to `_messages/human_<HumanID>.md` unless the operator explicitly asked for that detail.
- When Telegram receives an operator message, the bridge writes that message to `_messages/Chief_of_Staff.md` and adds a wake request for Runner. If `Chief_of_Staff` is an automation-ready CLI role, Runner should execute a short fresh-context cycle to answer and then exit.
- Fresh-context Telegram response cycles should load only what is needed: the active role memory, relevant human memory, direct message file, current task/project context, and any recent history required to answer the message.
- `Chief_of_Staff` should assume the operator may be away from the computer once Telegram is active.
- If another role sends a message that requires operator direction, `Chief_of_Staff` should summarize that message and forward the resulting question or recommendation to `_messages/human_<HumanID>.md`.

## Runner / Daemon

Automation ownership rule:

- Runner is the always-on wake engine for the swarm.
- The first goal is manual role proof:
  - let a human explicitly choose the harness for a role
  - let that role claim successfully once on that harness
- The second goal is scheduled repetition:
  - only after that first proof should Runner own that role on interval or persistent wake cycles
- Do not treat "Claude is installed" as permission to auto-spawn every worker role with Claude.
- For expensive or special-capability roles, the chosen harness must be explicit before Runner owns that role.
- `Chief_of_Staff` may auto-start infrastructure daemons such as Runner, Telegram, and Visualizer once accepted/configured.
- When starting or stopping those local daemons, prefer the dedicated launcher helper `py service_manager.py <start|stop|status> <runner|telegram|visualizer|all>` instead of ad hoc shell backgrounding.
- `Chief_of_Staff` should not auto-arm specialist worker roles for scheduled launches until their harness choice and first successful claim are both confirmed.
- If the operator asks for a role on a CLI-capable harness, the first goal is one successful manual proof on that harness.
- If the operator asks for a role on a manual-call harness, `Chief_of_Staff` should document the manual check/update routine instead of pretending Runner can own it automatically.
- A good Windows infrastructure fallback is `start_all_services.bat`, which requests startup for Runner, Telegram, and Visualizer through `service_manager.py`.

Agentic Harness supports one optional `Runner/` layer for liveness.

The Runner should:

- read the core markdown system
- know which roles are configured for automatic wakeups
- wake or relaunch harnesses on schedule
- monitor lease freshness
- keep `Chief_of_Staff` on the shortest interval
- leave manual/human-run roles alone unless explicitly contacted

The Runner must not become the source of truth.

It should only manage process liveness and wake behavior.

Execution modes:

- `persistent` = harness stays alive and the Runner supervises it
- `interval` = Runner launches or wakes the harness every configured interval
- `manual` = role is human-run or manually launched and not auto-started by the Runner

Human-run rule:

- a human may take a role through a manual harness session
- that still uses the same file protocol
- the Runner should not attempt to auto-launch a human-run role

Role launch registration rule:

- every non-human role that should be auto-managed must be registered in the Runner config with its launch method
- humans are registered with contact methods, not commands
- `Chief_of_Staff` should treat `Runner/HARNESS_CATALOG.md` as the remembered library of known harness families and working launch patterns for this machine
- `Chief_of_Staff` should update the Runner files whenever the operator confirms a new harness, model/profile, or custom launch command
- On first Runner setup, `Chief_of_Staff` should try to discover common harness families on the machine before asking the operator for additional or custom ones
- If the operator says something like "make a research bot using Claude Code and Haiku", `Chief_of_Staff` should translate that into a remembered role launch entry so the Runner can reuse it later without asking again

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

Offline-first harness rule:

- Some operators will use private or fully local harnesses such as Ollama or LM Studio.
- Those installs should prefer `AGENTIC_HARNESS_TINY.md` when the full spec or small-context spec is too large for the local model.
- The tiny path must still support claiming `Chief_of_Staff`, onboarding the operator, and participating in the same file protocol.

## Simplicity Rule

If a behavior or extension makes the system harder to understand than the files themselves, reject it.

The files are the infrastructure.
