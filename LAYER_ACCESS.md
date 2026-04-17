# LAYER ACCESS

Protocol Version: 13
Last Updated: 2026-04-15
Security Level: MANAGED

## Authority

- The operator/human may override any file.
- The active `Chief_of_Staff` may manage top-level orchestration.
- Role agents may update files required by their assigned work.

## Write Rules

- `AGENTIC_HARNESS.md`: operator only
- `PROJECT.md`: operator and `Chief_of_Staff`
- `LAYER_ACCESS.md`: operator only
- `LAYER_CONFIG.md`: operator and `Chief_of_Staff`
- `LAYER_MEMORY.md`: operator, `Chief_of_Staff`, and role agents
- `LAYER_TASK_LIST.md`: operator and `Chief_of_Staff`
- `LAYER_SHARED_TEAM_CONTEXT.md`: operator and all active roles
- `LAYER_LAST_ITEMS_DONE.md`: operator and all active roles
- `ROLES.md`: operator and `Chief_of_Staff`
- `HUMANS.md`: operator and `Chief_of_Staff`
- `MEMORY/agents/<Role>/**`: operator, `Chief_of_Staff`, and the active holder of that role
- `MEMORY/humans/<HumanID>/**`: operator and `Chief_of_Staff`; specialists only if the operator or `Chief_of_Staff` intentionally shared that context
- `_heartbeat/<Role>.md`: active holder of that role
- `_messages/<Role>.md`: operator, `Chief_of_Staff`, and message sender
- `_messages/human_<HumanID>.md`: operator, `Chief_of_Staff`, and automation layers
- `Projects/<project-slug>/**`: operator, `Chief_of_Staff`, and assigned role agents

## Human Override

The operator always has final authority over:

- role assignment
- task priority
- task state
- memory entries
- role memory entries
- human/operator memory entries
- project creation

## Safety

If a bot is unsure whether it may write to a file, it should ask in `LAYER_SHARED_TEAM_CONTEXT.md` and wait for clarification.
