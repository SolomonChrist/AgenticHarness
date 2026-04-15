# Agentic Harness v12.1.34 Deployment Runbook

This runbook is for packaging, installing, verifying, and operating the current production build.

## Release Baseline

Target build:
- `v12.1.34-PRODUCTION`

Validated areas:
- onboarding / FTUE
- file task execution
- research task execution
- deterministic sequential workflow execution
- mixed-runtime swarm operation
- offline 3D visualizer packaging

## Prerequisites

1. Python 3.10+
2. Required Python packages for the dashboard/runtime environment used by this build
3. At least one configured provider path:
   - OpenAI
   - LM Studio
   - Ollama
4. If using LM Studio:
   - local server enabled
   - model loaded
   - local endpoint reachable

## Fresh Install Procedure

1. Copy `MainCode` into the release/test location
2. Run:
   ```powershell
   .\INSTALL_HARNESS.bat
   ```
3. Open the dashboard
4. Hard refresh once with `Ctrl+F5`
5. Confirm the footer build number
6. Complete onboarding
7. Configure provider credentials/models as needed
8. Click `Restart Swarm`

## Recommended Post-Install Validation

Run these three tasks:

File:
```text
Create a file named ACCEPTANCE_FILE.md in the worker workspace and write exactly: Acceptance test successful.
```

Research:
```text
Use ResearchBot to research 5 practical uses of local LLMs for small businesses and save the findings in RESEARCH_ACCEPTANCE.md.
```

Sequential:
```text
Use a sequential workflow:
1. Create a file named manifest.txt containing exactly:
Version: 12.1
Status: Draft

2. Then append a new line to manifest.txt containing exactly:
SIGNED: MASTER
```

## Mixed Runtime Validation

Recommended mixed-swarm validation:
- MasterBot -> OpenAI
- ResearchBot -> OpenAI
- LocalBot1 -> LM Studio

Then run:
- local file task
- research task
- sequential task

This confirms cloud orchestration + local worker execution can coexist in one swarm.

## Provider Notes

| Provider | Status | Notes |
| :--- | :--- | :--- |
| OpenAI | Recommended | Most stable cloud path in this build |
| LM Studio | Recommended | Best local visual/offline story when the API server is running |
| Ollama | Supported | Same adapter pathway as other local providers |
| Claude / Anthropic | Integrated | Quality depends on model tier and environment |
| OpenRouter | Integrated | Quality depends on model tier and environment |

## Operations Notes

- Use `Restart Swarm` after provider changes
- Use `Open Console` as the main operator chat surface
- Use `Master Tasks` as the canonical task board
- Use `3D Visualizer` for live movement/state observation

## Offline Visualizer Note

The visualizer ships with vendored Three.js runtime files, so it does not depend on CDN availability after cloning this repo.

## Release Hygiene Checklist

- remove or revoke temporary test API keys
- verify no secrets are checked into the repo
- verify the packaged build footer version
- confirm README / runbook / known issues match the released behavior

## Known Operational Caveats

- cloud-provider task quality can vary by model tier
- advanced tool-routing flows like Obsidian/Claude Code integration may still require environment-specific setup
- UI polish may continue after launch, but the core orchestration flow is release-ready
