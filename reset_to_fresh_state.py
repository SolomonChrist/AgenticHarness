from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent


FRESH_FILES = {
    "HUMANS.md": """# HUMANS

Registry of humans who may be involved in tasks, approvals, reviews, or operational follow-up.

Human IDs must use:

- full first name and last name in CamelCase
- followed by a random 4-digit identifier

Example:

- `SolomonChrist4821`
- `JaneDoe1044`

## Record Template

### HUMAN
ID:
Full Name:
Role:
Preferred Contact Methods:
- telegram:
- email:
- phone:
- sms:
Escalation Preference:
Always Memory File:
Recent Memory Root:
Archive Memory Root:
Notes:

On a true fresh install, the first `Chief_of_Staff` should populate this file during operator onboarding.

## Records

(empty on fresh install - populated by `Chief_of_Staff` during operator onboarding)
""",
    "LAYER_CONFIG.md": """# LAYER CONFIG

Protocol Version: 13
Last Updated: 2026-04-15

## Swarm Configuration

- Active Chief of Staff Role: Chief_of_Staff
- Lease Renewal Interval Minutes: 5
- Lease Expiry Threshold Minutes: 5
- Event Log Archive Policy: Monthly rollover to `_archive/last_items_done/YYYY-MM.md`
- Project Root: `Projects/`
- Heartbeat Root: `_heartbeat/`
- Direct Message Root: `_messages/`
- Memory Root: `MEMORY/`
- Agent Memory Pattern: `MEMORY/agents/<Role>/`
- Human Memory Pattern: `MEMORY/humans/<HumanID>/`
- Recent Memory Archive Rule: summarize memory older than 30 days into `ARCHIVE/`
- Human Registry File: `HUMANS.md`

## Chief Of Staff Routing Rules

- Owns the top-level task list
- Reports back to the operator
- May cover missing specialist roles temporarily
- Should recommend missing roles when repeated coverage is needed
- Should inspect adopted existing projects and propose role structure on first run

## Registry

| Role | Current Holder | Harness | Provider | Model | Session ID | Last Seen | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chief_of_Staff | unclaimed | - | - | - | - | - | OPEN |

## Notes

- Update the registry when a role is claimed, released, or taken over.
- The lease files remain the live source of truth for active bot roles.
- Additional roles should be added only when the operator and/or `Chief_of_Staff` decides they are needed.
- If a harness cannot maintain timed renewal, it must refresh its lease on every meaningful write.
- A role with a stale self-lease must renew it before continuing normal work.
- Mixed harnesses are supported as long as they follow the same markdown protocol.
- On every successful role claim, the registry row, join note, and event log entry should all be updated as part of the same role-claim sequence.
- On every lease renewal, refresh `Last Seen` when possible so the registry stays aligned with the lease file.
- If registry state and lease state disagree, repair the registry to match the lease files.
- `LAYER_MEMORY.md` is shared memory; `MEMORY/` holds role-specific and human-specific long-term memory.
""",
    "LAYER_LAST_ITEMS_DONE.md": """# LAYER LAST ITEMS DONE

Newest entries should be appended in chronological order.
Archive monthly to `_archive/last_items_done/YYYY-MM.md`.

## Entries

[2026-04-15T09:00:00-04:00] [SYSTEM] BOOTSTRAP - Created Agentic Harness core markdown control plane.
[2026-04-15T09:01:00-04:00] [SYSTEM] BOOTSTRAP - Waiting for first role claims.
[2026-04-15T09:02:00-04:00] [SYSTEM] BOOTSTRAP - Initial swarm bootstrap tasks added to `LAYER_TASK_LIST.md`.
[2026-04-15T09:03:00-04:00] [SYSTEM] BOOTSTRAP - Every role claim should write a role-claim event here.
""",
    "LAYER_SHARED_TEAM_CONTEXT.md": """# LAYER SHARED TEAM CONTEXT

Shared whiteboard for team discussion, handoffs, and active coordination.

## Current Conversation

[2026-04-15T09:00:00-04:00] [SYSTEM] Agentic Harness control plane is live. Waiting for first role claims.
[2026-04-15T09:01:00-04:00] [SYSTEM] Chief_of_Staff should claim first, then coordinate role intake.
[2026-04-15T09:02:00-04:00] [SYSTEM] Every role claim should also write a short online note here.

## Working Agreements

- Keep messages short and actionable.
- Use `_messages/<Role>.md` for direct role-specific instructions.
- Use project `CONTEXT.md` files for project-local coordination when needed.
""",
    "LAYER_TASK_LIST.md": """# LAYER TASK LIST

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
""",
    "ROLES.md": """# ROLES

This file defines intended roles.
Live occupancy is determined by `_heartbeat/<Role>.md`.
The availability field in this file is design-time only.
It does not indicate who currently holds a live role.

## Role
Name: Chief_of_Staff
Default Availability: OPEN
Priority: CRITICAL
Can Write Main Task List: YES
Can Route Work: YES
Can Talk To Operator: YES
Can Create Project Subtasks: YES
Lease File: `_heartbeat/Chief_of_Staff.md`
Direct Message File: `_messages/Chief_of_Staff.md`
Expected Capabilities:
- orchestration
- delegation
- user communication
- proactive follow-up
- fallback execution when no specialist exists

## Role Expansion Rule

On a fresh install, this file should begin with only `Chief_of_Staff`.

Additional roles are added over time by:

- operator decision
- `Chief_of_Staff` recommendation
- project-specific needs

Roles may also be removed when they are no longer needed.

Suggested common roles to add when useful:

- Researcher
- Engineer
- Documentation
- QA
- Operations
- Calendar
- CRM
- Finance

When adding a new role, use this template:

## Role
Name:
Default Availability: OPEN
Priority:
Can Write Main Task List: NO
Can Route Work: NO
Can Talk To Operator: LIMITED
Can Create Project Subtasks: YES
Lease File: `_heartbeat/<Role>.md`
Direct Message File: `_messages/<Role>.md`
Expected Capabilities:
- 

## Claim Rules

- A bot must not act in a role until it has claimed that role.
- To claim a role, write `_heartbeat/<Role>.md`.
- Role occupancy is a lease, not a human-style checkout.
- Live occupancy is tracked by the lease file and registry, not by `Default Availability`.
- The role file should contain `Lease Expires At`.
- If a harness cannot maintain a timer, it must renew the lease on every meaningful write.
- If a role notices its own lease is stale, it must renew before continuing work.
- If the lease has expired, the role may be taken over.
- If a previous role-holder returns and finds a fresher lease, it must stand down.
""",
    "MEMORY/agents/Chief_of_Staff/ALWAYS.md": """# ALWAYS MEMORY - Chief_of_Staff

Use this file for standing memory that `Chief_of_Staff` should load every time.

Examples:

- how the operator prefers to work
- recurring priorities
- important standing rules
- communication preferences
- persistent executive-assistant behavior notes
""",
    "MEMORY/agents/Chief_of_Staff/ONBOARDING_STATUS.md": """# ONBOARDING STATUS - Chief_of_Staff

Status: NOT_STARTED
Completed At:
Active Human ID:
Notes:

Rules:

- On the first true run, `Chief_of_Staff` should update this file after operator onboarding is complete.
- If `Status: COMPLETE`, future `Chief_of_Staff` replacements should load existing memory and skip full onboarding.
- If memory is missing or damaged, `Chief_of_Staff` may run a repair onboarding pass and update this file.
""",
    "Runner/HARNESS_CATALOG.md": """# HARNESS CATALOG

Catalog of known harness types and learned launch methods.

This file is for `Chief_of_Staff`, the Runner, and future role builders.

Purpose:

- keep a growing list of common harness systems
- remember how this install launches them
- store confirmed launch patterns so the operator does not need to repeat them
- record custom harnesses added later
- support multiple harness families under one Runner instead of locking the swarm to a single vendor or CLI

## Usage Rules

- On first Runner setup, `Chief_of_Staff` should first check the machine and local environment for common harness families already known to Agentic Harness.
- After that first pass, `Chief_of_Staff` should ask the operator only which additional harnesses or custom commands exist that were not already detected or confirmed.
- If the operator confirms a harness is available, create or update its catalog entry.
- When a new role is created, `Chief_of_Staff` should connect that role to a known harness entry and record the chosen launch method in `Runner/ROLE_LAUNCH_REGISTRY.md`.
- If a custom harness is introduced later, add it here and then register the role launch entry that uses it.
- Keep entries practical and system-specific. The point is to remember what actually works on this machine.
- The Runner should stay harness-agnostic. A harness may be launched by:
  - a direct working command
  - a small wrapper script
  - a built-in Runner adapter for that harness family
- Claude Code, OpenCode, Goose, and Ollama ship as presets.
- Any prompt-based CLI can be registered as a custom provider when the user supplies a command template containing `{PROMPT}` or `{PROMPT_FILE}`.

## Common Harness Families To Check

- Claude Code
- OpenCode
- Ollama
- Goose
- Antigravity
- Google CLI
- Codex
- Manus
- n8n

## Harness Template

### HARNESS
Harness Key:
Display Name:
Family:
Available On This System:
Default Launch Command:
Default Working Directory:
Default Role Types:
- 
Model / Profile Notes:
Capabilities:
- Online LLM:
- Web/Search Capable:
- Browser/Tool Capable:
- Local Only:
- Manual Only:
Fallback Instructions:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes:

## Example Entries

### HARNESS
Harness Key: claude-code-haiku
Display Name: Claude Code (Haiku)
Family: Claude Code
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Chief_of_Staff
- Researcher
- Documentation
Model / Profile Notes: Example family entry. Replace with the actual model or command pattern used on this machine.
Prompt / Bootstrap Notes: Usually reads AGENTIC_HARNESS.md first unless a smaller bootstrap path is needed.
Last Confirmed:
Learned From:
Notes: Fill this only after the operator confirms the harness exists and works on this system.

### HARNESS
Harness Key: opencode-ollama
Display Name: OpenCode via Ollama
Family: OpenCode / Ollama
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Researcher
- Engineer
- Documentation
Model / Profile Notes: Useful for local models. Confirm context-window limits before assigning long boot prompts.
Prompt / Bootstrap Notes: Prefer AGENTIC_HARNESS_TINY.md for very small-context workers.
Last Confirmed:
Learned From:
Notes: Record the exact local model and command that worked on this machine once known.

### HARNESS
Harness Key: goose
Display Name: Goose
Family: Goose
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Researcher
- Engineer
- Operations
Model / Profile Notes:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: Record the exact Goose command or wrapper that works on this machine.

### HARNESS
Harness Key: gemini-cli
Display Name: Gemini CLI
Family: Gemini
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Researcher
- Documentation
- Analyst
Model / Profile Notes:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: Record the exact Gemini CLI command or wrapper that works on this machine.

### HARNESS
Harness Key: codex
Display Name: Codex CLI
Family: Codex
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Engineer
- Researcher
- Operations
Model / Profile Notes:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: Record the exact Codex command or wrapper that works on this machine.

### HARNESS
Harness Key: antigravity
Display Name: Antigravity
Family: Antigravity
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Engineer
- Operations
- QA
Model / Profile Notes:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes:

### HARNESS
Harness Key: openclaw
Display Name: OpenClaw
Family: OpenClaw
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- Chief_of_Staff
- Researcher
- Engineer
Model / Profile Notes:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: If OpenClaw already provides its own persistent daemon behavior, record the startup/bootstrap step and treat Runner as a coordinator rather than the primary scheduler for that role.

### HARNESS
Harness Key: custom
Display Name: Custom Harness
Family: Custom
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- 
Model / Profile Notes:
Prompt / Bootstrap Notes: Command templates may use `{PROMPT}`, `{PROMPT_FILE}`, `{ROLE}`, `{WORKDIR}`, and `{MODEL}`.
Last Confirmed:
Learned From:
Notes: Use this pattern for any future custom harness not already listed above.
""",
    "Runner/ROLE_LAUNCH_REGISTRY.md": """# ROLE LAUNCH REGISTRY

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
Automation Ready:
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
- `Automation Ready` should stay `NO` until that role has completed at least one successful manual first claim on the chosen harness for this install
- `Launch Command` may be blank for human/manual runners
- `Harness Key` should match an entry in `Runner/HARNESS_CATALOG.md` when possible
- `Launch Command` may use placeholders such as `{PROMPT}`, `{PROMPT_FILE}`, `{PROMPT_TEXT}`, `{ROLE}`, `{WORKDIR}`, `{MODEL}`, and `{BOOTSTRAP_FILE}`
- `Launch Command: {AUTO_CLAUDE_CYCLE}` tells the Runner to use the built-in Claude Code scheduled automation launcher
- `Launch Command: {AUTO_OPENCODE_CYCLE}` tells the Runner to use the built-in OpenCode scheduled automation launcher
- `Launch Command: {AUTO_GOOSE_CYCLE}` tells the Runner to use the built-in Goose scheduled automation launcher
- `Launch Command: {AUTO_OLLAMA_CYCLE}` tells the Runner to use the built-in Ollama scheduled automation launcher
- Custom CLI commands may be stored directly, for example: `cliname [FLAGS] "{PROMPT}" [ARGS]`
- For Claude Code auto-cycles, `Model / Profile` should be a real CLI model id such as `claude-haiku-4-5-20251001`, or left blank to use the CLI default. Do not store only a display label like `Haiku 4.5` if you expect Runner to pass `--model`.
- `Wake Message` is the short instruction the Runner should write into `_messages/<Role>.md` when it launches or nudges that role
- `Chief_of_Staff` should usually have the shortest interval or persistent mode
- Manual human-run roles can still claim roles and report work through the markdown files
- Do not blind-write this existing file from a harness. Use `configure_role_daemon.py` or read-then-update so existing registrations are preserved.

## Example Entries

### ROLE
Role: Chief_of_Staff
Enabled: NO
Automation Ready: NO
Execution Mode: interval
Harness Key:
Harness Type: Claude Code
Launch Command: {AUTO_CLAUDE_CYCLE}
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
Automation Ready: NO
Execution Mode: interval
Harness Key:
Harness Type: Claude Code
Launch Command: {AUTO_CLAUDE_CYCLE}
Working Directory:
Model / Profile:
Bootstrap File: AGENTIC_HARNESS.md
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
Notes: Use interval mode unless the harness can truly stay alive. Claude Code can use the built-in scheduled automation cycle.

### ROLE
Role: Engineer
Enabled: NO
Automation Ready: NO
Execution Mode: interval
Harness Key:
Harness Type: Claude Code
Launch Command: {AUTO_CLAUDE_CYCLE}
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
Notes: Interval mode is the safest default for Claude Code scheduled work cycles. Use `persistent` only when you have a true always-on launcher.

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
""",
    "Runner/RUNNER_CONFIG.md": """# RUNNER CONFIG

Configuration for the optional Agentic Harness Runner daemon.

## Purpose

This file defines how the single Runner daemon should behave.

The Runner should read this file together with:

- `ROLES.md`
- `LAYER_CONFIG.md`
- `_heartbeat/`
- `Runner/ROLE_LAUNCH_REGISTRY.md`
- `Runner/HARNESS_CATALOG.md`

## Global Settings

Runner Enabled: YES
Runner Mode: ACTIVE
Default Interval Minutes: 5
Chief_of_Staff Interval Minutes: 1
Stale Lease Check Minutes: 1
Fast Wake Poll Seconds: 1
Wake On File Change: YES
Wake On Message Change: YES
Wake On Task Change: YES
Wake On Stale Lease: YES
Allow Persistent Roles: YES
Allow Interval Roles: YES
Allow Manual Roles: YES
Launch Retry Backoff Seconds: 8
Urgent Wake Backoff Seconds: 3
Launch Failure Threshold: 3
Launch Failure Cooldown Seconds: 300
Provider Failure Cooldown Seconds: 21600
Stale Lease Storm Threshold: 5
Stale Lease Storm Window Seconds: 600
Stale Lease Storm Cooldown Seconds: 1800
Daily Check-In Enabled: YES
Daily Check-In Hour: 9
Daily All Hands Enabled: YES
Daily All Hands Interval Hours: 24
Daily All Hands Quota Retry: YES

## Notes

- `Runner Enabled: NO` is the safe template default for a brand-new install before onboarding confirms the launch plan.
- `Chief_of_Staff` should normally switch this to `YES` during first-run setup once the local harnesses are confirmed.
- `Runner Mode: DRY_RUN` means observe first, then switch to `ACTIVE` once the launch commands are real.
- For a normal first-run onboarding, `DRY_RUN` should be brief. The expected end state is `Runner Enabled: YES` and `Runner Mode: ACTIVE`.
- `Fast Wake Poll Seconds` controls how quickly the Runner notices urgent wake requests from Telegram or active roles.
- The Runner should be one daemon only.
- The Runner should not become the source of truth.
- Manual roles are valid and should not be auto-launched.
- Launch throttling should suppress repeated failed starts before they become credit drain or file-lock churn.
- `Daily All Hands` gives every automation-ready role one bounded recovery/check pass per interval. It helps quota-paused roles resume after provider access returns and keeps the operator from babysitting retries.
- `Chief_of_Staff` should maintain `Runner/HARNESS_CATALOG.md` and `Runner/ROLE_LAUNCH_REGISTRY.md` as the remembered launcher knowledge for this install.
- Recommended first run: set `Runner Enabled: YES` and keep `Runner Mode: DRY_RUN` only long enough to inspect the role decisions before using live launches.
""",
}


RUNTIME_FILES = [
    "debug.log",
    "Runner/.runner_state.json",
    "Runner/.runner_runtime.json",
    "Runner/_wake_requests.md",
    "Runner/_reminders.json",
    "ChiefChat/data/runtime.json",
    "ChiefChat/chief_chat.log",
    "Visualizer/.visualizer_runtime.json",
    "TelegramBot/data/state.json",
    "TelegramBot/data/runtime.json",
    "Runner/runner.log",
    "TelegramBot/telegram.log",
    "Visualizer/visualizer.log",
]


RUNTIME_DIRS = [
    "_heartbeat",
    "_messages",
    "Projects",
    "_archive/last_items_done",
    "Runner/_generated_prompts",
]


PRUNE_DIRS = [
    "__pycache__",
    ".locks",
    "_locks",
]


KEEP_IN_HUMANS = {"README.md", "_TEMPLATE"}
KEEP_IN_AGENTS = {"Chief_of_Staff"}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def clear_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        remove_path(child)


def prune_named_dirs(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_dir() and path.name in PRUNE_DIRS:
            shutil.rmtree(path)


def prune_human_memory(root: Path) -> None:
    humans_root = root / "MEMORY" / "humans"
    humans_root.mkdir(parents=True, exist_ok=True)
    for child in humans_root.iterdir():
        if child.name not in KEEP_IN_HUMANS:
            remove_path(child)


def prune_agent_memory(root: Path) -> None:
    agents_root = root / "MEMORY" / "agents"
    agents_root.mkdir(parents=True, exist_ok=True)
    for child in agents_root.iterdir():
        if child.name not in KEEP_IN_AGENTS:
            remove_path(child)


def main() -> None:
    for relative_path in RUNTIME_FILES:
        remove_path(ROOT / relative_path)

    for relative_path in RUNTIME_DIRS:
        clear_directory(ROOT / relative_path)

    prune_named_dirs(ROOT)
    prune_human_memory(ROOT)
    prune_agent_memory(ROOT)

    for relative_path, content in FRESH_FILES.items():
        write_text(ROOT / relative_path, content)

    print("Fresh-state reset complete.")


if __name__ == "__main__":
    main()
