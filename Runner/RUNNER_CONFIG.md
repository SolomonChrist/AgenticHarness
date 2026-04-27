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

Runner Enabled: YES
Runner Mode: ACTIVE
Default Interval Minutes: 5
Chief_of_Staff Interval Minutes: 1
Stale Lease Check Minutes: 1
Fast Wake Poll Seconds: 1
Wake On File Change: YES
Wake On Message Change: YES
Wake On Task Change: YES
Wake On Stale Lease: YES
Allow Persistent Roles: YES
Allow Interval Roles: YES
Allow Manual Roles: YES
Launch Retry Backoff Seconds: 8
Urgent Wake Backoff Seconds: 3
Launch Failure Threshold: 3
Launch Failure Cooldown Seconds: 300
Provider Failure Cooldown Seconds: 21600
Stale Lease Storm Threshold: 5
Stale Lease Storm Window Seconds: 600
Stale Lease Storm Cooldown Seconds: 1800
Daily Check-In Enabled: YES
Daily Check-In Hour: 9
Daily All Hands Enabled: YES
Daily All Hands Interval Hours: 24
Daily All Hands Quota Retry: YES

## Notes

- `Runner Enabled: NO` is the safe template default for a brand-new install before onboarding confirms the launch plan.
- `Chief_of_Staff` should normally switch this to `YES` during first-run setup once the local harnesses are confirmed.
- `Runner Mode: DRY_RUN` means observe first, then switch to `ACTIVE` once the launch commands are real.
- For a normal first-run onboarding, `DRY_RUN` should be brief. The expected end state is `Runner Enabled: YES` and `Runner Mode: ACTIVE`.
- `Fast Wake Poll Seconds` controls how quickly the Runner notices urgent wake requests from Telegram or active roles.
- The Runner should be one daemon only.
- The Runner should not become the source of truth.
- Manual roles are valid and should not be auto-launched.
- Launch throttling should suppress repeated failed starts before they become credit drain or file-lock churn.
- `Daily All Hands` gives every automation-ready role one bounded recovery/check pass per interval. It helps quota-paused roles resume after provider access returns and keeps the operator from babysitting retries.
- `Chief_of_Staff` should maintain `Runner/HARNESS_CATALOG.md` and `Runner/ROLE_LAUNCH_REGISTRY.md` as the remembered launcher knowledge for this install.
- Recommended first run: set `Runner Enabled: YES` and keep `Runner Mode: DRY_RUN` only long enough to inspect the role decisions before using live launches.
