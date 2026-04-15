# Phase 3 Markdown Contract

## Purpose

This document defines the exact markdown file formats that Agentic Harness should use for:

- operator input
- MasterBot responses
- master task management
- master board summaries
- system status summaries

Phase 2 should write files in ways that are already compatible with this contract.

Phase 3 should use this document as the source of truth when building:

- dashboard views
- operator input helpers
- project/task rendering
- later worker-bot parsing

The goal is to keep the system:

- simple
- durable
- markdown-native
- easy for bots to read
- easy for humans to inspect
- easy for UIs to parse

---

## Design Rules

1. Markdown files must remain readable without any UI.
2. Files should be append-friendly where possible.
3. Files should use stable section headers.
4. Avoid hidden metadata formats unless absolutely necessary.
5. If machine-readable markers are needed, keep them small and obvious.
6. The operator should be able to edit these files directly without breaking the system.
7. Bots should be able to understand what to do by reading plain sections.

---

## 1. Operator Input Contract

### File

`MasterBot/workspace/OPERATOR_NOTES.md`

### Purpose

The Human Operator writes requests, goals, clarifications, and follow-ups here.

MasterBot reads new entries, processes them once, and records the result elsewhere.

### Format

```md
# Operator Notes

## Entry
Timestamp: 2026-04-09T14:00:00-04:00
Operator: Solomon
Status: new

Please create a new project for my Second Brain and define the first three setup tasks.

## Entry
Timestamp: 2026-04-09T14:10:00-04:00
Operator: Solomon
Status: new

Use ResearchBot for anything related to market analysis.
```

### Rules

- Each input is a separate `## Entry` block.
- `Status` begins as `new`.
- MasterBot should not rewrite or delete operator text.
- MasterBot may optionally change `Status: new` to `Status: processed` only if that proves stable in practice.
- If status mutation is avoided, idempotency should be tracked in runtime state.

### Parsing rule

MasterBot should process entries in file order and only once.

Recommended idempotency key:

- hash of the full entry block
or
- timestamp + content hash

---

## 2. Master Response Contract

### File

`MasterBot/workspace/TEAM_COMMUNICATION.md`

### Purpose

This is the primary append-only communication log for MasterBot and later for worker bots.

During Phase 2 and early Phase 3, MasterBot is the main writer.

### Format

```md
# Team Communication

## Message
Timestamp: 2026-04-09T14:01:10-04:00
Sender: MasterBot
Type: operator_response
Project: none
Task: none

I created a new project structure for your Second Brain and added three initial setup tasks to `MASTER_TASKS.md`.

## Message
Timestamp: 2026-04-09T14:02:00-04:00
Sender: MasterBot
Type: coordination_note
Project: ExampleProject
Task: task-secondbrain-001

This work should later be routed to the best available research-oriented bot once worker automation is enabled.
```

### Allowed `Type` values

- `operator_response`
- `coordination_note`
- `task_claim`
- `task_handoff`
- `task_complete`
- `blocker`
- `system_note`

### Rules

- Append only.
- Do not rewrite past messages.
- Keep messages short and focused.
- Use `Project: none` and `Task: none` if not applicable.
- Worker bots will later use the same structure.

---

## 3. Master Task Contract

### File

`MasterBot/workspace/MASTER_TASKS.md`

### Purpose

The top-level durable task list for the entire organization.

This is the main planning surface for MasterBot.

### Format

```md
# Master Tasks

## Active

### Task
ID: task-secondbrain-001
Title: Create Second Brain project structure
Project: ExampleProject
Status: active
Priority: high
Preferred Bot: none
Owner: MasterBot

Create the initial project structure and prepare the first three setup tasks.

### Task
ID: task-secondbrain-002
Title: Define first three setup tasks
Project: ExampleProject
Status: active
Priority: high
Preferred Bot: none
Owner: MasterBot

Define the first three high-value setup tasks for the Second Brain project.

## Blocked

### Task
ID: task-secondbrain-003
Title: Connect Obsidian vault path
Project: ExampleProject
Status: blocked
Priority: medium
Preferred Bot: none
Owner: none

Waiting for the Human Operator to provide the Obsidian vault folder path.

## Done

### Task
ID: task-master-001
Title: Initialize MasterBot filesystem
Project: none
Status: done
Priority: high
Preferred Bot: none
Owner: MasterBot

The MasterBot filesystem was initialized successfully.
```

### Rules

- Organize tasks by section:
  - `## Active`
  - `## Blocked`
  - `## Done`
- Each task uses a `### Task` block.
- Task IDs must be stable and unique.
- `Owner` may be:
  - `MasterBot`
  - a worker bot name later
  - `none`
- `Preferred Bot` is informational and may reflect operator preference.

### Task ID convention

Use:

- `task-<project>-<sequence>`

Examples:

- `task-secondbrain-001`
- `task-sales-004`
- `task-master-002`

Keep the scheme simple and predictable.

---

## 4. Master Board Contract

### File

`MasterBot/workspace/MASTER_BOARD.md`

### Purpose

A fast human-readable operating summary for the Human Operator.

This is not a log.
It is a snapshot.

### Format

```md
# Master Board

## Top Priorities
- Create Second Brain project structure
- Define first three setup tasks
- Prepare for first worker bot integration

## Active Projects
- ExampleProject

## Recent Completions
- Initialized MasterBot filesystem
- Updated master task list

## Current Blockers
- Waiting on Obsidian vault path from operator

## Live Bots
- MasterBot: online
- ExampleWorker: defined

## Last Updated
2026-04-09T14:05:00-04:00
```

### Rules

- This file is rewritten as a current snapshot.
- Keep it short.
- Prefer bullet lists over paragraphs.
- Only include the most important information.
- `Last Updated` must always be present.

---

## 5. System Status Contract

### File

`System/SYSTEM_STATUS.md`

### Purpose

A lightweight overall system health summary.

### Format

```md
# System Status

## Runtime
- MasterBot: online
- Heartbeat Interval: 300 seconds
- Lease State: active

## Provider
- Current Provider: openai
- Current Model: PLACEHOLDER
- Degraded Mode Allowed: true

## Workspace
- Active Projects: 1
- Known Bots: 2
- Backups Folder Present: yes

## Last Updated
2026-04-09T14:05:00-04:00
```

### Rules

- Rewrite as a snapshot.
- Keep it operational, not conversational.
- Reflect current runtime truth only.

---

## 6. Live Bots Contract

### File

`System/LIVE_BOTS.md`

### Purpose

A human-readable summary of all known bots and their current live status.

### Format

```md
# Live Bots

## Bot
Name: MasterBot
Role: master
Harness: provider-service
Model: PLACEHOLDER
Status: online
Last Heartbeat: 2026-04-09T14:05:00-04:00
Folder: MasterBot

## Bot
Name: ExampleWorker
Role: worker
Harness: claude-code
Model: PLACEHOLDER
Status: defined
Last Heartbeat: none
Folder: Bots/ExampleWorker
```

### Rules

- Use one `## Bot` block per bot.
- Rewrite the file as current truth.
- Keep fields stable for later parsing.

---

## 7. Status Contract

### File

`MasterBot/bot_definition/Status.md`

### Purpose

Human-readable current state of MasterBot.

### Format

```md
# Status
Current State: active
Current Focus: Processing operator request
Blockers: none
Last Meaningful Action: Added tasks to MASTER_TASKS.md
Last Updated: 2026-04-09T14:03:00-04:00
```

### Rules

- Keep it compact.
- Rewrite the full snapshot each cycle or on meaningful state change.
- Avoid logs here; use communication files for logs.

---

## 8. Heartbeat Contract

### File

`MasterBot/bot_definition/Heartbeat.md`

### Purpose

Human-readable liveness record.

### Format

```md
# Heartbeat
Last Updated: 2026-04-09T14:05:00-04:00
Mode: active
Current Activity: synchronizing state
Current Focus: ExampleProject
```

### Rules

- Rewrite as a snapshot every heartbeat cycle.
- Keep the content short and stable.

---

## 9. Lease Contract

### File

`MasterBot/bot_definition/Lease.json`

### Purpose

Prevent duplicate daemon runs.

### Format

```json
{
  "bot_id": "masterbot",
  "lease_owner": "HOSTNAME:PID",
  "pid": 12345,
  "started_at": "2026-04-09T14:00:00-04:00",
  "renewed_at": "2026-04-09T14:05:00-04:00",
  "expires_at": "2026-04-09T14:10:00-04:00",
  "current_activity": "active"
}
```

### Rules

- JSON only.
- Rewrite on each lease renewal.
- If a lease is stale, the daemon may recover ownership.

---

## 10. Runtime Profiles

### ProviderProfile.json

Recommended structure:

```json
{
  "provider": "PLACEHOLDER",
  "model": "PLACEHOLDER",
  "api_base": "",
  "api_key_env": "",
  "enabled": false
}
```

### RuntimeProfile.json

Recommended structure:

```json
{
  "heartbeat_seconds": 300,
  "lease_seconds": 600,
  "enabled": true,
  "degraded_mode_allowed": true,
  "last_processed_operator_note": ""
}
```

---

## Phase 3 Acceptance Criteria

Phase 3 should be considered ready when:

1. MasterBot daemon writes files in exactly these formats.
2. Operator notes can be added and processed repeatedly without duplication.
3. `TEAM_COMMUNICATION.md` becomes the durable response log.
4. `MASTER_TASKS.md` and `MASTER_BOARD.md` remain human-readable after multiple cycles.
5. `SYSTEM_STATUS.md` and `LIVE_BOTS.md` remain current snapshots.
6. The dashboard can be built as a thin view over these files without inventing a separate state model.

---

## Transfer Prompt

Use this prompt for any builder implementing Phase 3:

> Read `AGENTIC_HARNESS_RESTART_TRANSFER.md` and `PHASE_3_MARKDOWN_CONTRACT.md` first. Treat them as the source of truth. Implement only the markdown reading and writing behavior described there. Keep the files simple, stable, append-friendly where specified, and easy for both humans and bots to read.
