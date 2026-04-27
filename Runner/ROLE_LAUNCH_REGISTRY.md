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
- `Launch Command: {AUTO_CLAUDE_CYCLE}` tells the Runner to use the built-in Claude Code scheduled automation launcher. The default Claude launch is a direct print-mode CLI run shaped like `claude -p "{PROMPT}" --model <model> --dangerously-skip-permissions`.
- `Launch Command: {AUTO_OPENCODE_CYCLE}` tells the Runner to use the built-in OpenCode scheduled automation launcher
- `Launch Command: {AUTO_GOOSE_CYCLE}` tells the Runner to use the built-in Goose scheduled automation launcher
- `Launch Command: {AUTO_OLLAMA_CYCLE}` tells the Runner to use the built-in Ollama scheduled automation launcher
- Custom CLI commands may be stored directly, for example: `cliname [FLAGS] "{PROMPT}" [ARGS]`
- For Claude Code auto-cycles, `Model / Profile` should be a real CLI model id such as `claude-haiku-4-5-20251001`, or left blank to use the CLI default. Do not store only a display label like `Haiku 4.5` if you expect Runner to pass `--model`.
- `py Runner\scheduled_role_runner.py --role <ROLE>` is the stable one-shot scheduled command for any registered role. It checks files, leases, work, and cooldowns before any provider call.
- `py Runner\daily_all_hands.py` runs the configurable 24-hour check/recovery pass for all automation-ready roles.
- `Wake Message` is the short instruction the Runner should write into `_messages/<Role>.md` when it launches or nudges that role
- `Chief_of_Staff` should usually have the shortest interval or persistent mode
- Claude Code is the easiest bootstrap and deep-work harness. The always-on Chief front door can stay cheaper and more file-first, for example with n8n or a custom CLI that only reads and writes markdown and routes work.
- Manual human-run roles can still claim roles and report work through the markdown files
- Claude Code reads `.claude/settings.json` and the Runner uses `claude -p "{PROMPT}" --model "{MODEL}" --dangerously-skip-permissions` for direct print-mode launches.
- OpenCode reads `opencode.json`; project config can set `permission` rules and the Runner bootstraps a permissive project config when needed.
- Gemini CLI reads `.gemini/settings.json`; `--approval-mode yolo` is applied at launch because yolo is a CLI flag, not a settings file value.
- Codex CLI reads `~/.codex/config.toml`; the Runner also passes `--yolo` for direct non-interactive runs.
- Goose reads `~/.config/goose/config.yaml` on macOS/Linux or `%APPDATA%\\Block\\goose\\config\\config.yaml` on Windows; the Runner records `GOOSE_PROVIDER`, `GOOSE_MODEL`, `GOOSE_MODE: auto`, and loads the developer builtin extension.
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
Startup Prompt: This is an existing Agentic Harness system. You are the operator's cheap file-first Chief_of_Staff control plane, not the heavy worker harness. Read standing memory, active human memory, leases, tasks, wake requests, and project state before replying. Keep responses warm, specific, and operational. For simple chat and status, answer directly. For deeper coding, research, or setup work, create or update the relevant task or wake request and delegate to the right harness. Use markdown files as the source of truth.
Wake Message: Check operator messages, check status, and continue orchestration.
Check Interval Minutes: 2
Wake Triggers:
- task_change
- message_change
- stale_lease
Max Concurrent Sessions: 1
Registration Source:
Last Confirmed:
Notes: Bootstrap and deep work can still use Claude Code, but the live always-on Chief should stay cheap and file-first, for example with n8n or a custom CLI. Use direct Claude only when you intentionally want a heavier Chief cycle. Claude launches should also create `.claude/settings.json` with read/write/edit allowances if it is missing.

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
