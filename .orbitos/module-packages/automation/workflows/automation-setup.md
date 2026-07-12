---
title: Automation Setup Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-11
updated: 2026-07-11
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
3. For catalog tasks, preserve the stated read scope, write scope, and prohibitions. System Check must use `.orbitos/scripts/automation-health.py`; Today Refresh must run System Check before projecting the dashboard; Weekly Review must stop at a week boundary. For a new task, present the same fields for user confirmation.
4. Create or update the task in the selected agent's external scheduler only after confirmation.
5. Run the task once manually or wait for its first run, then report the observed result.

## Shared Boundaries

- System Check and Today Refresh may write only `02-时间线/今日.md`.
- Weekly Review may write only the current `02-时间线/本周.md` and may not perform a week archive or rollover.
- Reading Candidate Scan and Reading Health Check are read-only. Their command output may be reviewed or explicitly projected into `今日.md`, but they do not write, import, or repair reading content.
- No catalog task moves, deletes, archives, ingests, creates knowledge, changes rules, or creates another scheduled task.
- Do not require an external notification channel. The user-facing result belongs in `今日.md` or `本周.md`.

## Prohibitions

- Do not create a task during onboarding.
- Do not infer cadence or scheduler ownership without user confirmation.
- Do not use a successful check as permission to modify OrbitOS beyond the task's declared projection path.
