# RUNNER CONFIG

Configuration for the optional Agentic Harness Runner daemon.

## Purpose

This file defines how the single Runner daemon should behave.

The Runner should read this file together with:

- `ROLES.md`
- `LAYER_CONFIG.md`
- `_heartbeat/`
- `Runner/ROLE_LAUNCH_REGISTRY.md`
- `Runner/HARNESS_CATALOG.md`

## Global Settings

Runner Enabled: NO
Runner Mode: DRY_RUN
Default Interval Minutes: 5
Chief_of_Staff Interval Minutes: 2
Stale Lease Check Minutes: 1
Wake On File Change: YES
Wake On Message Change: YES
Wake On Task Change: YES
Wake On Stale Lease: YES
Allow Persistent Roles: YES
Allow Interval Roles: YES
Allow Manual Roles: YES

## Notes

- `Runner Enabled` should remain `NO` until the daemon is actually implemented and intentionally started.
- `Runner Mode: DRY_RUN` means the design is documented but not active.
- The Runner should be one daemon only.
- The Runner should not become the source of truth.
- Manual roles are valid and should not be auto-launched.
- `Chief_of_Staff` should maintain `Runner/HARNESS_CATALOG.md` and `Runner/ROLE_LAUNCH_REGISTRY.md` as the remembered launcher knowledge for this install.
- Recommended first run: set `Runner Enabled: YES` and keep `Runner Mode: DRY_RUN` to inspect the role decisions before using live launches.
