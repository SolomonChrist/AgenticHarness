# ChiefChat Skill: Role Routing

Handler: `route_tasks_reply`, `role_wake_reply`, `assign_matching_tasks`
Safety Level: deterministic-routing

## Purpose
Route work to registered roles and bot aliases through markdown tasks and wake requests.

## Trigger Examples
- `Send this to Engineer and Researcher`
- `Wake Mary`
- `Assign TASK-123 to Bob`
- `Have the researcher look at this`

## Contract
- Resolve role and bot aliases before treating a name as a human.
- Write task updates before confirming routing.
- Write wake entries only after the target role/task is known.
- If a role is disabled, unregistered, or not automation-ready, say the task is queued but cannot run automatically yet.

