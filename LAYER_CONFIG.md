# LAYER CONFIG

Version: V13
Last Updated: 2026-04-15

## Swarm Configuration

- Active Chief of Staff Role: Chief_of_Staff
- Lease Renewal Interval Minutes: 5
- Lease Expiry Threshold Minutes: 5
- Event Log Archive Policy: Monthly rollover to `_archive/last_items_done/YYYY-MM.md`
- Project Root: `Projects/`
- Heartbeat Root: `_heartbeat/`
- Direct Message Root: `_messages/`
- Human Registry File: `HUMANS.md`

## Chief Of Staff Routing Rules

- Owns the top-level task list
- Reports back to the operator
- May cover missing specialist roles temporarily
- Should recommend missing roles when repeated coverage is needed
- Should inspect adopted existing projects and propose role structure on first run

## Registry

| Role | Current Holder | Harness | Provider | Model | Session ID | Last Seen | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chief_of_Staff | unclaimed | - | - | - | - | - | OPEN |

## Notes

- Update the registry when a role is claimed, released, or taken over.
- The lease files remain the live source of truth for active bot roles.
- Additional roles should be added only when the operator and/or `Chief_of_Staff` decides they are needed.
