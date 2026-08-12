---
title: Automation Setup Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-11
updated: 2026-08-09
tags:
  - orbitos
  - automation
  - scheduled-task
---

# Automation Setup Workflow

## Trigger

- User explicitly asks to configure System Check, Today Refresh, Weekly Review, Reading Candidate Scan, Reading Health Check, or another OrbitOS scheduled task.

## Process

1. Read `.orbitos/rules/core/scheduled-task-boundary.md` and the Automation task catalog.
2. Confirm the scheduler-capable agent, selected task, cadence, delivery behavior, and read/write boundary.
3. For catalog tasks, preserve the stated read scope, write scope, and prohibitions. System Check must use `.orbitos/scripts/automation-health.py`; Today Refresh must use `.orbitos/scripts/today-refresh.py`, which runs that check first, records a receipt and continues its managed projection when validation fails. Weekly Review must use `.orbitos/scripts/weekly-review.py`, which performs the user-authorized restricted auto-rollover within its declared weekly write scope (archive the old week, create the current week page, block on archive conflict) and reports success or a blocked result through the Dashboard. Only the declared maintenance-state update and managed projection rebuild are allowed; no user-content repair. Stop only for failed preflight or unreadable required sources. For a new task, present the same fields for user confirmation.
4. Create or update the task in the selected agent's external scheduler only after confirmation.
5. Run the task once manually or wait for its first run, then report the observed result.

## Shared Boundaries

- System Check and Today Refresh may write `02-时间线/今日.md` managed blocks and `.orbitos/state/maintenance.json` runtime state.
- Today Refresh may write only the `orbitos:today-date` and `orbitos:today-projection` markers, plus the health block produced by System Check. It must preserve all content outside those markers.
- Weekly Review may write only its declared restricted weekly path: `02-时间线/本周.md`, `02-时间线/归档/YYYY-Www.md`, the ignored runtime state `.orbitos/state/maintenance.json`, and the existing today Dashboard managed projection blocks. It auto-rollovers the week boundary inside this path and blocks on archive conflict instead of overwriting.
- Reading Candidate Scan and Reading Health Check are read-only. Their command output may be reviewed or explicitly projected into `今日.md`, but they do not write, import, or repair reading content.
- No catalog task moves, deletes, ingests, creates knowledge, changes rules, or creates another scheduled task. The only archive action allowed is Weekly Review's restricted `02-时间线/归档/YYYY-Www.md` rollover.
- Do not require an external notification channel. The user-facing result belongs in `今日.md` or `本周.md`; a blocked Weekly Review run is reported through the today Dashboard「需要用户决定 / 当前维护事项」entrance.

## Prohibitions

- Do not create a task during onboarding.
- Do not infer cadence or scheduler ownership without user confirmation.
- Do not use a successful check as permission to modify OrbitOS beyond the task's declared projection path.
