# HARNESS CATALOG

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
