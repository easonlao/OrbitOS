# Automation Module

Automation provides generic OrbitOS maintenance tasks. It defines task contracts only: the user chooses the scheduler, cadence, and executor. OrbitOS never creates a cron job by itself.

## Enablement

After an agent is onboarded, it may mention that these tasks are available. A task is configured only after the user explicitly selects its executor and schedule.

The scheduler's external configuration is the source of truth for job IDs and cadence. OrbitOS only defines what the task may read and write.

## Task Catalog

### System Check

- Purpose: run deterministic integrity checks and expose current failures in the user's main view.
- Command: `python .orbitos/scripts/automation-health.py --executor {executor}`.
- Read scope: OrbitOS runtime as required by validation.
- Write scope: the managed system-health block in `02-时间线/今日.md` and the ignored runtime state `.orbitos/state/maintenance.json`.
- Result: write a structure-layer run receipt and create/update the `system-check` maintenance item; on failure, show failed checks and keep the item open; a later passing receipt is fresh evidence that can close it.
- Prohibitions: no user-content repair, file moves, ingestion, knowledge creation, or external notification requirement.

### Today Refresh

- Purpose: rebuild the daily projection from existing state sources.
- Command: `python .orbitos/scripts/today-refresh.py --executor {executor}`.
- Read scope: current maintenance state, the latest health-check result, and existing project `STATUS.md` files for business focus. A project without `STATUS.md` is skipped.
- Write scope: only the managed `02-时间线/今日.md` markers and ignored `.orbitos/state/maintenance.json` runtime state.
- Prerequisite: run System Check first and record its result before projecting the dashboard. A failed validation is visible system state, not a reason to skip the daily projection.
- Managed blocks: `orbitos:today-date`, `orbitos:today-projection`, and `orbitos:system-health` in `02-时间线/今日.md`. Content outside these markers is preserved byte-for-byte.
- Projection links: when a projection names an existing Markdown source, use a valid Obsidian wikilink so the source is a real user-visible entry and can be checked by validation.
- Result: on either validation success or validation failure, refresh the date and the projection block from current maintenance state when preflight and source reads succeed. Keep validation failures in the health block; only rebuild the explicitly managed projection markers and remove closed/expired stale maintenance notices.
- Failure behavior: stop without rewriting the projection only when the OrbitOS preflight fails or a required source cannot be read. A failed validation alone must not stop Today Refresh.
- Prohibitions: `今日.md` is a projection, not a new source of truth; do not move, delete, ingest, or promote content.

### Weekly Review

- Purpose: produce the weekly projection from the existing review workflow.
- Read scope: event records and current state sources required by `.orbitos/workflows/weekly-review.md`.
- Write scope: only the current `02-时间线/本周.md` when it already represents the current ISO week.
- Result: update the weekly summary without changing projects, knowledge, rules, or user content. At a week boundary, stop for a user-confirmed archival run instead of moving the old weekly file.

Use `.orbitos/modules/automation/workflows/automation-setup.md` only after the user asks to configure one of these tasks.

### Reading Candidate Scan

- Purpose: identify likely books and long-form reading material in the inbox.
- Command: `python .orbitos/scripts/reading-candidate-scan.py`.
- Read scope: `01-收件箱/` only.
- Write scope: none. A caller may project the command's report into `今日.md` through an explicitly configured projection task.
- Result: reports candidates by extension and light file metadata; it does not decide that material must enter reading.
- Prohibitions: no ingest, move, book creation, Insight creation, progress update, or Hindsight retain.

### Reading Health Check

- Purpose: check reading-domain structure and traceability without interpreting or modifying reading content.
- Command: `python .orbitos/scripts/reading-health-check.py`.
- Read scope: `05-阅读/books/`, `05-阅读/insight/`, and their source sidecars.
- Write scope: none. A caller may project the command's report into `今日.md` through an explicitly configured projection task.
- Result: reports missing progress files, missing source sidecars, unresolved source paths, and Insight index drift.
- Prohibitions: no source import, link repair, Insight creation, progress update, or cross-domain promotion.
