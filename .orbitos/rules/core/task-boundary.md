---
title: Task Boundary Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-14
updated: 2026-06-14
tags:
  - orbitos
  - agent-rule
  - boundary
---

# Task Boundary Rule

This rule keeps agent actions scoped when the user gives a short or imprecise request.

## Default Boundary

When the user request is short, broad, or ambiguous, agents must choose the smallest reversible action that satisfies the request.

Default behavior:

- read only the minimum required context
- modify only the directly relevant file or workflow
- keep changes reversible
- run validation when system files or visible Markdown are changed
- summarize what was changed and what remains
- do not create temporary workdirs, external repository clones, downloads, or experiment outputs at the OrbitOS root

## Semantic Work Routing

Before reading or modifying task files:

1. Resolve the target work area from explicit paths, project names, referenced files, or the object named by the user.
2. Starting at the OrbitOS root, read each `AGENTS.md` that lies on the direct path to the target directory.
3. For `03-项目/{project}/`, check the project root `AGENTS.md` before `README.md` and `STATUS.md`.
4. If the project router points into a product repository or deeper work area, continue the same path-based lookup there.
5. When the task changes work area, resolve the path again before acting.

Do not scan the entire vault for `AGENTS.md`. A local file applies only to its directory tree, may add or tighten instructions, and cannot weaken root safety or confirmation boundaries.

Temporary placement:

- If the material should be visible for later user/agent review, put it under `01-收件箱/`.
- If it is disposable execution scratch, use the OS temp directory or `.orbitos/tmp/`.
- Do not create new top-level directories such as `raw/`, `.tmp-*`, `temp/`, or cloned repositories without explicit user confirmation.

## Stop And Ask

Stop and ask before:

- moving, deleting, archiving, or batch-renaming user content
- creating any new top-level directory in the OrbitOS root
- creating knowledge cards, ADRs, formal artifacts, or core rules
- changing Git tracking boundaries
- editing multiple areas when the user only named one target
- rewriting an entire file when a small patch is enough
- using project status as a source to rewrite daily Dashboard, or using Dashboard as a source to rewrite project status, without a clear state change
- falling back to old paths such as `.orbit/` when `.orbitos/` is missing

## Low-Risk Write

A low-risk write may proceed without extra confirmation when all are true:

- the user asked for the work
- the target file is clear
- no user content is moved or deleted
- no formal artifact is created
- the change is navigation, status projection, typo-level correction, or schema/workflow implementation already confirmed in conversation
- validation can be run afterward

## Self-Check Before Progress Sync

Before Progress Sync, answer these questions:

1. Did I change only the intended scope?
2. Did I move or delete user content?
3. Did I create any formal artifact, knowledge card, ADR, or core rule?
4. Did I update the correct source of truth before projecting to `今日.md`?
5. Did validation pass?
6. Did this produce a reusable experience or pitfall?

Record the result in the event checklist.

## Recovery

If an agent exceeded scope:

1. Stop immediately.
2. Do not continue with additional fixes unless needed to prevent data loss.
3. Report the exact files changed.
4. Ask the user whether to keep, adjust, or revert the extra changes.
5. Record the incident through Experience Capture.

## 禁止

- Do not treat a short user approval as permission to expand scope.
- Do not convert user material into formal knowledge without explicit confirmation.
- Do not silently correct unrelated files.
- Do not hide validation failures behind a successful partial result.
