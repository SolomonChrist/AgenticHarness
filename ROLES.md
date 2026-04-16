# ROLES

This file defines intended roles.
Live occupancy is determined by `_heartbeat/<Role>.md`.
The availability field in this file is design-time only.
It does not indicate who currently holds a live role.

## Role
Name: Chief_of_Staff
Default Availability: OPEN
Priority: CRITICAL
Can Write Main Task List: YES
Can Route Work: YES
Can Talk To Operator: YES
Can Create Project Subtasks: YES
Lease File: `_heartbeat/Chief_of_Staff.md`
Direct Message File: `_messages/Chief_of_Staff.md`
Expected Capabilities:
- orchestration
- delegation
- user communication
- proactive follow-up
- fallback execution when no specialist exists

## Role Expansion Rule

On a fresh install, this file should begin with only `Chief_of_Staff`.

Additional roles are added over time by:

- operator decision
- `Chief_of_Staff` recommendation
- project-specific needs

Roles may also be removed when they are no longer needed.

Suggested common roles to add when useful:

- Researcher
- Engineer
- Documentation
- QA
- Operations
- Calendar
- CRM
- Finance

When adding a new role, use this template:

## Role
Name:
Default Availability: OPEN
Priority:
Can Write Main Task List: NO
Can Route Work: NO
Can Talk To Operator: LIMITED
Can Create Project Subtasks: YES
Lease File: `_heartbeat/<Role>.md`
Direct Message File: `_messages/<Role>.md`
Expected Capabilities:
- 

## Claim Rules

- A bot must not act in a role until it has claimed that role.
- To claim a role, write `_heartbeat/<Role>.md`.
- Role occupancy is a lease, not a human-style checkout.
- Live occupancy is tracked by the lease file and registry, not by `Default Availability`.
- The role file should contain `Lease Expires At`.
- If a harness cannot maintain a timer, it must renew the lease on every meaningful write.
- If a role notices its own lease is stale, it must renew before continuing work.
- If the lease has expired, the role may be taken over.
- If a previous role-holder returns and finds a fresher lease, it must stand down.
