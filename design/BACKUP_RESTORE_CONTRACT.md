# Backup Restore Contract

## Purpose

This document defines the minimum production contract for backing up and restoring Agentic Harness state.

The goal is simple:

- the operator must be able to trust the system
- bot identity must survive
- project continuity must survive
- provider or harness changes must not destroy the organization

Backup and restore are not optional features.
They are core to operator ownership.

---

## Core Principle

The operator owns:

- the bots
- the memory
- the files
- the projects
- the orchestration logic
- the continuity

Therefore, the system must make it easy to:

- snapshot the ecosystem
- restore the ecosystem
- move the ecosystem
- reuse individual bots

---

## Scope

The backup/restore system must support:

1. full workspace backup
2. full workspace restore
3. selective bot restore
4. selective project restore
5. MasterBot restore

It should work even if:

- providers change
- harnesses change
- folders move
- the operator migrates to a new machine

---

## What Must Be Backed Up

### Required full-system backup contents

Back up:

- `MasterBot/`
- `Bots/`
- `Projects/`
- `System/`

These are the durable truth.

### Optional exclusions

Do not prioritize backing up:

- transient process IDs
- temporary caches
- regenerated UI assets if any exist later

The focus is on durable state, not ephemeral runtime debris.

---

## Backup Unit Types

### 1. Full Workspace Backup

Back up the entire workspace state.

Use when:

- operator wants a complete snapshot
- before upgrades
- before major changes
- before provider/harness migration

### 2. Bot Backup

Back up one bot folder, including:

- `bot_definition/`
- bot `workspace/`

Use when:

- reusing a bot elsewhere
- selling/sharing a bot
- protecting a specialized worker

### 3. Project Backup

Back up one project folder.

Use when:

- archiving project work
- moving a project to another workspace

### 4. MasterBot Backup

Back up `MasterBot/` separately when needed.

Use when:

- preserving operator command continuity
- migrating providers
- testing alternative Master runtimes

---

## Backup Structure

### Full backup destination

Store backups inside:

```text
Backups/
  <timestamp>/
    MasterBot/
    Bots/
    Projects/
    System/
    MANIFEST.json
```

### Bot-only backup destination

```text
Backups/
  bots/
    <bot-name>/
      <timestamp>/
        <bot-folder contents>
        MANIFEST.json
```

### Project-only backup destination

```text
Backups/
  projects/
    <project-name>/
      <timestamp>/
        <project-folder contents>
        MANIFEST.json
```

---

## Manifest Contract

Every backup should include a manifest.

### MANIFEST.json

Minimum structure:

```json
{
  "type": "full_workspace",
  "created_at": "2026-04-09T16:00:00-04:00",
  "workspace_root": "C:/Users/info/AgenticHarnessWork",
  "includes": [
    "MasterBot",
    "Bots",
    "Projects",
    "System"
  ],
  "notes": ""
}
```

### Allowed `type` values

- `full_workspace`
- `masterbot`
- `bot`
- `project`

### Rules

- manifest must always exist
- manifest must be machine-readable
- manifest should be enough to understand what the backup contains

---

## Restore Rules

### Full restore

Full restore should:

1. let the operator pick a backup snapshot
2. let the operator pick a target workspace root
3. restore:
   - `MasterBot`
   - `Bots`
   - `Projects`
   - `System`

### Selective bot restore

Selective bot restore should:

1. let the operator pick a bot backup
2. let the operator pick a target bot folder
3. restore the bot contents there
4. preserve existing unrelated files unless overwrite is explicitly requested

### Selective project restore

Selective project restore should:

1. let the operator pick a project backup
2. let the operator pick a target project folder
3. restore the project there

### MasterBot restore

MasterBot restore should:

1. let the operator pick a MasterBot backup
2. let the operator pick the target MasterBot folder
3. restore the full `MasterBot/` structure

---

## Safety Rules

### Non-destructive by default

Restore should be non-destructive by default.

That means:

- do not delete target folders automatically
- do not overwrite existing files silently
- either:
  - restore into a new location
  - or require explicit overwrite confirmation

### Preserve portability

Restored bots and projects must remain usable even if:

- folder paths changed
- provider settings changed later
- harnesses changed later

### Runtime-neutral restore

Restore should restore the durable files only.

It should not attempt to automatically restore:

- running processes
- terminal sessions
- ephemeral runtime state

Those can be restarted from the restored files.

---

## Backup Implementation Rules

### Simple implementation first

Use:

- normal filesystem copy
- timestamped folders
- manifest generation

Avoid:

- complex archive formats first
- database backup dependency
- cloud-only assumptions

### Filesystem semantics

Backup should preserve:

- directory structure
- file names
- UTF-8 markdown content
- JSON content

---

## Restore Implementation Rules

### Restore modes

Support:

1. full restore
2. bot restore
3. project restore
4. MasterBot restore

### Restore behavior

The restore system should:

- validate source exists
- validate manifest exists
- validate type
- restore into selected target path
- report what changed

---

## Minimum Tooling

The minimum production implementation may be command-line first.

Suggested scripts:

- `backup_system.py`
- `restore_system.py`

They should be simple and explicit.

Later, Dashboard may wrap them.

---

## Backup Examples

### Full backup

```powershell
py backup_system.py --workspace ../AgenticHarnessWork --type full
```

### Bot backup

```powershell
py backup_system.py --workspace ../AgenticHarnessWork --type bot --bot ExampleWorker
```

### Project backup

```powershell
py backup_system.py --workspace ../AgenticHarnessWork --type project --project ExampleProject
```

---

## Restore Examples

### Full restore

```powershell
py restore_system.py --backup ../AgenticHarnessWork/Backups/2026-04-09T16-00-00 --target ../RecoveredWorkspace
```

### Bot restore

```powershell
py restore_system.py --backup ../AgenticHarnessWork/Backups/bots/ExampleWorker/2026-04-09T16-00-00 --target ../RecoveredWorker
```

---

## Acceptance Criteria

Backup/restore is ready when:

1. full workspace backups can be created
2. full workspace can be restored into a fresh location
3. individual bots can be backed up and restored
4. individual projects can be backed up and restored
5. MasterBot can be backed up and restored independently
6. restored files remain readable and usable by the rest of the system
7. restore is non-destructive by default

---

## Transfer Prompt

Use this prompt for any builder implementing backup/restore:

> Read `AGENTIC_HARNESS_RESTART_TRANSFER.md` and `BACKUP_RESTORE_CONTRACT.md` first. Implement a simple, durable backup and restore system for the full workspace, MasterBot, individual bots, and individual projects. Keep it filesystem-native, non-destructive by default, and easy to understand.
