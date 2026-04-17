# HARNESS CATALOG

Catalog of known harness types and learned launch methods.

This file is for `Chief_of_Staff`, the Runner, and future role builders.

Purpose:

- keep a growing list of common harness systems
- remember how this install launches them
- store confirmed launch patterns so the operator does not need to repeat them
- record custom harnesses added later

## Usage Rules

- On first Runner setup, `Chief_of_Staff` should first check the machine and local environment for common harness families already known to Agentic Harness.
- After that first pass, `Chief_of_Staff` should ask the operator only which additional harnesses or custom commands exist that were not already detected or confirmed.
- If the operator confirms a harness is available, create or update its catalog entry.
- When a new role is created, `Chief_of_Staff` should connect that role to a known harness entry and record the chosen launch method in `Runner/ROLE_LAUNCH_REGISTRY.md`.
- If a custom harness is introduced later, add it here and then register the role launch entry that uses it.
- Keep entries practical and system-specific. The point is to remember what actually works on this machine.

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
Harness Key: custom
Display Name: Custom Harness
Family: Custom
Available On This System: UNKNOWN
Default Launch Command:
Default Working Directory:
Default Role Types:
- 
Model / Profile Notes:
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: Use this pattern for any future custom harness not already listed above.
