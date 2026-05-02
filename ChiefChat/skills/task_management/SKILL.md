# ChiefChat Skill: Task Management

Handler: `task_action_reply`
Safety Level: deterministic-file-mutation

## Purpose
Mutate file-backed task state only after ChiefChat classifies an operator message as a task action.

## Trigger Examples
- `Remove those web requests`
- `Cancel TASK-WEB-123`
- `Complete TASK-123`
- `Reopen TASK-123`
- `Assign TASK-123 to Engineer`
- `Add note to TASK-123: this is priority one`

## Contract
- Never physically delete task blocks.
- Update `Status`, `Owner Role`, or `Audit` lines in markdown.
- Reply with before count, after count, changed count, and changed task IDs.
- If no task matches, say no files changed.

