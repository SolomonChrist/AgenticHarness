# Bot Builder Contract

## Purpose

This document defines the minimum production contract for creating and integrating bots in Agentic Harness.

The bot builder must allow the operator to:

- create a new bot in any folder
- initialize the canonical bot_definition and workspace structure
- configure the bot identity and runtime basics
- integrate an existing folder into the system without destroying local work

This contract is intentionally simple.

The goal is to make bot creation and reuse reliable today.

---

## Scope

The bot builder must support:

1. creating a new worker bot
2. integrating an existing bot folder
3. generating canonical bot files
4. registering the bot in system state
5. preserving operator ownership

It should not yet require:

- fancy UI
- advanced multi-bot orchestration
- every harness-specific optimization

Phase 1 production target:

- simple command-line builder is acceptable
- dashboard form can come later

---

## Core Principle

A bot is not its provider or harness.

A bot is:

- its identity
- its soul
- its memory
- its skills
- its policies
- its status
- its relationships to projects and other bots

So the bot builder must initialize the durable bot definition, not merely a runtime command.

---

## Supported Harnesses

For the initial production build, the builder must support exactly:

- `claude-code`
- `opencode`
- `openclaw`
- `custom`

Support may be minimal for some harnesses, but the canonical bot structure must be consistent across all of them.

---

## Modes

### 1. Create New Bot

Creates a new folder and initializes the bot there.

### 2. Integrate Existing Bot

Takes an existing folder and adds the canonical `bot_definition/` and `workspace/` structure without destroying unrelated work.

This mode must be careful and non-destructive.

---

## Required Inputs

The bot builder must collect or accept:

- `bot_name`
- `role`
- `harness_type`
- `target_folder`
- `movement_style`
- `provider` optional
- `model` optional
- `entry_command` optional

### Optional inputs

- `personality`
- `core_strengths`
- `core_weaknesses`
- `preferred_projects`
- `skills_seed`

If optional values are missing, use simple placeholders.

---

## Required Output Structure

For every bot, the builder must ensure:

```text
<BotFolder>/
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

This is the minimum required worker bot scaffold.

---

## File Content Rules

### Soul.md

Purpose:
- persistent core essence of the bot

Minimum structure:

```md
# Soul
Core essence and enduring purpose of this bot.

## Core Drive
- Placeholder

## Commitments
- Work clearly
- Preserve continuity
- Update files faithfully
```

### Identity.md

Purpose:
- stable bot identity

Minimum structure:

```md
# Identity
Formal identity, role, and movement style.

Name: ExampleBot
Role: specialist
Movement Style: calm
Harness: claude-code
```

### Memory.md

Purpose:
- durable operator- and project-relevant memory

### Learnings.md

Purpose:
- append reusable lessons

### Skills.md

Purpose:
- durable skill inventory

Minimum structure:

```md
# Skills
Specific capabilities and learned strengths.

## Core Skills
- Placeholder

## Tool Access
- Placeholder
```

### RolePolicies.md

Purpose:
- bot-specific operating constraints

### Status.md

Must match the status contract pattern:

```md
# Status
Current State: idle
Current Focus: none
Blockers: none
Last Meaningful Action: initialized
Last Updated: none
```

### Heartbeat.md

Must match the heartbeat contract pattern:

```md
# Heartbeat
Last Updated: none
Mode: inactive
Current Activity: idle
Current Focus: none
```

### Lease.json

Initialize as:

```json
{}
```

### HarnessProfile.json

Minimum structure:

```json
{
  "harness": "claude-code",
  "entry_command": "",
  "provider": "",
  "model": "",
  "enabled": true
}
```

### RuntimeProfile.json

Minimum structure:

```json
{
  "heartbeat_seconds": 300,
  "lease_seconds": 600,
  "enabled": true,
  "degraded_mode_allowed": true
}
```

---

## Workspace File Rules

### WORKING_NOTES.md

Internal working scratchpad for the bot.

### TASKS.md

Bot-local task view or currently assigned items.

### TEAM_COMMUNICATION.md

Bot-local communication context if needed.

### ARTIFACTS.md

Bot-local index of outputs created by this bot.

These files may remain simple initially, but they must exist.

---

## Non-Destructive Integration Rules

When integrating an existing folder:

- never delete unrelated files
- never overwrite existing bot_definition files unless explicitly requested
- create missing files only
- update existing files only if the operator explicitly allows it later

This is critical for operator trust.

---

## Registration Rules

The bot builder must also update system visibility.

At minimum:

- the new bot folder must be visible to `LIVE_BOTS.md` scanning
- the bot should be discoverable by MasterBot through folder structure alone

No separate hidden registry is required if filesystem discovery works reliably.

---

## Builder Behaviors

### Create New Bot

1. resolve target folder
2. create the bot folder if missing
3. create `bot_definition/`
4. create `workspace/`
5. write canonical templates
6. preserve placeholders where operator values are not known

### Integrate Existing Bot

1. resolve target folder
2. check for existing contents
3. create `bot_definition/` if missing
4. create `workspace/` if missing
5. create only missing canonical files
6. do not overwrite unrelated content

---

## Acceptance Criteria

The bot builder is ready when:

1. a new bot can be created into any chosen folder
2. an existing bot folder can be integrated without destructive changes
3. all canonical files are generated
4. identity fields include movement style
5. harness type and runtime basics are recorded
6. MasterBot can discover the bot through the filesystem
7. the resulting folder is portable and backupable

---

## Transfer Prompt

Use this prompt for any builder implementing bot creation:

> Read `AGENTIC_HARNESS_RESTART_TRANSFER.md`, `PHASE_3_MARKDOWN_CONTRACT.md`, `PHASE_4_WORKER_CONTRACT.md`, and `BOT_BUILDER_CONTRACT.md` first. Implement a simple bot builder that can create new worker bots or integrate existing bot folders without destructive changes. Keep the generated structure canonical, durable, and easy to understand.
