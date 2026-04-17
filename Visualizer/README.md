# VISUALIZER

Optional visual interface for Agentic Harness.

This folder is separate from the core markdown control plane.

## Purpose

The Visualizer is a full web-based interface for seeing the swarm in action.

It should provide:

- a full 3D live view
- a 2D live view
- a VR live view
- one connected visual experience across all three modes

Its main goal is to visualize the system, the bots, their movement, and their current work in a way that feels alive and easy to understand.

## Current Files

- `visualizer_server.py`
- `world2d.html`
- `world3d.html`
- `worldvr.html`
- `dashboard.html`
- `styles.css`
- `app.js`

## Start Commands

Windows:

```powershell
py Visualizer\visualizer_server.py
python Visualizer\visualizer_server.py
```

Then open:

- [http://127.0.0.1:8787/world2d.html](http://127.0.0.1:8787/world2d.html)
- [http://127.0.0.1:8787/world3d.html](http://127.0.0.1:8787/world3d.html)
- [http://127.0.0.1:8787/worldvr.html](http://127.0.0.1:8787/worldvr.html)
- [http://127.0.0.1:8787/dashboard.html](http://127.0.0.1:8787/dashboard.html)

## API

The server exposes:

- `/api/state`

That endpoint reads the live markdown system and returns:

- roles and lease state
- task summary
- projects
- recent event log lines
- recent shared context lines

## Core Behavior

The Visualizer should:

- show all live bots in a virtual setting
- represent bot movement and state visually
- show which bots are active, idle, blocked, or waiting
- show current task ownership
- show role ownership based on the live lease files in `_heartbeat/`
- show project and task state from the markdown files
- show recent events and messages from the markdown system

The Visualizer must read from the same core files used by every harness.

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

## V11 Inspiration To Preserve

From the older V11 world layer, the most valuable ideas to preserve are:

- one beautiful main 3D scene
- a simpler 2D tactical view
- a VR doorway into the same live system
- strong HUD overlays
- clear role/task/status visibility
- a dashboard for at-a-glance operator health

## Next Phase

The current implementation gives a local server and live markdown-driven UI scaffold.

Next improvements:

- richer 3D movement and scene design
- clickable role cards and detail panels
- write-back controls into `_messages/` and tasks
- full VR/WebXR layer
- presentation polish for the public demo
