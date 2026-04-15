# FTUE Onboarding Contract

## Purpose

This file defines the first-time user experience for Agentic Harness.

The onboarding must live inside the system itself, not in external documentation.
The goal is that a fresh GitHub user can install the framework, launch it, and be guided through creating a real MasterBot and first workspace without reading a manual.

This contract is binding for future Dashboard and Telegram onboarding work.

## Core Principles

- The system must teach through action, not prose.
- The user should configure their first real bot by making choices inside the app.
- The onboarding should write the real workspace files the system will continue using.
- The onboarding must keep the architecture visible and simple:
  - bots own bot files
  - projects own project files
  - the system owns global files
- The onboarding must not seed personal bots into the repo.
- The onboarding must use generic examples only when the user asks for them.

## FTUE Entry Points

The first-time user experience must be reachable from all future frontends:

- Dashboard
- Telegram
- CLI bootstrap flow

All entry points must drive the same underlying setup logic and write to the same workspace files.

## Required First-Run State Detection

The system is considered "not yet onboarded" if any of the following are true:

- `MasterBot/bot_definition/Identity.md` is missing
- `MasterBot/bot_definition/Soul.md` is missing
- `MasterBot/bot_definition/ProviderProfile.json` is missing
- `MasterBot/bot_definition/RuntimeProfile.json` is missing
- `System/SYSTEM_STATUS.md` is missing
- `MasterBot/workspace/OPERATOR_NOTES.md` does not contain a completed onboarding marker

If the workspace is not onboarded, the user must be routed into FTUE instead of dropped into an empty interface.

## Onboarding Goals

The onboarding must help the user do five things:

1. choose or confirm a workspace
2. define the MasterBot identity
3. choose the first provider
4. create the first project or skip it
5. understand how to create the first worker bot

The onboarding ends only when the workspace is ready for real use.

## FTUE Flow

### Step 1: Welcome and System Shape

The system should show a short interactive orientation:

- what Agentic Harness is
- that the bot is the files the user owns
- that providers and harnesses are replaceable engines
- that the system will guide them through creating their MasterBot

Do not show a long tutorial wall.

The user should see only:

- what will be created
- what they will decide now
- what they can change later

### Step 2: MasterBot Basics

Collect:

- MasterBot name
- MasterBot role label
- movement style
- short purpose

Default suggestions:

- name: `MasterBot`
- role label: `Chief of Staff`
- movement style: `calm`
- short purpose: `Coordinate work, protect operator time, and keep projects moving.`

These values must write into:

- `MasterBot/bot_definition/Identity.md`
- `MasterBot/bot_definition/Soul.md`

### Step 3: Provider Setup

Let the user choose:

- OpenAI
- LM Studio
- configure later

If OpenAI is chosen:

- ask for or point the user to `OPENAI_API_KEY`
- write `ProviderProfile.json` with `provider: openai`

If LM Studio is chosen:

- ask for local base URL
- write `ProviderProfile.json` with `provider: lmstudio`
- write `api_base`

If configure later is chosen:

- write placeholder provider values
- do not block the rest of onboarding
- clearly mark the system as not ready to run until a provider is configured

### Step 4: First Project

Offer:

- create first project now
- skip for now

If the user creates a project:

Collect:

- project name
- short purpose
- first next action

Then create the canonical project folder and write:

- `CONTEXT.md`
- `NEXT_ACTION.md`
- `TEAM_COMMUNICATION.md`
- `ARTIFACTS.md`
- `KANBAN.md`

If skipped:

- leave `Projects/` empty or with generic example content only if examples were explicitly requested

### Step 5: First Worker Guidance

The user should not be forced to create a worker yet.

But the system must offer:

- create first worker now
- do it later

If the user chooses to create one, FTUE should call the same bot-builder logic used everywhere else.

Collect:

- bot name
- role
- harness
- provider
- model
- movement style

This must create a real worker bot folder, not a fake tutorial artifact.

### Step 6: Ready State

At the end, show a single clear "you are ready" view with:

- MasterBot name
- active provider
- workspace path
- current project count
- current bot count
- next recommended action

The next recommended action should be one of:

- start MasterBot
- create first project
- create first worker
- configure provider

## Files FTUE Must Write

### MasterBot

- `MasterBot/bot_definition/Identity.md`
- `MasterBot/bot_definition/Soul.md`
- `MasterBot/bot_definition/ProviderProfile.json`
- `MasterBot/bot_definition/RuntimeProfile.json`
- `MasterBot/bot_definition/Status.md`
- `MasterBot/bot_definition/Heartbeat.md`
- `MasterBot/bot_definition/Lease.json`

### Workspace / System

- `MasterBot/workspace/OPERATOR_NOTES.md`
- `MasterBot/workspace/MASTER_TASKS.md`
- `MasterBot/workspace/MASTER_BOARD.md`
- `MasterBot/workspace/TEAM_COMMUNICATION.md`
- `System/SYSTEM_STATUS.md`
- `System/LIVE_BOTS.md`

### Optional Project

- canonical project files if the user creates a first project

### Optional Worker

- canonical bot files if the user creates a first worker

## Onboarding Marker

FTUE completion must be recorded in:

- `MasterBot/workspace/OPERATOR_NOTES.md`

Add a completed onboarding entry like:

```md
## Entry
Timestamp: 2026-04-09T12:00:00-04:00
Operator: Operator
Status: done

FTUE complete. MasterBot configured and workspace initialized.
```

This acts as the durable signal that the workspace has crossed first-run setup.

## Dashboard Requirements

The Dashboard FTUE must:

- detect uninitialized workspace
- launch onboarding automatically
- ask only one thing at a time
- persist after each step
- allow resume if interrupted
- never require the user to edit raw files during onboarding

The Dashboard must not implement separate setup logic from the underlying workspace logic.

## Telegram Requirements

The Telegram FTUE must be conversational but still step-based.

It must:

- detect uninitialized workspace
- ask one setup question at a time
- write the same underlying files
- allow the user to pause and resume
- hand off to the Dashboard or CLI if a step requires richer editing later

Telegram must not create a second onboarding system. It must call the same core setup routines.

## CLI Requirements

The CLI/bootstrap FTUE must support:

- creating the workspace
- stepping through MasterBot setup
- optionally creating the first project
- optionally creating the first worker

This is the fallback onboarding path if the Dashboard is not yet available.

## Acceptance Criteria

FTUE is complete only if a fresh GitHub user can:

1. install the framework
2. launch the system
3. be guided through MasterBot setup without reading a manual
4. choose OpenAI, LM Studio, or configure later
5. create a first project or skip it
6. create a first worker or skip it
7. land in a ready state with a real initialized workspace
8. resume onboarding if interrupted midway

## Non-Goals

The FTUE should not:

- hide the underlying file architecture
- pre-seed personal bots into the repo
- require the user to understand every file before continuing
- add duplicate orchestration logic in each frontend
- become a separate product layer disconnected from the workspace
