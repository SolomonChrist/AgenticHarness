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

The Runner is not the source of truth.

The markdown files remain the source of truth.

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

## Recommended Defaults

- `Chief_of_Staff`: shortest interval, or persistent when possible
- Researcher / Engineer / Documentation: interval mode by default
- Humans: manual mode

## Guardrails

- never write project state outside the markdown system
- never override leases as source of truth
- never spawn duplicate role holders intentionally
- respect stale lease handling from the core protocol

## First Setup

1. Fill `Runner/ROLE_LAUNCH_REGISTRY.md` with the roles you want the Runner to manage.
2. Fill or confirm `Runner/HARNESS_CATALOG.md` with the harnesses available on this system.
3. Set `Runner Enabled: YES` in `Runner/RUNNER_CONFIG.md` when you are ready.
4. Keep `Runner Mode: DRY_RUN` first to verify behavior.
5. Start the daemon and inspect the console output.
6. Switch to active mode only after the registry looks correct.

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

This lets the Runner prepare per-role prompt files and pass them to wrapper commands without hardcoding every role by hand.

## Wake Messages

Each auto-managed role may also define a short `Wake Message` in `ROLE_LAUNCH_REGISTRY.md`.

The Runner writes that message into `_messages/<Role>.md` when it launches or nudges the role.

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
