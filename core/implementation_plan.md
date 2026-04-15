# [PLAN] Swarm Execution & Routing Policy Hardening

This plan transitions the Agentic Harness from a "planner/decomposer" into a "deterministic execution swarm" by implementing systemic routing policies, worker viability checks, and a hardened task lifecycle.

## User Review Required

> [!IMPORTANT]
> **Cost Tier Calibration**: I am introducing a `cost_tier` metadata field for all bots (1-10). 
> - `1` = Local/Zero Cost (LM Studio, Local Python).
> - `7` = Standard Cloud (GPT-4o, Claude 3.5 Sonnet).
> - `10` = Premium (Claude 3 Opus).
> **Routing Policy**: The MasterBot will now filter and sort available bots based on the global `routing_policy` set in the dashboard.

> [!WARNING]
> **Viability Enforcement**: Bots that are disabled or have stale heartbeats (older than 5 minutes) will be automatically ignored by the MasterBot, even if they are the "best" fit on paper.

## Proposed Changes

### 1. Global System Configuration
#### [NEW] [SystemProfile.json](file:///c:/Users/info/AgenticHarnessWork/System/SystemProfile.json)
- Store global state: `routing_policy` (default: `OPEN_COST`).

### 2. Bot Metadata & Templates [HARDENING]
#### [MODIFY] [build_bot.py](file:///c:/Users/info/OneDrive/Desktop/AgenticHarness/MainCode/core/build_bot.py)
- Add `cost_tier`: `1` for `lmstudio`, `7` for others by default.
- Add `cost_tier` to `HarnessProfile.json`.

### 3. MasterBot: Policy-Aware Routing
#### [MODIFY] [master_daemon.py](file:///c:/Users/info/OneDrive/Desktop/AgenticHarness/MainCode/core/master_daemon.py)
- **`get_swarm_roster()`**: Add `cost_tier` and `is_alive` (heartbeat check) to each bot object.
- **`get_routing_instruction()`**: 
    - Filter by `is_alive == True` and `enabled == True`.
    - Apply `RoutingPolicy` filters (e.g., `ZERO_COST` only allows `cost_tier == 1`).
    - Sort results by cost/quality based on the active policy.
- **Task Emission**: Include `Routing Policy: <name>` and `Selection Reason: <reason>` in the task markdown block for dashboard visibility.

### 4. Worker: Hardened Execution Loop
#### [MODIFY] [worker_daemon.py](file:///c:/Users/info/OneDrive/Desktop/AgenticHarness/MainCode/core/worker_daemon.py)
- **Atomic Claiming**: Transition tasks through `new` -> `claimed` -> `in_progress`.
- **Result Writing**: Ensure harness output is summarized in `WORKING_NOTES.md` and `ARTIFACTS.md`.
- **Error States**: Explicitly transition to `blocked` on harness failure.

### 5. Dashboard UI: Operator Control
#### [MODIFY] [dashboard_server.py](file:///c:/Users/info/OneDrive/Desktop/AgenticHarness/MainCode/core/dashboard_server.py)
- Add `/api/system/policy` endpoint to toggle routing modes.
#### [MODIFY] [index.html](file:///c:/Users/info/OneDrive/Desktop/AgenticHarness/MainCode/core/dashboard/index.html)
- Add "Global Routing Policy" dropdown to the MasterBot Configuration panel.
#### [MODIFY] [app.js](file:///c:/Users/info/OneDrive/Desktop/AgenticHarness/MainCode/core/dashboard/app.js)
- Update rendering to show routing metadata on task cards.

## Open Questions
- Should the `cost_tier` be manually adjustable in the bot editor, or should I try to auto-deduce it based on the provider/model? (I recommend manual adjustment as the source of truth).
- For `ZERO_COST` mode, if NO local bots are alive, should the MasterBot fail the delegation or fallback to a "Cheap" bot with an alert?

## Verification Plan

### Automated Tests
- **Routing Test**: Set policy to `ZERO_COST`, attempt a task, and verify no cloud bots are selected.
- **Viability Test**: Kill a worker process, wait 5 mins for stale heartbeat, and verify the MasterBot stops routing to it.

### Manual Verification
- **Dashboard Check**: Verify that task cards now show "Why it was chosen" and the current Policy.
