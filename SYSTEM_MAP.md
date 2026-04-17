# SYSTEM MAP

Agentic Harness has five conceptual layers.

## 1. Core

This is the source of truth.

Files:

- `AGENTIC_HARNESS.md`
- `PROJECT.md`
- `LAYER_ACCESS.md`
- `LAYER_CONFIG.md`
- `LAYER_MEMORY.md`
- `LAYER_TASK_LIST.md`
- `LAYER_SHARED_TEAM_CONTEXT.md`
- `LAYER_LAST_ITEMS_DONE.md`
- `ROLES.md`
- `HUMANS.md`

Supporting folders:

- `_heartbeat/`
- `_messages/`
- `_archive/`
- `MEMORY/`
- `SKILLS/`

Purpose:

- coordination
- memory
- leases
- messaging
- task routing

## 2. Projects

This is the actual work.

Folder:

- `Projects/`

Purpose:

- project-specific files
- project tasks
- artifacts
- working outputs

Rule:

- projects should not become the control plane
- the control plane should not be mixed into every project folder

## 3. Runner

This is the optional liveness layer.

Folder:

- `Runner/`

Purpose:

- wake roles
- relaunch harnesses
- monitor leases
- keep the swarm feeling alive

Rule:

- Runner is not the source of truth
- it only manages wake/relaunch behavior

## 4. Telegram

This is the optional transport layer.

Folder:

- `TelegramBot/`

Purpose:

- remote messaging with `Chief_of_Staff`

Rule:

- Telegram is transport only
- `Chief_of_Staff` remains the orchestrator

## 5. Visualizer

This is the optional visibility layer.

Folder:

- `Visualizer/`

Purpose:

- show the swarm in 2D / 3D / VR
- visualize role state and tasks

Rule:

- Visualizer is not the source of truth
- it reads and writes the same markdown system

## In One Sentence

Core is the brain, Projects are the work, Runner is the wake engine, Telegram is remote chat, and Visualizer is the live view.
