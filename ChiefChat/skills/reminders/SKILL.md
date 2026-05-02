# ChiefChat Skill: Reminders

Handler: `append_today_checkin_reminders`
Safety Level: deterministic-scheduler-entry

## Purpose
Capture day-of operator errands and create lightweight follow-up reminders without involving deep harnesses.

## Trigger Examples
- `Make note of my current tasks for today...`
- `Remind me in 2 minutes to check the mango`
- `Nudge me later to finish this`

## Contract
- Store reminders in `Runner/_reminders.json`.
- Keep personal errands owned by `Chief_of_Staff` unless the operator asks to delegate them.
- Reply only after the reminder or checklist record has been written.

