# LAYER TASK LIST

Machine-parseable but still readable.

Task status values:

- `TODO`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`
- `WAITING_ON_HUMAN`
- `HUMAN_CHECKOUT`

Bot-owned work should use role leases.
Human-owned work should use checkout fields instead of heartbeat behavior.

While an active milestone or validation phase is still in progress, continue the current workstream before opening a new one unless the operator explicitly changes direction.

## TASK
ID: TASK-0001
Title: Claim and verify Chief_of_Staff role
Project: swarm-bootstrap
Owner Role: Chief_of_Staff
Status: TODO
Priority: CRITICAL
Created By: operator
Created At: 2026-04-15T09:00:00-04:00
Done When:
- One bot claims `Chief_of_Staff`
- Heartbeat file exists for that role
- Registry is updated in `LAYER_CONFIG.md`

## TASK
ID: TASK-0002
Title: Claim specialist roles for first live swarm
Project: swarm-bootstrap
Owner Role: Chief_of_Staff
Status: TODO
Priority: HIGH
Created By: operator
Created At: 2026-04-15T09:01:00-04:00
Required Roles For This Bootstrap Pass:
- `Researcher`
- `Engineer`
Done When:
- At least one specialist role is claimed
- Heartbeat files exist for claimed roles
- Shared team context records who joined

Completion rule:
- Do not mark this task `DONE` until every specifically requested specialist role is verifiably active in `_heartbeat/`, `LAYER_CONFIG.md`, `LAYER_SHARED_TEAM_CONTEXT.md`, and `LAYER_LAST_ITEMS_DONE.md`.
- For this template bootstrap pass, that means both `Researcher` and `Engineer` must be verifiably active.
- If only one of those roles joins, keep this task `IN_PROGRESS`.

## TASK
ID: TASK-0003
Title: Create first real project subfolder and delegate sub-tasks
Project: swarm-bootstrap
Owner Role: Chief_of_Staff
Status: TODO
Priority: HIGH
Created By: operator
Created At: 2026-04-15T09:02:00-04:00
Done When:
- A project folder is created under `Projects/`
- Project task file contains role-specific sub-tasks
- At least one role agent picks up project work

Boundary rule:
- Do not satisfy this task by adopting optional add-on folders such as `TelegramBot/` or `Visualizer/` into `Projects/` unless the operator explicitly requested that work.

## HUMAN TASK TEMPLATE
ID: TASK-HUMAN-0001
Title:
Project:
Owner Role: Chief_of_Staff
Status: WAITING_ON_HUMAN
Priority:
Created By:
Created At:
Checked Out By:
Checked Out At:
Expected Follow-Up:
Last Human Contact At:
Escalate After:
Contact Method:
Reason:
Done When:
- 
