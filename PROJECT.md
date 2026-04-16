# PROJECT

Created: 2026-04-15
Protocol Version: 13
Status: ACTIVE

## Mission

Build and validate a simple, file-first Agentic Harness control plane that any harness system can join by reading one entry file and a small set of markdown files.

## Definition Of Done

- Multiple harnesses can join this workspace by reading the Agentic Harness markdown protocol.
- Roles can be claimed, heartbeated, and taken over after staleness.
- The `Chief_of_Staff` can orchestrate top-level work through the task list.
- Role agents can carry project work through project subfolders.
- The system remains understandable and restorable from the markdown files alone.

## Operating Principle

Simplicity over framework complexity.

## Current Milestones

- [ ] M1: Boot several bots into the markdown control plane
- [ ] M2: Validate role claim and heartbeat behavior
- [ ] M3: Validate top-level task orchestration plus per-project sub-tasks
- [ ] M4: Validate restart continuity with replacement bots

## Current Focus

Stand up the Agentic Harness core file system and begin live multi-bot testing.

## Install Modes

- Fresh install: start with `Chief_of_Staff` only, then expand roles as needed.
- Existing project adoption: place existing project work under `Projects/`, let `Chief_of_Staff` inspect it, and decide the needed roles with the operator.
