# Agentic Harness v12.1.34 Known Issues

This file tracks the current known caveats for the release build.

## Runtime / Provider Caveats

1. Cloud quality is model-tier sensitive.
   - Anthropic / OpenRouter paths may connect successfully while still showing weaker autonomous execution on lower-tier models.

2. Local providers require the local server to actually be online.
   - LM Studio must have its server enabled and a model loaded.
   - If the local endpoint is unavailable, the system should fail visibly instead of pretending the task completed.

## UI / UX Polish

1. Bot Management is significantly improved from earlier builds, but may still receive further visual refinement after launch.
2. The visualizer and dashboard continue to evolve; some spacing and inspector/feed presentation may still be tuned post-release.

## Operational Notes

1. After provider changes, use `Restart Swarm`.
2. After updating the code, hard refresh the dashboard (`Ctrl+F5`) to ensure the latest UI is loaded.

## Packaging Reminder

Before pushing:
- confirm the footer version matches the intended release build
- confirm no test credentials remain
- confirm the vendored Three.js files and `THIRD_PARTY_NOTICES.md` are included
