# RUNNER

Optional liveness layer for Agentic Harness.

This folder is separate from the core markdown control plane.

## Purpose

The Runner is one daemon only.

Its job is to keep the swarm alive by:

- reading the core markdown system
- waking harnesses on interval
- supervising persistent harnesses
- leaving manual/human-run roles alone unless explicitly contacted
- monitoring stale leases
- relaunching roles when needed
- writing a short wake/check instruction into `_messages/<Role>.md` when it launches or nudges an auto-managed role
- reacting quickly to urgent wake requests written by Telegram or active harness roles

The Runner is not the source of truth.

The markdown files remain the source of truth.

## Operating Model

- first run: manually prove each specialist role once on the chosen harness
- later runs: let Runner own only the CLI-capable roles that were successfully proven
- manual-call systems remain valid swarm participants, but they should stay registered as manual until a real CLI cycle path exists

## Execution Modes

### persistent

The harness stays running in the background.

The Runner:

- monitors lease health
- monitors process health
- restarts the harness if needed

### interval

The harness is not always running.

The Runner:

- launches it every configured interval
- or launches it when relevant files changed
- expects the harness to read the files, do work, renew its lease, and exit or idle
- should only own a specialist role after that role has been manually proven once on the chosen harness for this install

### manual

The role is human-run or manually launched.

The Runner:

- does not auto-launch it
- may record that it is manual
- may help `Chief_of_Staff` understand how to contact the human/operator

## Files

Expected files in this folder:

- `README.md`
- `RUNNER_CONFIG.md`
- `HARNESS_CATALOG.md`
- `ROLE_LAUNCH_REGISTRY.md`
- `harness_role_cycle.py`
- `claude_role_cycle.py`
- `runner_daemon.py`
- `start_runner.bat`
- `start_runner.sh`

## Dynamic Role Support

The Runner must adapt to the current swarm, not a hardcoded list.

It should read:

- `ROLES.md`
- `_heartbeat/`
- `LAYER_CONFIG.md`
- `HARNESS_CATALOG.md`
- `ROLE_LAUNCH_REGISTRY.md`

If the swarm has 3 roles today, it manages 3.

If the swarm grows to 7 roles later, it manages 7.

## Human / Contact Support

Humans are not launched by command.

Instead, the Runner and `Chief_of_Staff` should know how to contact them.

Examples:

- email
- phone
- sms
- telegram
- manual claude code session

That contact metadata belongs in:

- `HUMANS.md`
- `Runner/HARNESS_CATALOG.md` for known manual harness types
- `Runner/ROLE_LAUNCH_REGISTRY.md`

## Harness Discovery And Learned Launch Memory

The Runner layer should grow smarter over time.

`Chief_of_Staff` should ask the operator which harnesses exist on the current machine, and it should also check the system for common harness families such as:

- Claude Code
- OpenCode
- Ollama
- Goose
- Antigravity
- Google CLI
- Codex
- Manus
- n8n

If one of those harnesses is available, `Chief_of_Staff` should record it in:

- `Runner/HARNESS_CATALOG.md`

Then, when a specific role is assigned to a specific harness, `Chief_of_Staff` should record the actual launch method in:

- `Runner/ROLE_LAUNCH_REGISTRY.md`

This means the system should remember things like:

- which harness family is available
- which model or profile is preferred for that harness
- what command successfully starts that harness on this machine
- what wake/check instruction should be left for that role after launch
- which bootstrap file it should read first
- which role types it is usually used for

The operator should not have to repeat the same harness launch details forever.

Over time, the install should accumulate a practical launch memory for the local swarm.

Important design rule:

- The Runner is meant to be cross-harness.
- Claude Code is only the first built-in scheduled-cycle adapter.
- Other harness families should be supported through the same pattern:
  - direct confirmed commands
  - small wrapper scripts
  - future built-in adapters
- The goal is one Runner controlling many harness types on schedule, not one vendor-specific daemon.

## Recommended Defaults

- `Chief_of_Staff`: shortest interval, or persistent when possible
- Researcher / Engineer / Documentation: interval mode only after first successful manual claim on the chosen harness
- Humans: manual mode

## Guardrails

- never write project state outside the markdown system
- never override leases as source of truth
- never spawn duplicate role holders intentionally
- respect stale lease handling from the core protocol

## First Setup

1. `Chief_of_Staff` should fill `Runner/ROLE_LAUNCH_REGISTRY.md` with the roles the Runner should manage.
2. `Chief_of_Staff` should fill or confirm `Runner/HARNESS_CATALOG.md` with the harnesses available on this system.
3. `Chief_of_Staff` should set `Runner Enabled: YES` in `Runner/RUNNER_CONFIG.md` once the local launch plan is confirmed.
4. Keep `Runner Mode: DRY_RUN` only long enough to verify behavior.
5. Start the daemon and inspect the console output.
6. Switch to active mode once the registry looks correct.

Preferred local daemon helper:

```powershell
py service_manager.py start runner
py service_manager.py stop runner
py service_manager.py status runner
```

Or, to request all core infrastructure at once on Windows:

```powershell
start_all_services.bat
```
7. When new specialist roles join later, `Chief_of_Staff` should immediately add them to the Runner so they become scheduled swarm members.

## Start Commands

Windows:

```powershell
Runner\start_runner.bat
```

Cross-platform:

```powershell
py Runner\runner_daemon.py
python Runner\runner_daemon.py
```

Mac/Linux:

```bash
./Runner/start_runner.sh
```

## Launch Command Placeholders

The Runner can render launch commands using placeholders from the role registry.

Supported placeholders:

- `{WORKDIR}` = role working directory
- `{HARNESS_ROOT}` = harness root folder
- `{ROLE}` = role name
- `{BOOTSTRAP_FILE}` = bootstrap file from the registry entry
- `{PROMPT_FILE}` = generated prompt file written by the Runner
- `{PROMPT_TEXT}` = full rendered startup prompt text
- `{HARNESS_KEY}` = harness key from the registry
- `{HARNESS_TYPE}` = harness type from the registry
- `{MODEL_PROFILE}` = model/profile text from the registry
- `{AUTO_CLAUDE_CYCLE}` = built-in Claude Code scheduled automation launcher
- `{AUTO_OPENCODE_CYCLE}` = built-in OpenCode scheduled automation launcher
- `{AUTO_GOOSE_CYCLE}` = built-in Goose scheduled automation launcher
- `{AUTO_OLLAMA_CYCLE}` = built-in Ollama scheduled automation launcher

This lets the Runner prepare per-role prompt files and pass them to wrapper commands without hardcoding every role by hand.

For Claude Code roles, the easiest working pattern is:

```text
Launch Command: {AUTO_CLAUDE_CYCLE}
```

That tells the Runner to call the built-in `claude_role_cycle.py` helper, which starts one short Claude automation pass for that role, lets it read the markdown state, do work, write updates, and exit until the next wake interval.

For the `Model / Profile` field:

- use a real Claude CLI model id such as `claude-haiku-4-5-20251001`, or
- leave it blank and let the local Claude CLI use its current default

Avoid storing only a display label like `Haiku 4.5` in a role that is meant to auto-run, because the Runner may need to pass that field directly to the CLI.

This is the first built-in adapter, not the final boundary of the system.

The same model should later exist for other harness families, for example:

- OpenCode / Ollama role cycles
- Goose role cycles
- Gemini CLI role cycles
- Codex role cycles
- Antigravity launch wrappers

Current built-in adapters:

- Claude Code
- OpenCode
- Goose
- Ollama

Current non-headless / wrapper-needed cases:

- Antigravity
- Gemini CLI (if/when installed)
- Codex (depends on a working local invocation path)
- OpenClaw (if installed and not already self-daemonized)

Important:

- If a role is currently being run manually through one of those wrapper-needed harnesses, register it as `Execution Mode: manual` until a real non-interactive launch method is confirmed.
- Do not point a manual Antigravity or similar role at `{AUTO_CLAUDE_CYCLE}` just because Claude is installed on the same machine.
- Mixed-harness swarms are valid, but the registry should reflect reality role by role.

## Wake Messages

Each auto-managed role may also define a short `Wake Message` in `ROLE_LAUNCH_REGISTRY.md`.

The Runner writes that message into `_messages/<Role>.md` when it launches or nudges the role.

## Immediate Wake Requests

Scheduled intervals are the fallback, not the only trigger.

If a Telegram message arrives or one active role assigns urgent work to another role, the system should not wait for the next normal interval.

The built-in wake request path is:

- append a line to `Runner/_wake_requests.md`
- format: `[timestamp] RoleName: reason`
- example: `[2026-04-18T14:45:00Z] Chief_of_Staff: telegram_message`

The Runner polls this file on a short fast-wake interval and will:

- `nudge` the role immediately if it is already active
- `launch` the role immediately if it is stale or missing

This means:

- Telegram can wake `Chief_of_Staff` right away
- `Chief_of_Staff` can wake `Researcher` or `Engineer` right away after dispatching work
- scheduled intervals remain as the safety net if no urgent wake request was written

That helps a freshly relaunched harness know what to do next, for example:

- check status
- check direct messages
- continue active work
- review newly assigned tasks

Example pattern:

```text
Launch Command: my-harness-launcher --cwd "{WORKDIR}" --prompt-file "{PROMPT_FILE}"
```

If a harness cannot be launched headlessly yet, leave it in manual mode until a working wrapper command exists.

Important limitation:

- The Runner can relaunch or nudge a role, but it cannot magically drive an already-open interactive CLI window unless that harness itself can continue work autonomously.
- In practice, the Runner works best when it can relaunch the role cleanly and leave a concrete wake message waiting in `_messages/<Role>.md`.
- For Claude Code specifically, interval automation works best as repeated short `claude -p` work cycles rather than trying to force an already-open terminal window to behave like a daemon.
- The same principle applies to every other harness family: prefer repeated short scheduled work cycles or a true wrapper/daemon path, not “one human-opened terminal should stay smart forever.”

## Recommended Workflow

- use `DRY_RUN` first
- confirm the Runner sees the correct roles
- confirm manual roles are ignored
- confirm unregistered roles are only reported, not launched
- then switch to active mode

## Fastest First Setup

Use this when you already have `Chief_of_Staff` running and want the Runner configured quickly.

1. Ask `Chief_of_Staff` to discover the harnesses on your machine and record them in:
   - `Runner/HARNESS_CATALOG.md`
   - `Runner/ROLE_LAUNCH_REGISTRY.md`
2. Tell `Chief_of_Staff` which role should use which harness.
3. Keep `Runner Enabled: YES` and `Runner Mode: DRY_RUN` for the first pass.
4. Start the daemon and inspect what it would launch.
5. Only after that, switch the Runner to active mode.

This setup should normally be performed by the active `Chief_of_Staff` during the first-run walkthrough as part of onboarding, not by forcing the operator to hand-edit Runner files first.

After the first-pass Runner setup is complete, `Chief_of_Staff` should try to start the Runner daemon for the operator if the local harness can safely execute the start command. If it cannot, it should immediately provide the exact command to run next.

The operator should not have to discover or invent a separate Runner setup prompt. If Runner is present, `Chief_of_Staff` should own this setup path by default.

Recommended instruction to give `Chief_of_Staff`:

```text
Set up the Runner for this install.
First, check this machine and local environment for common harnesses you know how to look for.
Then update Runner/HARNESS_CATALOG.md with what you can confidently confirm.
After that, ask me only about any other harnesses or custom commands I use that were not already detected or confirmed.
Next, update Runner/ROLE_LAUNCH_REGISTRY.md with the actual role-to-harness launch entries we want to use.
Use Chief_of_Staff as the first role to configure.
Keep Runner/RUNNER_CONFIG.md in DRY_RUN mode for the first pass.
Do not guess launch commands if you are unsure. Ask me to confirm them.
```

If the swarm is already running manually and you want to turn that into the first remembered Runner configuration, give `Chief_of_Staff` this:

```text
Set up the Runner now.

Use the current live swarm as the first known working configuration:
- Chief_of_Staff = Claude Code (Haiku 4.5)
- Researcher = Claude Code
- Engineer = Claude Code

Update Runner/HARNESS_CATALOG.md with the confirmed harnesses on this machine.
Update Runner/ROLE_LAUNCH_REGISTRY.md with launch entries for Chief_of_Staff, Researcher, and Engineer.
Keep Runner/RUNNER_CONFIG.md in DRY_RUN mode.
Do not switch to active mode yet.
After that, tell me exactly how to start the Runner daemon and what it would try to launch.
```
