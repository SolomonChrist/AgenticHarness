# ChiefChat Skill: Web Research

Handler: `try_browser_research`, `evidence_fallback_reply`
Safety Level: source-gathering-with-task-trace

## Purpose
Answer current-info and web lookup requests with sourced evidence while preserving a durable `TASK-WEB-*` trail.

## Trigger Examples
- `What events are happening in Toronto tonight?`
- `Why is there a lineup at Bloor and Bathurst?`
- `Find a lunch place near me`
- `Research this GitHub repo`

## Contract
- Create a `TASK-WEB-*` task before browser/search work.
- Prefer source APIs, official pages, and alternate sources when automation-hostile websites block access.
- Do not return only `I'm checking` if evidence exists.
- If automation is blocked, name the blocked source, name the alternate source used, and leave the task open for Researcher if needed.

