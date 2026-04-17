# MEMORY

Long-term markdown memory store for Agentic Harness.

Use this folder for:

- role-specific long-term memory
- human/operator long-term memory
- always-loaded standing context
- recent dated memory notes
- archived memory summaries older than 30 days

Recommended structure:

- `agents/<Role>/ALWAYS.md`
- `agents/<Role>/RECENT/YYYY-MM-DD.md`
- `agents/<Role>/ARCHIVE/YYYY-MM-summary.md`
- `humans/<HumanID>/ALWAYS.md`
- `humans/<HumanID>/RECENT/YYYY-MM-DD.md`
- `humans/<HumanID>/ARCHIVE/YYYY-MM-summary.md`

Rules:

- `LAYER_MEMORY.md` is shared swarm/project memory.
- `MEMORY/` is personal long-term memory by role or human.
- A harness taking over a role should read that role's memory before normal work.
- `Chief_of_Staff` should read the active operator's human memory before operator-facing work.
- `ALWAYS.md` should stay small and important.
- `RECENT/` should hold dated files that are still useful short-term.
- When recent memory exceeds 30 days, summarize it into `ARCHIVE/`.
- Archive summaries remain readable and should still be used for context when relevant.
