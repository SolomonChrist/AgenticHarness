# ROLE LAUNCH REGISTRY

Registry of how each role is started or contacted.

This file is for the optional Runner daemon and for `Chief_of_Staff` to understand how roles are called.

## Registration Rules

- Every auto-managed non-human role should have a registration entry here.
- Humans do not need launch commands, but they should have contact metadata.
- The Runner should use this file together with `ROLES.md`, `HUMANS.md`, `_heartbeat/`, and `Runner/HARNESS_CATALOG.md`.
- Every role that is started by a harness should point to a remembered harness entry when possible.
- `Chief_of_Staff` should update this file whenever a new role is created or a role's working launch command changes.
- The goal is to remember working launch methods so the operator does not need to repeat them in future sessions.

## Role Template

### ROLE
Role:
Enabled:
Execution Mode:
Harness Key:
Harness Type:
Launch Command:
Working Directory:
Model / Profile:
Bootstrap File:
Startup Prompt:
Wake Message:
Check Interval Minutes:
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions:
Registration Source:
Last Confirmed:
Notes:

## Human Template

### HUMAN RUNNER
Human ID:
Enabled:
Execution Mode: manual
Human Role:
Contact Methods:
- telegram:
- email:
- phone:
- sms:
- manual harness:
Wake Method:
Last Confirmed:
Notes:

## Example Notes

- `Execution Mode` should be one of: `persistent`, `interval`, `manual`
- `Launch Command` may be blank for human/manual runners
- `Harness Key` should match an entry in `Runner/HARNESS_CATALOG.md` when possible
- `Launch Command` may use placeholders such as `{WORKDIR}`, `{PROMPT_FILE}`, `{PROMPT_TEXT}`, `{ROLE}`, and `{BOOTSTRAP_FILE}`
- `Wake Message` is the short instruction the Runner should write into `_messages/<Role>.md` when it launches or nudges that role
- `Chief_of_Staff` should usually have the shortest interval or persistent mode
- Manual human-run roles can still claim roles and report work through the markdown files

## Example Entries

### ROLE
Role: Chief_of_Staff
Enabled: NO
Execution Mode: interval
Harness Key:
Harness Type: Claude Code
Launch Command:
Working Directory:
Model / Profile:
Bootstrap File: AGENTIC_HARNESS.md
Startup Prompt:
Wake Message: Check operator messages, check status, and continue orchestration.
Check Interval Minutes: 2
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source:
Last Confirmed:
Notes: Usually the shortest interval. Fill in the actual launch command for your environment.

### ROLE
Role: Researcher
Enabled: NO
Execution Mode: interval
Harness Key:
Harness Type: OpenCode/Ollama
Launch Command:
Working Directory:
Model / Profile:
Bootstrap File: AGENTIC_HARNESS_TINY.md
Startup Prompt:
Wake Message: Check status, review assigned research tasks, and continue active work.
Check Interval Minutes: 5
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source:
Last Confirmed:
Notes: Use interval mode unless the harness can truly stay alive.

### ROLE
Role: Engineer
Enabled: NO
Execution Mode: persistent
Harness Key:
Harness Type: Antigravity
Launch Command:
Working Directory:
Model / Profile:
Bootstrap File: AGENTIC_HARNESS.md
Startup Prompt:
Wake Message: Check status, review assigned engineering tasks, and continue active work.
Check Interval Minutes: 5
Wake Triggers:
- task_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source:
Last Confirmed:
Notes: Persistent mode works best if the harness can remain alive.

### HUMAN RUNNER
Human ID:
Enabled: YES
Execution Mode: manual
Human Role:
Contact Methods:
- telegram:
- email:
- phone:
- sms:
- manual harness:
Wake Method: Contact through the listed methods when a human-run task is assigned.
Last Confirmed:
Notes: Human manual runner. No launch command.
