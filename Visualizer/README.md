# VISUALIZER

Optional visual interface for Agentic Harness V13.

This folder is separate from the core markdown control plane.

## Purpose

The Visualizer is a full web-based interface for seeing the swarm in action.

It should provide:

- a full 3D live view
- a 2D live view
- a VR live view
- one connected visual experience across all three modes

Its main goal is to visualize the system, the bots, their movement, and their current work in a way that feels alive and easy to understand.

## Core Behavior

The Visualizer should:

- show all live bots in a virtual setting
- represent bot movement and state visually
- show which bots are active, idle, blocked, or waiting
- show current task ownership
- show role ownership based on the live lease files in `_heartbeat/`
- show project and task state from the markdown files
- show recent events and messages from the markdown system

The Visualizer must read from the same V13 files used by every harness.

It must not become the source of truth.

## Communication Model

All communication should be possible through the Visualizer.

That includes:

- human to bot direct messages
- bot to human responses
- task creation
- task updates
- wake or attention requests
- viewing of live role occupancy

The Visualizer should send updates into the markdown system using the existing file protocol.

Preferred file touch points:

- `_messages/<Role>.md`
- `_messages/human_<HumanID>.md`
- `LAYER_TASK_LIST.md`
- `LAYER_SHARED_TEAM_CONTEXT.md`
- `LAYER_LAST_ITEMS_DONE.md`

## Required Views

### 3D View

- main beautiful immersive view
- live bot movement in 3D
- bot labels, role names, and status indicators
- clear indication of what each live bot is doing

### 2D View

- simplified tactical overview
- easier scanning of agents, tasks, and status
- useful for quick operational control

### VR View

- same swarm represented in VR
- intended for headset-capable environments
- should remain connected to the same live markdown-driven system

## Operator Controls

The operator should be able to:

- click on a live bot
- inspect its role, current task, and recent messages
- send a direct message to that bot
- add or update tasks
- view which role leases are live
- view which roles are stale or unclaimed
- act similarly to `Chief_of_Staff` for task updates when needed

## Design Rule

This is a visual layer, not a replacement for the core system.

It should:

- feel immersive
- feel alive
- make swarm activity obvious
- remain optional
- work entirely from the user's own system

## Expected Future Files

- `index.html`
- `world2d.html`
- `world3d.html`
- `worldvr.html`
- `styles.css`
- `app.js`
- optional local server helper if needed
