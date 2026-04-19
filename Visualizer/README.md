# VISUALIZER

Optional visual interface for Agentic Harness.

This folder is separate from the core markdown control plane.

`Chief_of_Staff` should help set it up only when the operator explicitly asks for the Visualizer add-on.

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
- `vendor/three-r184.module.min.js`
- `vendor/THREEJS_LICENSE.txt`

## Start Commands

Windows:

```powershell
py Visualizer\visualizer_server.py
python Visualizer\visualizer_server.py
Visualizer\start_visualizer.bat
py service_manager.py start visualizer
```

Then open:

- [http://127.0.0.1:8787/world2d.html](http://127.0.0.1:8787/world2d.html)
- [http://127.0.0.1:8787/world3d.html](http://127.0.0.1:8787/world3d.html)
- [http://127.0.0.1:8787/worldvr.html](http://127.0.0.1:8787/worldvr.html)
- [http://127.0.0.1:8787/dashboard.html](http://127.0.0.1:8787/dashboard.html)

## 3D Controls

The 3D world now supports:

- `WASD` to move through the scene
- forward and backward movement follow the current look direction
- `Shift` to move faster
- right-click drag to look around
- left-click an office to inspect project details
- left-click a bot to inspect role/lease details

## Movement Notes

- The 3D world currently behaves like a free-roam office camera.
- `W` moves forward in the direction you are currently looking.
- `S` moves backward relative to your current view.
- `A` and `D` strafe left and right relative to your current facing direction.
- Hold `Shift` while moving to travel faster.
- Hold right-click and drag to rotate the camera view.
- Use left-click only for interacting with offices and bot entities.

## Bot Visual State

- Idle live roles should appear blue and show `idle` above their heads.
- Working roles should appear orange and show their current task above their heads.
- Working roles should drift and animate faster so the world feels active at a glance.
- Stale roles should appear red to highlight that they need attention or renewal.
- The 3D world derives this from the live lease files plus the current task field for each role.

## Offline Reliability

The 3D world uses a locally vendored copy of Three.js instead of a CDN.

That means:

- the demo keeps working if internet drops
- users can run the visualizer offline
- the repo ships with the exact pinned version it was tested with

Current bundled version:

- `three-r184.module.min.js`

Three.js is MIT-licensed. The bundled license text is included in:

- `vendor/THREEJS_LICENSE.txt`

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
- bring `worldvr.html` up to the same level as the upgraded 3D world
- full VR/WebXR layer
- presentation polish for the public demo
