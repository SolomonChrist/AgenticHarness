# Phase 4 Worker Contract

## Purpose

This document defines the first real worker bot behavior contract for Agentic Harness.

Phase 4 is the first point where a non-Master worker bot should:

- read project files
- determine whether work is available
- claim tasks
- perform work
- update markdown state
- collaborate with MasterBot through files

This contract is intentionally narrow.

It applies first to:

- `claude-code`

Later harnesses such as:

- `opencode`
- `openclaw`
- `custom`

should follow the same bot-facing file and state model.

The goal is to make worker bots simple, durable, portable, and easy to reason about.

---

## Phase 4 Scope

Phase 4 should implement only:

- one real worker bot contract
- one claiming model
- one update model
- one artifact recording model
- one handoff/help request model

It should not yet implement:

- full swarm auctions
- complex scoring engines
- full multi-harness parity
- advanced dashboard behavior

This phase exists to make one truthful worker behavior work end to end.

---

## Worker Role In The System

The worker bot is:

- not the operator-facing brain
- not the system owner
- not the controller of the organization

The worker bot is:

- a specialist or generalist contributor
- a project-facing collaborator
- a markdown-native actor
- a real harness-native runtime

MasterBot:

- publishes tasks
- interprets operator requests
- watches progress
- summarizes outcomes

Worker bots:

- inspect available work
- evaluate fit
- claim work
- complete work
- ask for help or hand off when needed

---

## Worker Filesystem Contract

Each worker has its own folder.

### Worker bot-owned files

```text
<WorkerBotFolder>/
  bot_definition/
    Soul.md
    Identity.md
    Memory.md
    Learnings.md
    Skills.md
    RolePolicies.md
    Status.md
    Heartbeat.md
    Lease.json
    HarnessProfile.json
    RuntimeProfile.json
  workspace/
    WORKING_NOTES.md
    TASKS.md
    TEAM_COMMUNICATION.md
    ARTIFACTS.md
```

### Project-owned files

Worker bots also read and update project files:

```text
Projects/<ProjectName>/
  KANBAN.md
  NEXT_ACTION.md
  NOTES.md
  ARTIFACTS.md
  DECISIONS.md
  TEAM_COMMUNICATION.md
  HUMANS.md
  PROJECT_POLICIES.md
  RESEARCH.md
  CONTEXT.md
```

### Important rule

All bot-specific items live with the bot.
All project-specific items live with the project.

Do not mix them.

---

## Worker Startup Rule

When a worker bot wakes up on its heartbeat cycle, it should:

1. acquire or verify its lease
2. update its heartbeat
3. read its bot definition
4. inspect relevant project and communication files
5. determine whether there is work it should take
6. claim or continue work if appropriate
7. update files
8. exit if no further action is needed

This should work whether the worker is:

- launched by scheduler
- launched manually
- launched by a harness-specific helper

---

## Minimum Read Set

On each cycle, the worker should read:

### Bot files

1. `bot_definition/Identity.md`
2. `bot_definition/Soul.md`
3. `bot_definition/RolePolicies.md`
4. `bot_definition/Skills.md`
5. `bot_definition/Status.md`
6. `bot_definition/RuntimeProfile.json`
7. `bot_definition/HarnessProfile.json`

### Project files

For each relevant project:

1. `KANBAN.md`
2. `NEXT_ACTION.md`
3. `TEAM_COMMUNICATION.md`
4. `PROJECT_POLICIES.md`
5. `CONTEXT.md`
6. `ARTIFACTS.md`

### Optional reads

If needed:

7. `NOTES.md`
8. `RESEARCH.md`
9. `DECISIONS.md`

---

## Minimum Write Set

Each worker must be able to write:

### Bot files

1. `bot_definition/Status.md`
2. `bot_definition/Heartbeat.md`
3. `bot_definition/Lease.json`
4. `workspace/WORKING_NOTES.md`
5. `workspace/TASKS.md`

### Project files

6. `Projects/<Project>/TEAM_COMMUNICATION.md`
7. `Projects/<Project>/ARTIFACTS.md`
8. `Projects/<Project>/KANBAN.md`

If needed:

9. `Projects/<Project>/NOTES.md`
10. `Projects/<Project>/DECISIONS.md`

---

## Worker Self-Knowledge

Each worker bot must maintain explicit awareness of:

- its harness
- its model
- its tools
- its skills
- its strengths
- its weaknesses
- its preferred project types
- its movement style

This self-knowledge should come from:

- `Identity.md`
- `Skills.md`
- `HarnessProfile.json`
- `RuntimeProfile.json`

Without this, task fit decisions become weak and inconsistent.

---

## Claiming Model

Phase 4 introduces simple worker claiming.

### Claim rule

A worker should claim a task only if:

1. the task is visible in project state
2. the task is not already actively owned
3. the worker is a reasonable fit
4. the worker is not already busy with another incompatible task

### Worker fit criteria

The worker should evaluate:

- harness suitability
- model suitability
- required tools
- required skills
- domain fit
- current availability

### Human and Master priority

The worker must defer to:

1. explicit Human Operator preference
2. explicit MasterBot assignment

These outrank self-nomination.

---

## Claim Recording Contract

When a worker claims a task, it must record that claim in:

### 1. Project `TEAM_COMMUNICATION.md`

Append:

```md
## Message
Timestamp: 2026-04-09T15:00:00-04:00
Sender: ExampleWorker
Type: task_claim
Project: ExampleProject
Task: task-example-001

I am claiming this task because my current harness, tools, and skills are a good fit.
```

### 2. Project `KANBAN.md`

Move or write the task under the active/in-progress section according to the project’s kanban format.

### 3. Worker `Status.md`

Update current state to:

- active
- current focus = task id or task title

### 4. Worker `workspace/TASKS.md`

Record the active worker-local task list.

---

## Working Notes Contract

### File

`workspace/WORKING_NOTES.md`

### Purpose

Internal scratchpad for the worker’s current thinking and work progress.

### Format

```md
# Working Notes

## Session
Timestamp: 2026-04-09T15:05:00-04:00
Project: ExampleProject
Task: task-example-001

- Reviewed current project context.
- Confirmed the task fits my available tools and skills.
- Starting implementation draft.
```

### Rules

- append by session
- keep concise
- do not treat as final deliverable storage

---

## Artifact Recording Contract

### File

`Projects/<Project>/ARTIFACTS.md`

### Purpose

Durable index of outputs created by the worker.

### Format

```md
# Artifacts

## Artifact
Timestamp: 2026-04-09T15:20:00-04:00
Task: task-example-001
Created By: ExampleWorker
Type: markdown
Path: Projects/ExampleProject/output/proposal.md

Created first draft proposal for the project.
```

### Rules

- append only
- one `## Artifact` block per meaningful output
- path should be workspace-relative where possible

---

## Completion Contract

When a worker completes a task, it must:

1. append a completion note to project `TEAM_COMMUNICATION.md`
2. update `ARTIFACTS.md` if there are durable outputs
3. update project `KANBAN.md`
4. update worker `Status.md`
5. optionally append a concise learning to `Learnings.md` if something reusable was discovered

### Completion message example

```md
## Message
Timestamp: 2026-04-09T15:30:00-04:00
Sender: ExampleWorker
Type: task_complete
Project: ExampleProject
Task: task-example-001

Task complete. Output has been recorded in `ARTIFACTS.md`.
```

---

## Help Request / Handoff Contract

If a worker cannot finish alone, it should not silently fail.

It should request support.

### Help request format

Append to project `TEAM_COMMUNICATION.md`:

```md
## Message
Timestamp: 2026-04-09T15:40:00-04:00
Sender: ExampleWorker
Type: task_handoff
Project: ExampleProject
Task: task-example-001

I completed the research stage, but this task now needs a stronger writing-oriented bot for final report drafting.
```

### Rules

- describe what was done
- describe what remains
- describe what kind of bot would be a better fit

This will later support multi-bot collaboration.

---

## Worker Status Contract

### File

`bot_definition/Status.md`

### Format

```md
# Status
Current State: active
Current Focus: task-example-001
Blockers: none
Last Meaningful Action: Claimed task-example-001
Last Updated: 2026-04-09T15:05:00-04:00
```

### States

Allowed initial values:

- `idle`
- `active`
- `blocked`
- `waiting`
- `offline`

Keep the state set small and clear.

---

## Worker Heartbeat Contract

### File

`bot_definition/Heartbeat.md`

### Format

```md
# Heartbeat
Last Updated: 2026-04-09T15:05:00-04:00
Mode: active
Current Activity: evaluating project task
Current Focus: ExampleProject
```

### Rules

- rewrite as a snapshot
- update every run

---

## Worker Lease Contract

### File

`bot_definition/Lease.json`

### Format

```json
{
  "bot_id": "exampleworker",
  "lease_owner": "HOSTNAME:PID",
  "pid": 12345,
  "started_at": "2026-04-09T15:00:00-04:00",
  "renewed_at": "2026-04-09T15:05:00-04:00",
  "expires_at": "2026-04-09T15:10:00-04:00",
  "current_activity": "active"
}
```

### Rules

- use the same lease semantics as MasterBot
- stale lease may be recovered
- fresh lease owned by another process means this run exits

---

## Phase 4 Worker Run Loop

Recommended default loop:

1. acquire lease
2. update heartbeat
3. load self-definition
4. inspect project state
5. determine whether to claim or continue work
6. update working notes and status
7. write outputs
8. update project state
9. exit

This is a scheduled wake-up model, not a permanently open chat dependency.

---

## Claude Code Specific Guidance

Claude Code is the first worker harness to support.

The goal is:

- do real work from files
- avoid presenting the system as a hidden control harness

Claude should be treated as:

- a collaborator working from a local folder
- reading project files and bot definition files
- updating markdown state as it works

Not:

- a bot pulling from a hidden inbox/outbox command bus

---

## Phase 4 Acceptance Criteria

Phase 4 should be considered ready when:

1. a Claude worker can read its bot definition and project files
2. it can determine task fit
3. it can claim a task visibly in markdown
4. it can update worker status and heartbeat
5. it can write working notes
6. it can write artifacts
7. it can mark completion
8. it can request help or hand off

No advanced swarm logic is required yet.
Only truthful single-worker behavior.

---

## Transfer Prompt

Use this prompt for any builder implementing Phase 4:

> Read `AGENTIC_HARNESS_RESTART_TRANSFER.md`, `PHASE_3_MARKDOWN_CONTRACT.md`, and `PHASE_4_WORKER_CONTRACT.md` first. Treat them as the source of truth. Implement only the first real worker bot contract, starting with Claude Code. Keep the worker markdown-native, portable, and easy to understand. Do not reintroduce explicit inbox/outbox command-and-control framing.
