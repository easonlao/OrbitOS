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
- validation passes before Dashboard refresh
- failure behavior is defined

If validation fails:

1. stop the task
2. do not refresh Dashboard files
3. report the failed command and full reason
4. do not attempt broad repair

## Delivery Rules

Default delivery:

- success with no action: local only
- validation/runtime failure: notify user
- daily summary: notify user only if explicitly configured
- review-needed item: notify user or write to the agreed review location

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
- do not write OrbitOS files unless this task explicitly allows Progress Sync
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
