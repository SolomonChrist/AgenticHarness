# Agentic Harness v12.1.34

**The Universal Standard for Autonomous AI Agent Swarms**

Agentic Harness is a local-first multi-bot orchestration system with:
- guided first-time onboarding
- a dashboard for configuration, tasking, and recovery
- mixed-runtime support across cloud and local models
- an offline-capable 3D swarm visualizer

This build is the production-ready continuation of the earlier V11 concept, now upgraded with onboarding, runtime switching, bot management, visual state monitoring, and a cleaner operator workflow.

## Why It Exists

Agentic Harness started as a practical response to real production friction:
- fragmented agent platforms
- weak session continuity
- poor visibility into what digital staff were actually doing
- too much orchestration complexity pushed onto the operator

This release keeps the original goal intact: put the complexity in the system, not in your workflow.

## What This Version Adds

- First-use onboarding that creates a working starter swarm
- Dashboard-led configuration for MasterBot and worker bots
- `Restart Swarm` recovery flow directly in the header
- compact floating `Operator Console` as the main chat surface
- 3D Visualizer with live bot state, motion, labels, and offline Three.js packaging
- mixed-provider swarms, including OpenAI + LM Studio combinations
- improved task reliability for:
  - file creation
  - research tasks
  - deterministic sequential workflows

## Supported Runtime Matrix

| Provider / Harness | Status | Recommendation | Notes |
| :--- | :--- | :--- | :--- |
| OpenAI | Supported | Primary | Best cloud orchestration path tested in this release. |
| LM Studio | Supported | Primary | Best local/offline path when the local API server is running. |
| Ollama | Supported | Primary | Local model path supported by the same provider adapter flow. |
| Claude / Anthropic | Integrated | Capability-sensitive | Works, but real task quality depends on accessible model tier and environment setup. |
| OpenRouter | Integrated | Capability-sensitive | Connected and usable, but execution quality depends on model tier. |
| Claude Code harness | Integrated | Advanced | Installed/callable on supported systems; best treated as an advanced runtime surface. |

## Works With

Agentic Harness is designed to stay model- and runtime-flexible:
- OpenAI
- LM Studio
- Ollama
- Claude / Anthropic
- OpenRouter
- Claude Code

Mixed-provider swarms are supported, so orchestration and worker execution do not have to come from the same runtime.

## Quick Start

1. Run the installer:
   ```powershell
   .\INSTALL_HARNESS.bat
   ```

2. Open the dashboard:
   - default URL: `http://localhost:5000`

3. Complete onboarding:
   - choose or create your workspace
   - let the starter swarm be generated
   - configure providers if needed

4. Use the header controls:
   - `Quick Start` for the guided walkthrough
   - `Open Console` for the floating operator chat window
   - `Restart Swarm` to reload the daemon fleet after configuration changes

## First Launch Flow

On a fresh install, the intended flow is:

1. Connect or create a workspace
2. Complete the FTUE onboarding
3. Configure providers for the bots you want to use
4. Restart the swarm
5. Submit a task from the floating operator console
6. Watch live state in:
   - `Master Tasks`
   - `Swarm Status`
   - `3D Visualizer`

## Recommended Acceptance Tests

Use these exact prompts after onboarding:

File task:
```text
Create a file named ACCEPTANCE_FILE.md in the worker workspace and write exactly: Acceptance test successful.
```

Research task:
```text
Use ResearchBot to research 5 practical uses of local LLMs for small businesses and save the findings in RESEARCH_ACCEPTANCE.md.
```

Sequential task:
```text
Use a sequential workflow:
1. Create a file named manifest.txt containing exactly:
Version: 12.1
Status: Draft

2. Then append a new line to manifest.txt containing exactly:
SIGNED: MASTER
```

Mixed swarm test:
- MasterBot -> OpenAI
- ResearchBot -> OpenAI
- LocalBot1 -> LM Studio

## Dashboard Surfaces

- `Command Center`: high-level operator landing area
- `Master Tasks`: source of truth for queued, active, blocked, and done work
- `Swarm Status`: specialist state and pulse view
- `3D Visualizer`: live animated world view of the bot staff
- `Bot Management`: inspect bot identity, provider setup, and managed files
- `Configuration`: system-level controls and recovery utilities

## 3D Visualizer

The visualizer is part of this release and is designed to work offline after cloning the repo.

It currently supports:
- live bot state and status coloring
- animated bot movement
- labels above each bot showing current work/focus
- camera reset
- calmer motion mode for long sessions

## Third-Party Runtime Notes

- The 3D Visualizer vendors a local copy of `three.module.js` and `OrbitControls.js`
- This allows the visualizer to load without CDN access
- Three.js is MIT-licensed
- See `THIRD_PARTY_NOTICES.md` for release notices

## Repo Layout

- `core/`: runtime logic, daemons, provider adapter, dashboard, onboarding, visualizer
- `core/dashboard/vendor/three/`: vendored offline Three.js runtime
- `design/`: design and architecture materials
- `INSTALL_HARNESS.bat`: recommended installer entry point
- `setup.py`: workspace generation/bootstrap logic
- `README.md`: release overview and onboarding guide
- `DEPLOYMENT_RUNBOOK.md`: deployment and runtime operations
- `KNOWN_ISSUES.md`: current caveats

## Version Lineage

| Version | Meaning |
| :--- | :--- |
| V11 | Original public concept: universal harness framing, worlds, and protocol-first direction |
| V12 | Transition into a dashboard-led, runtime-switching, production-focused harness |
| v12.1.34 | Current production build with onboarding, mixed-runtime orchestration, offline 3D visualizer, and launch-ready operator surfaces |

## Launch Notes

Before pushing or distributing:
- revoke temporary test API keys
- confirm no secrets are stored in workspace config files you intend to publish
- verify the dashboard footer version matches the build you want to ship
- run one final clean install + onboarding pass

## Official Links

- [AgenticHarness.io](https://AgenticHarness.io)
- [SolomonChrist.com](https://SolomonChrist.com)

Built for visible orchestration, truthful automation, and a more human way to work with digital staff.

The complexity is in the system. Not in your workflow.
