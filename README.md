# AHOS MASTER BLUEPRINT v2.0
## Universal Agentic Harness Operating System
### By Solomon Christ — Enhanced Edition

> **Core Law:** All intelligence, memory, and continuity must live inside the repository — not inside the agent.
> Agents are temporary. The repo is permanent.

---

## WHAT THIS SYSTEM DOES

This blueprint initializes a **portable, cross-harness project operating system** (AHOS) that works identically across:
- Claude Code / Claude.ai
- Google Gemini CLI
- OpenCode / OpenClaw
- Codex-style systems
- Local LLM harnesses (Ollama, LM Studio, etc.)
- Any future agentic system not yet built

Any agent, at any time, can open this repo, read the system files, and continue the project with zero context loss.

---

## REPOSITORY INITIALIZATION PROTOCOL

### Step 1 — Create Folder and Private Git Repo

```bash
mkdir <project-name>
cd <project-name>
git init
gh repo create <project-name> --private --source=. --remote=origin
```

### Step 2 — Create Full Directory Structure

```
<project-root>/
├── CLAUDE.md                    # Adapter: Claude Code / Claude.ai
├── AGENTS.md                    # Adapter: OpenAI Agents / Codex / generic
├── GEMINI.md                    # Adapter: Gemini CLI / Vertex
├── README.md                    # Human-readable project overview
├── .gitignore                   # Must include .env, secrets/, *.key
│
└── docs/
    ├── PROJECT_RULES.md         # ★ Constitution — highest authority
    ├── MEMORY.md                # Long-term stable knowledge
    ├── LAST_WORK_ITEMS_DONE.md  # Session handoff file
    ├── TODO.md                  # Execution queue
    ├── ARCHITECTURE.md          # System design
    ├── DECISIONS.md             # Decision log with rationale
    ├── TESTING.md               # Test strategy and commands
    ├── TOOLS.md                 # All tools, MCPs, CLIs, APIs
    ├── PERMISSIONS.md           # Pre-approved / Ask-first / Never
    ├── SESSION_LOG.md           # Chronological session history
    ├── CHANGELOG.md             # ★ NEW: Semantic version history
    ├── CONTEXT_SNAPSHOT.md      # ★ NEW: Compressed current state
    ├── ENVIRONMENT.md           # ★ NEW: Env configs per environment
    ├── ERRORS.md                # ★ NEW: Error and incident tracker
    └── SECRETS.template.md      # ★ NEW: Secrets manifest (keys only)
```

---

## FILE DEFINITIONS (MANDATORY STRUCTURE)

---

### `docs/PROJECT_RULES.md` — The Constitution

**This is the highest authority. All agents must read this first.**

```markdown
# PROJECT RULES

## Project Purpose
[What this project does and why it exists]

## Tech Stack
[Languages, frameworks, runtimes, versions]

## Coding Standards
- [Style conventions]
- [Naming patterns]
- [Comment requirements]

## File Organization Rules
[Where things go and why]

## Execution Rules
- Never modify production without running tests
- Never commit secrets
- Always update LAST_WORK_ITEMS_DONE.md before ending session
- [Add project-specific rules]

## Safety Constraints
[Hard limits that must never be bypassed]

## Update Protocol
After EVERY task you must update:
1. LAST_WORK_ITEMS_DONE.md
2. TODO.md
3. SESSION_LOG.md
And optionally:
4. MEMORY.md (if new stable knowledge was learned)
5. ARCHITECTURE.md (if design changed)
6. DECISIONS.md (if a significant choice was made)
7. ERRORS.md (if an error occurred)
8. CHANGELOG.md (if a version-worthy change was made)
```

---

### `docs/MEMORY.md` — Long-Term Knowledge Store

Store ONLY stable, long-term facts. Never store temporary session notes here.

```markdown
# MEMORY

## Tech Stack
- Language: [e.g., TypeScript 5.x]
- Runtime: [e.g., Node 20 LTS]
- Framework: [e.g., Next.js 14]
- Database: [e.g., PostgreSQL 16 via Supabase]

## Key Decisions (Summary)
[One-line summaries — full entries go in DECISIONS.md]

## Constraints
[Hard technical or business constraints]

## Preferences
[Owner preferences: formatting, patterns, naming]

## Environments
- Local: [how to run locally]
- Staging: [URL / access]
- Production: [URL / access level]

## Core Assumptions
[Assumptions baked into the architecture]

## Agent Notes
[Anything future agents must know that doesn't fit elsewhere]
```

---

### `docs/LAST_WORK_ITEMS_DONE.md` — Session Handoff

**This is the most critical file for continuity. Always write as if you will never see this project again.**

```markdown
# LAST WORK ITEMS DONE

## Last Updated
[ISO 8601 timestamp — e.g., 2025-01-15T14:32:00Z]

## Agent / Harness Used
[e.g., Claude Code 1.x / Gemini CLI 2.x / OpenCode]

## Completed This Session
- [Task 1 — specific and complete]
- [Task 2]

## Files Changed
- [path/to/file.ts — what changed and why]

## Commands Run
```bash
[exact commands run this session]
```

## Tests Run
- [test name] — [PASS/FAIL] — [notes]

## Current Project Status
[One paragraph: where the project stands right now]

## Next Recommended Action
[The single most important next thing to do]

## Blockers
- [Any blockers or unresolved questions]

## Notes for Next Agent
[Anything critical the next agent must know before starting]

## Danger Zones
[Files or areas that are fragile or partially complete — DO NOT TOUCH without reading this]
```

---

### `docs/TODO.md` — Execution Queue

```markdown
# TODO

## 🔴 HIGH PRIORITY
- [ ] [Task — specific, actionable, estimated complexity: S/M/L]

## 🟡 MEDIUM PRIORITY
- [ ] [Task]

## 🟢 LOW PRIORITY / NICE TO HAVE
- [ ] [Task]

## ✅ COMPLETED (archive, do not delete)
- [x] [Task] — completed [date]
```

---

### `docs/ARCHITECTURE.md` — System Design

```markdown
# ARCHITECTURE

## System Overview
[High-level description — must enable a new agent to understand the full system in 2 minutes]

## Components
[List each component, its purpose, and how it connects]

## Data Flow
[Describe how data moves through the system]

## APIs
[Internal and external APIs — endpoints, auth, rate limits]

## Database Schema
[Table/collection summaries — link to migration files]

## Dependencies
[Critical external dependencies and why they were chosen]

## Known Technical Debt
[Areas that need refactoring]
```

---

### `docs/DECISIONS.md` — Decision Log

**Prevents regressions. Prevents agents from re-asking the same question.**

```markdown
# DECISIONS

## Decision Template
### [Short decision title]
- **Date:** [ISO date]
- **Decision:** [What was decided]
- **Reason:** [Why this was the right choice]
- **Alternatives Considered:** [What else was evaluated]
- **Impact:** [What this affects]
- **Rollback:** [How to undo this if it turns out to be wrong]
```

---

### `docs/TESTING.md` — Test Strategy

```markdown
# TESTING

## How to Run Tests
```bash
[exact commands]
```

## Test Types
- Unit: [what is unit tested and how]
- Integration: [what integration tests exist]
- E2E: [what E2E tests exist]

## Success Criteria
[What "passing" means for this project]

## Known Failing Tests
[Any tests that are intentionally skipped and why]

## Before Committing
[Checklist an agent must run before committing]
```

---

### `docs/TOOLS.md` — Tools, MCPs, and Integrations

```markdown
# TOOLS

## CLI Commands
| Command | Purpose | Usage |
|---------|---------|-------|
| `npm run dev` | Start dev server | [details] |

## MCP Servers
| MCP | Purpose | Connection |
|-----|---------|------------|
| [name] | [what it does] | [how to connect] |

## APIs
| API | Purpose | Auth Method | Rate Limits |
|-----|---------|-------------|-------------|

## Package Managers
[Which ones and versions]

## External Integrations
[Webhooks, third-party services, etc.]

## Agent-Specific Notes
- Claude Code: [any specific flags or modes to use]
- Gemini CLI: [any specific settings]
- OpenCode: [any specific settings]
```

---

### `docs/PERMISSIONS.md` — Permission Framework

```markdown
# PERMISSIONS

## ✅ PRE-APPROVED (No confirmation needed)
- Read any file in the repo
- Write to any file in /docs/
- Run test commands
- Install dev dependencies
- Create new files in designated directories
- Commit and push to feature branches

## ⚠️ ASK FIRST (Must confirm before proceeding)
- Delete any file
- Modify database schema
- Change environment variables
- Install new production dependencies
- Push to main/master branch
- Make external API calls with side effects
- Modify CI/CD configuration
- Rename or restructure directories

## 🚫 NEVER (Requires explicit written approval)
- Modify .env files containing real credentials
- Access or transmit any secrets or API keys
- Deploy to production
- Drop or truncate database tables
- Modify billing or payment logic
- Push force to any branch
- Disable tests or CI checks
- Execute anything outside the project directory

## Situation Handling
If an action is ambiguous:
1. Stop
2. Log the situation in LAST_WORK_ITEMS_DONE.md under Blockers
3. State what you were trying to do and what approval you need
4. Do not proceed until instructed
```

---

### `docs/SESSION_LOG.md` — Chronological Session History

```markdown
# SESSION LOG

## Entry Template
### [ISO Timestamp] — [Agent/Harness Name]
- **What was done:** [summary]
- **Key insights:** [anything learned that future agents should know]
- **Issues encountered:** [problems hit and how they were resolved]
- **State at end:** [what state the project was in when this session ended]
```

---

### `docs/CHANGELOG.md` ★ NEW — Version History

Tracks meaningful project milestones using semantic versioning. Agents update this when a version-worthy change is complete.

```markdown
# CHANGELOG

All notable changes to this project will be documented here.
Format: [Semantic Versioning](https://semver.org/)

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [0.1.0] — YYYY-MM-DD
### Added
- Initial project scaffolding
- AHOS system initialized
```

---

### `docs/CONTEXT_SNAPSHOT.md` ★ NEW — Compressed Current State

**This is the single-file fast-load for token-constrained agents.** When an agent has a small context window or needs a quick orientation, it reads this first. Agents must regenerate this at the end of every session.

```markdown
# CONTEXT SNAPSHOT
*Auto-generated at end of each session. Read this first if context window is limited.*

## Last Updated
[ISO timestamp]

## Project in One Sentence
[What this project is]

## Current Phase
[e.g., "MVP build — 60% complete" / "Bug fixing before v1.0 release"]

## Most Recent Action
[Last thing completed]

## Single Most Important Next Action
[The next thing to do]

## Active Danger Zones
[Files or areas that must not be touched carelessly]

## Quick Command Reference
```bash
# Start dev server
[command]

# Run tests
[command]

# Build
[command]
```

## Where Everything Is
- Main entry: [path]
- Config: [path]
- Tests: [path]
- Docs: /docs/
```

---

### `docs/ENVIRONMENT.md` ★ NEW — Environment Configuration

```markdown
# ENVIRONMENT

## Local Development
- Setup: [step-by-step]
- Required env vars: [list — values in .env, never committed]
- Seed data: [how to seed]

## Staging
- URL: [url]
- Access: [how to get access]
- Deploy command: [command]

## Production
- URL: [url]
- Access: [restricted — see PERMISSIONS.md]
- Deploy command: [restricted]

## Environment Variables Required
| Variable | Purpose | Example Value |
|----------|---------|---------------|
| DATABASE_URL | DB connection | postgres://... |
| API_KEY | Third-party auth | [see SECRETS.template.md] |

*Never commit real values. Use .env locally. Use secrets manager in production.*
```

---

### `docs/ERRORS.md` ★ NEW — Error and Incident Tracker

**Agents must log any significant errors here. This prevents future agents from hitting the same walls.**

```markdown
# ERRORS & INCIDENTS

## Error Template
### [Short error title] — [Date]
- **Error:** [Exact error message or description]
- **Context:** [What was being attempted]
- **Root Cause:** [Why it happened]
- **Resolution:** [How it was fixed]
- **Prevention:** [How to avoid this in the future]
- **Status:** [RESOLVED / OPEN / WORKAROUND]
```

---

### `docs/SECRETS.template.md` ★ NEW — Secrets Manifest

**This file lists what secrets are needed — NEVER the values themselves. Commit this file. Never commit .env.**

```markdown
# SECRETS MANIFEST

This file documents what secrets this project requires.
Actual values must NEVER be committed to the repository.
Store real values in: .env (local), secrets manager (production).

## Required Secrets
| Key | Purpose | Where to Get It |
|-----|---------|-----------------|
| DATABASE_URL | Primary DB | [Infra docs / provider] |
| OPENAI_API_KEY | AI completions | platform.openai.com |
| [KEY_NAME] | [purpose] | [how to obtain] |

## .env Format
```
DATABASE_URL=
OPENAI_API_KEY=
```

## Rotation Schedule
| Key | Last Rotated | Rotate Every |
|-----|-------------|--------------|
```

---

## HARNESS ADAPTER FILES

These files must NOT contain logic. They are boot loaders — they tell each harness exactly how to initialize.

---

### `CLAUDE.md`

```markdown
# CLAUDE — Agentic Harness Adapter
# Universal Agentic Harness Operating System (AHOS) v2.0

You are operating in Claude Code or Claude.ai.

## BOOT SEQUENCE (Execute in order — do not skip)

1. Read docs/PROJECT_RULES.md       ← CONSTITUTION. Highest authority.
2. Read docs/CONTEXT_SNAPSHOT.md    ← Fast orientation
3. Read docs/MEMORY.md              ← Stable knowledge
4. Read docs/LAST_WORK_ITEMS_DONE.md ← What happened last session
5. Read docs/TODO.md                ← What to do next
6. Read docs/PERMISSIONS.md         ← What you can and cannot do
7. Read docs/TOOLS.md               ← What tools are available
8. Read docs/ARCHITECTURE.md        ← System design
9. Read docs/DECISIONS.md           ← Why things are the way they are
10. Read docs/ERRORS.md             ← Known issues to avoid

## OPERATING RULES
- Do NOT rely on chat history. The docs are your only source of truth.
- Do NOT assume context that isn't in the docs.
- Do NOT end a session without updating LAST_WORK_ITEMS_DONE.md, TODO.md, SESSION_LOG.md, and CONTEXT_SNAPSHOT.md.
- Always follow PERMISSIONS.md. No exceptions.

## CLAUDE-SPECIFIC NOTES
- Use extended thinking for architectural decisions
- Use multi-file edits for refactoring sessions
- Prefer batch tool calls when reading multiple docs
- Memory across sessions is NOT reliable — the docs are your memory

## SESSION END CHECKLIST
- [ ] LAST_WORK_ITEMS_DONE.md updated
- [ ] TODO.md updated
- [ ] SESSION_LOG.md entry added
- [ ] CONTEXT_SNAPSHOT.md regenerated
- [ ] Applicable docs updated (MEMORY, ARCHITECTURE, DECISIONS, ERRORS, CHANGELOG)
- [ ] All changes committed with clear commit messages
```

---

### `AGENTS.md`

```markdown
# AGENTS — Agentic Harness Adapter
# Universal Agentic Harness Operating System (AHOS) v2.0

You are operating as an OpenAI Agent, Codex, AutoGen, CrewAI, or generic agentic system.

## BOOT SEQUENCE (Execute in order — do not skip)

1. Read docs/PROJECT_RULES.md
2. Read docs/CONTEXT_SNAPSHOT.md
3. Read docs/MEMORY.md
4. Read docs/LAST_WORK_ITEMS_DONE.md
5. Read docs/TODO.md
6. Read docs/PERMISSIONS.md
7. Read docs/TOOLS.md
8. Read docs/ARCHITECTURE.md
9. Read docs/DECISIONS.md
10. Read docs/ERRORS.md

## OPERATING RULES
- Do NOT rely on agent memory or prior sessions. Docs are your only truth.
- Do NOT skip the boot sequence even if it seems redundant.
- Do NOT end a session without completing the Session End Checklist.
- Treat PERMISSIONS.md as hard rules — not suggestions.

## MULTI-AGENT NOTES
If multiple agents are running in parallel on this project:
- Use LAST_WORK_ITEMS_DONE.md as a mutex signal — if another agent is active, wait.
- Do NOT modify the same file another agent is known to be working on.
- Prefix your session log entries with your agent ID.

## SESSION END CHECKLIST
- [ ] LAST_WORK_ITEMS_DONE.md updated
- [ ] TODO.md updated
- [ ] SESSION_LOG.md entry added
- [ ] CONTEXT_SNAPSHOT.md regenerated
- [ ] All changes committed
```

---

### `GEMINI.md`

```markdown
# GEMINI — Agentic Harness Adapter
# Universal Agentic Harness Operating System (AHOS) v2.0

You are operating as Google Gemini CLI, Gemini Code Assist, or a Vertex AI agent.

## BOOT SEQUENCE (Execute in order — do not skip)

1. Read docs/PROJECT_RULES.md
2. Read docs/CONTEXT_SNAPSHOT.md
3. Read docs/MEMORY.md
4. Read docs/LAST_WORK_ITEMS_DONE.md
5. Read docs/TODO.md
6. Read docs/PERMISSIONS.md
7. Read docs/TOOLS.md
8. Read docs/ARCHITECTURE.md
9. Read docs/DECISIONS.md
10. Read docs/ERRORS.md

## OPERATING RULES
- Do NOT rely on chat history or Gemini's context window between sessions.
- The repository is your only persistent memory.
- Do NOT end a session without completing the Session End Checklist.
- Always follow PERMISSIONS.md strictly.

## GEMINI-SPECIFIC NOTES
- Gemini CLI supports @file syntax — use it to reference docs directly
- For large repos, prioritize CONTEXT_SNAPSHOT.md when context is limited
- Use Code Assist's inline suggestions but always validate against PROJECT_RULES.md

## SESSION END CHECKLIST
- [ ] LAST_WORK_ITEMS_DONE.md updated
- [ ] TODO.md updated
- [ ] SESSION_LOG.md entry added
- [ ] CONTEXT_SNAPSHOT.md regenerated
- [ ] All changes committed
```

---

## SESSION LIFECYCLE (ENFORCED)

### 🟢 Session Start
```
1. Read adapter file (CLAUDE.md / AGENTS.md / GEMINI.md)
2. Execute boot sequence in order
3. Confirm understanding of current state
4. State: "I have read the system. Current state: [summary]. Next action: [action]."
5. Begin work
```

### 🔄 During Work
```
- Follow PROJECT_RULES.md at all times
- Do not assume context that isn't documented
- Log significant decisions to DECISIONS.md immediately
- Log errors to ERRORS.md immediately
- Check PERMISSIONS.md before any sensitive action
```

### 🔴 Session End (MANDATORY — never skip)
```
1. Update LAST_WORK_ITEMS_DONE.md (complete handoff entry)
2. Update TODO.md (mark done, add new tasks)
3. Add entry to SESSION_LOG.md
4. Regenerate CONTEXT_SNAPSHOT.md
5. Update MEMORY.md if new stable knowledge was learned
6. Update ARCHITECTURE.md if design changed
7. Update DECISIONS.md if significant choices were made
8. Update ERRORS.md if errors occurred
9. Update CHANGELOG.md if version-worthy changes were made
10. git add . && git commit -m "[agent] [scope]: [summary]"
11. git push
```

---

## GIT COMMIT CONVENTION

Format: `[harness] [scope]: [summary]`

Examples:
```
[claude] feat: add user authentication module
[gemini] fix: resolve database connection timeout
[agents] docs: update ARCHITECTURE.md with new API routes
[claude] refactor: extract payment logic to service layer
```

---

## ANTI-PATTERNS (NEVER DO THESE)

| Anti-Pattern | Why It Breaks the System |
|---|---|
| Storing knowledge only in chat | Lost forever when session ends |
| Skipping the boot sequence | Agent operates on stale assumptions |
| Not updating LAST_WORK_ITEMS_DONE.md | Next agent starts blind |
| Committing secrets or .env files | Security catastrophe |
| Making production changes without tests | Unpredictable breakage |
| Assuming another agent's context | Cross-contamination, wrong decisions |
| Skipping PERMISSIONS.md checks | Unauthorized destructive actions |
| Not logging errors to ERRORS.md | Future agents repeat the same mistakes |

---

## INITIALIZATION TASK FOR AGENTS

### New Project
```
1. Create all files and directories listed above
2. Populate PROJECT_RULES.md with what you know about the project
3. Populate MEMORY.md with the tech stack and core assumptions
4. Populate TODO.md with known first tasks
5. Set CONTEXT_SNAPSHOT.md to "Phase: Initialization"
6. Create initial git commit
7. Ask user only for critical missing information
8. Begin work immediately
```

### Existing Project
```
1. Read CONTEXT_SNAPSHOT.md first (fastest orientation)
2. Execute full boot sequence
3. Reconstruct complete understanding from docs
4. State current understanding and confirm before proceeding
5. Continue from TODO.md
```

---

## AHOS SYSTEM VERSION

This blueprint is **AHOS v2.0**

To check system version of any project: `cat docs/PROJECT_RULES.md | grep "AHOS"`

Add to PROJECT_RULES.md: `AHOS Version: 2.0`

---

## FINAL DIRECTIVE

Begin immediately.

If system is not initialized → **initialize everything above, then start work**

If system exists → **read CONTEXT_SNAPSHOT.md, run boot sequence, continue from TODO.md**

Always leave this repository in a more complete, more organized, more resumable state than you found it.

The next agent — whether it's you, another Claude, Gemini, a local LLM, or something not yet invented — must be able to pick this up in under 60 seconds.

That is the only standard that matters.
