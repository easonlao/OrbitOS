---
title: Scheduled Task Boundary Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-14
updated: 2026-06-17
tags:
  - orbitos
  - agent-rule
  - scheduled-task
  - boundary
---

# Scheduled Task Boundary Rule

This rule keeps unattended OrbitOS scheduled tasks narrow, predictable, and auditable.

## Default Boundary

Scheduled tasks default to read-only.

Allowed by default:

- confirm the OrbitOS root path
- confirm `.orbitos/` exists
- run runtime checks
- run validation
- read Dashboard files
- count inbox files
- report failures or summaries

Not allowed by default:

- move, delete, archive, or rename user content
- triage or reorganize the inbox
- create knowledge cards, ADRs, formal artifacts, or core rules
- modify agent registry or Agent Profiles
- modify system rules, schemas, workflows, or Git boundaries
- create, update, or delete other scheduled tasks

## Preferred Modes

Use no-agent scripts for deterministic health checks:

- validation watchdog
- runtime availability check
- path integrity check
- disk or service watchdog

Use agent scheduled tasks only when interpretation is required:

- daily read-only Startup Sync summary
- inbox count summary
- weekly event and pending-review audit

## Required Prompt Fields

Every agent scheduled task must state:

- `agent_id`
- OrbitOS root path
- expected workdir
- whether the task is read-only or write-enabled
- exact allowed files or directories for writes
- validation command
- delivery rule for normal and failure states

Do not use conversational references such as "as discussed earlier"; scheduled tasks run in fresh sessions.

## Write-Enabled Tasks

A scheduled task may write only when all are true:

- the task explicitly declares it is write-enabled
- the allowed write paths are listed
- the write is reversible or append-only
- the validation result is recorded before Dashboard refresh
- failure behavior is defined

If validation fails, follow the task-specific contract:

- System Check: update its managed health block, report the failure in that block, and stop.
- Today Refresh: keep the failure in the health block and continue refreshing its declared date and projection blocks from readable existing sources. Do not repair the validation failure or change any source of truth.
- Any task without an explicit projection exception: stop, report the failed command and full reason, and do not attempt broad repair.

## Dashboard Projection Exception

The automation catalog may explicitly allow a task to update a named managed
block in `02-时间线/今日.md` or `02-时间线/本周.md`. This is a narrow
projection exception, not permission to refresh an entire Dashboard page.

- System Check may update only the `orbitos:system-health` marker block in
  `今日.md`, including when validation fails.
- Today Refresh may update only the `orbitos:today-date` and
  `orbitos:today-projection` marker blocks declared by its task contract; it
  must preserve every byte outside those markers, including user-authored or
  manually maintained sections.
- Weekly Review may update the current ISO week's `本周.md`; it must stop at a
  week boundary and may not archive, rename, or replace a prior week without
  a user-confirmed run.
- Dashboard projection does not require an event. It must never be used to
  conceal a failed validation or to make a repair.

## Delivery Rules

The default user-facing delivery location is the Dashboard, not a separate
notification channel:

- normal System Check: update its local health block and remain silent
- failed System Check: record the failure in the health block and remain silent
  unless the scheduler owner explicitly configures a notification
- Today Refresh and Weekly Review: write their agreed Dashboard projection
- review-needed item: write only to the agreed Dashboard location or report it
  through an explicitly configured channel

Do not spam the user with normal successful watchdog runs.

## Safe OrbitOS Template

Use this boundary for OrbitOS scheduled tasks unless the user confirms otherwise:

```text
You are {agent_name}, agent_id={agent_id}.
OrbitOS root is {orbitos_root}.
The task workdir must be {orbitos_root}.

Before acting, confirm:
1. current path is {orbitos_root}
2. .orbitos/ exists
3. .orbitos/agents/registry.yaml exists
4. .orbitos/workflows/startup-sync.md exists

If any check fails, stop and report. Do not fall back to .orbit/.

Boundary:
- do not move files
- do not triage the inbox
- do not create knowledge cards
- do not modify registry
- do not modify Agent Profiles
- do not modify system rules
- do not write OrbitOS files unless this task explicitly declares a managed
  Dashboard projection path
```

## Progress Sync

If a scheduled task is allowed to write a Progress Sync event, the event checklist must record:

- scheduled_task
- read_only_or_write_enabled
- allowed_write_paths
- validation
- delivery

If the task is read-only and produces no durable change, no Progress Sync is required.

## 禁止

- Do not let a scheduled task expand its own scope.
- Do not let a scheduled task schedule another scheduled task.
- Do not use scheduled tasks to bypass user confirmation.
- Do not treat successful validation as permission to move user content.
