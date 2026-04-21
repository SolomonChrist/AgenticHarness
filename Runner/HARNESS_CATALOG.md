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
- Claude Code, OpenCode, Gemini CLI, Codex CLI, Goose, Ollama, DeepAgents CLI, and OpenClaw CLI ship as presets.
- Any prompt-based CLI can be registered as a custom provider when the user supplies a command template containing `{PROMPT}` or `{PROMPT_FILE}`.

## Built-In Daemon Presets

These presets are known to Agentic Harness out of the box. Use `py configure_role_daemon.py --role <ROLE> --provider <KEY> --model <MODEL> --start-runner` after a role has been proven manually once.

| Provider Key | Display Name | Non-Interactive Shape | Web / Current Info Notes |
| --- | --- | --- | --- |
| claude | Claude Code | `claude -p "{PROMPT}" --model "{MODEL}" --permission-mode acceptEdits --chrome` | Online LLM. Chrome/browser integration is enabled for daemon cycles when available. |
| opencode | OpenCode | `opencode run "{PROMPT}" --model "{MODEL}" --dir "{WORKDIR}"` | Provider-dependent. Can attach to `opencode serve` later for lower cold-start time. |
| gemini | Gemini CLI | `gemini -p "{PROMPT}" --model "{MODEL}"` | Online LLM when authenticated. Good default for quick web-aware answers when configured. |
| codex | Codex CLI | `codex exec --cd "{WORKDIR}" --full-auto --search --model "{MODEL}" "{PROMPT}"` | Online LLM with live web search enabled by default for daemon cycles. |
| goose | Goose | `goose run --no-session -t "{PROMPT}" --model "{MODEL}" --quiet` | Provider-dependent. Supports tool-using agent runs and max-turn bounds. |
| ollama | Ollama | `ollama run "{MODEL}" "{PROMPT}"` | Local-only unless paired with external tools. Use for private/offline work, not current web facts. |
| deepagents | DeepAgents CLI | `deepagents "{PROMPT}" --model "{MODEL}"` | Provider-dependent; documented as supporting headless/non-interactive use and web search when configured. |
| openclaw | OpenClaw CLI | `openclaw agent --local --to agentic-harness -m "{PROMPT}"` | Provider/tooling-dependent. Useful where OpenClaw agents and gateway features are already configured. |

## Common Harness Families To Check

- Claude Code
- OpenCode
- Ollama
- Goose
- Antigravity
- Google CLI
- Codex
- DeepAgents CLI
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
Default Launch Command: {AUTO_CLAUDE_CYCLE}
Default Working Directory:
Default Role Types:
- Chief_of_Staff
- Researcher
- Documentation
Model / Profile Notes: Example family entry. Replace with the actual model or command pattern used on this machine.
Capabilities:
- Online LLM: YES
- Web/Search Capable: YES, when Chrome/browser integration or web-capable tools are available
- Browser/Tool Capable: YES
- Local Only: NO
- Manual Only: NO
Fallback Instructions: If browser/search is unavailable, answer best-effort and say exactly what verification is needed.
Prompt / Bootstrap Notes: Usually reads AGENTIC_HARNESS.md first unless a smaller bootstrap path is needed.
Last Confirmed:
Learned From:
Notes: Fill this only after the operator confirms the harness exists and works on this system.

### HARNESS
Harness Key: opencode-ollama
Display Name: OpenCode via Ollama
Family: OpenCode / Ollama
Available On This System: UNKNOWN
Default Launch Command: {AUTO_OPENCODE_CYCLE}
Default Working Directory:
Default Role Types:
- Researcher
- Engineer
- Documentation
Model / Profile Notes: Useful for local models. Confirm context-window limits before assigning long boot prompts.
Capabilities:
- Online LLM: Provider-dependent
- Web/Search Capable: Provider/tool-dependent
- Browser/Tool Capable: YES, when configured
- Local Only: NO, unless paired with Ollama/local provider
- Manual Only: NO
Fallback Instructions: If using a local model without web tools, give best-effort guidance plus verification steps.
Prompt / Bootstrap Notes: Prefer AGENTIC_HARNESS_TINY.md for very small-context workers.
Last Confirmed:
Learned From:
Notes: Record the exact local model and command that worked on this machine once known.

### HARNESS
Harness Key: goose
Display Name: Goose
Family: Goose
Available On This System: UNKNOWN
Default Launch Command: {AUTO_GOOSE_CYCLE}
Default Working Directory:
Default Role Types:
- Researcher
- Engineer
- Operations
Model / Profile Notes:
Capabilities:
- Online LLM: Provider-dependent
- Web/Search Capable: Provider/tool-dependent
- Browser/Tool Capable: YES
- Local Only: NO, unless configured with a local model only
- Manual Only: NO
Fallback Instructions: Configure provider/model before assigning web-current tasks.
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: Record the exact Goose command or wrapper that works on this machine.

### HARNESS
Harness Key: gemini-cli
Display Name: Gemini CLI
Family: Gemini
Available On This System: UNKNOWN
Default Launch Command: {AUTO_GEMINI_CYCLE}
Default Working Directory:
Default Role Types:
- Researcher
- Documentation
- Analyst
Model / Profile Notes:
Capabilities:
- Online LLM: YES, when authenticated
- Web/Search Capable: YES, depending on Gemini CLI model/tool configuration
- Browser/Tool Capable: Provider-dependent
- Local Only: NO
- Manual Only: NO
Fallback Instructions: If Gemini auth is missing, run `gemini` login/setup flow and retry.
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: Record the exact Gemini CLI command or wrapper that works on this machine.

### HARNESS
Harness Key: codex
Display Name: Codex CLI
Family: Codex
Available On This System: UNKNOWN
Default Launch Command: {AUTO_CODEX_CYCLE}
Default Working Directory:
Default Role Types:
- Engineer
- Researcher
- Operations
Model / Profile Notes:
Capabilities:
- Online LLM: YES
- Web/Search Capable: YES, daemon preset enables live search
- Browser/Tool Capable: YES
- Local Only: NO
- Manual Only: NO
Fallback Instructions: If not logged in, authenticate Codex CLI and rerun role daemon configuration.
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
Default Launch Command: {AUTO_OPENCLAW_CYCLE}
Default Working Directory:
Default Role Types:
- Chief_of_Staff
- Researcher
- Engineer
Model / Profile Notes:
Capabilities:
- Online LLM: Provider-dependent
- Web/Search Capable: Provider/tool-dependent
- Browser/Tool Capable: YES, when OpenClaw tools/gateway are configured
- Local Only: NO
- Manual Only: NO, when `openclaw agent --local` is configured
Fallback Instructions: Run OpenClaw setup/doctor and configure an agent before daemon handoff.
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: If OpenClaw already provides its own persistent daemon behavior, record the startup/bootstrap step and treat Runner as a coordinator rather than the primary scheduler for that role.

### HARNESS
Harness Key: deepagents
Display Name: DeepAgents CLI
Family: DeepAgents
Available On This System: UNKNOWN
Default Launch Command: {AUTO_DEEPAGENTS_CYCLE}
Default Working Directory:
Default Role Types:
- Researcher
- Engineer
- Documentation
Model / Profile Notes:
Capabilities:
- Online LLM: Provider-dependent
- Web/Search Capable: YES, when provider credentials and web search are configured
- Browser/Tool Capable: YES
- Local Only: NO, unless configured with a local provider
- Manual Only: NO, when headless mode is available
Fallback Instructions: If the CLI is not installed or credentials are missing, run DeepAgents CLI install/setup first.
Prompt / Bootstrap Notes:
Last Confirmed:
Learned From:
Notes: DeepAgents is best for richer tool-using tasks once provider credentials are configured.

### HARNESS
Harness Key: ollama
Display Name: Ollama
Family: Ollama
Available On This System: UNKNOWN
Default Launch Command: {AUTO_OLLAMA_CYCLE}
Default Working Directory:
Default Role Types:
- Researcher
- Engineer
- Documentation
Model / Profile Notes: Requires a local model name, for example `llama3.1`, `qwen3.5`, or another installed Ollama model.
Capabilities:
- Online LLM: NO
- Web/Search Capable: NO, unless paired with external tools
- Browser/Tool Capable: NO by default
- Local Only: YES
- Manual Only: NO
Fallback Instructions: Use for private/offline reasoning. For current web facts, route to a web-capable provider or provide verification steps.
Prompt / Bootstrap Notes: Prefer AGENTIC_HARNESS_TINY.md for smaller local context windows.
Last Confirmed:
Learned From:
Notes: Good for low-cost private background cycles when exact current information is not required.

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
