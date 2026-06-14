---
title: OrbitOS Runtime Contract
area: internal
purpose: guide
lifecycle: active
created: 2026-06-14
updated: 2026-06-14
tags:
  - orbitos
  - runtime
  - agents
---

# OrbitOS Runtime Contract

This document defines the minimum runtime environment expected by OrbitOS agents.

## Goal

Agents may run from different devices, sandboxes, and shells. The runtime contract keeps system scripts predictable without requiring Docker or a heavy platform.

## Minimum Requirements

- Python 3.10 or newer is required for system scripts.
- Git is recommended for repository work.
- Node.js is optional and kept as validation fallback.
- PowerShell is optional and only used as a Windows wrapper.

## Workspace Integrity

Before running any OrbitOS command, the workspace must contain:

- `.orbitos/`
- `.orbitos/agents/registry.yaml`
- `.orbitos/scripts/env-check.py`
- `.orbitos/scripts/run-validation.py`
- `.orbitos/workflows/startup-sync.md`

If these paths are missing, the runtime is blocked.

Do not fall back to legacy `.orbit/`.

Do not read another agent's profile when the registry is unavailable.

This usually means the mapped workspace is stale, incomplete, or not synced to the current OrbitOS repository state.

## Standard Commands

Run environment check:

```powershell
python .orbitos/scripts/env-check.py --agent-id <agent_id>
```

Run validation:

```powershell
python .orbitos/scripts/run-validation.py
```

Windows local wrapper:

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

Node fallback:

```powershell
node .orbitos/scripts/run-validation.mjs
```

## Environment Report

`env-check.py` writes a runtime report to:

```text
.orbitos/state/env/{agent_id}.json
```

The report is runtime state and is not committed.

It records:

- `agent_id`
- `checked_at`
- `orbitos_path`
- `python`
- `node`
- `git`
- `pwsh`
- `validation_command`
- `status`

## Status

- `ok`: Python is available and the OrbitOS root looks valid.
- `degraded`: Python is available but optional tools are missing.
- `blocked`: Python is missing or the OrbitOS root is invalid.

## Common Blocked Case

If an agent sees `AGENTS.md` and `00-系统/`, but `.orbitos/` is missing, the correct result is:

```text
blocked: incomplete OrbitOS workspace
```

The agent should report:

- current working directory
- whether `.orbitos/` exists
- whether `.orbit/` exists
- Python / Node / Git / PowerShell availability, if manually checked
- that validation could not run because scripts were missing

## Rule

New OrbitOS system scripts should be written in Python by default.

PowerShell should remain a local Windows wrapper.

Node.js should remain a fallback when Python is unavailable or when a specific agent sandbox handles Node more reliably.
