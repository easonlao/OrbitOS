# OrbitOS Changelog

This is the full internal changelog and release history for OrbitOS.

The user-facing current release summary lives at `00-系统/CHANGELOG.md`.

## v0.1.0 - 2026-06-12

### Summary

First working OrbitOS system baseline.

This release establishes the workspace skeleton, user onboarding README, Dashboard semantics, strict schemas, validation workflow, inbox triage workflow, core-change workflow, eval script, and documentation promotion rules.

### Added

- Added root `AGENTS.md` as the single agent usage entry.
- Added `.orbitos/AGENTS.md` as the internal development and extension entry.
- Added system docs under `00-系统/`.
- Added timeline views under `02-时间线/`.
- Added strict schemas:
  - `.orbitos/schemas/event.schema.yaml`
  - `.orbitos/schemas/lifecycle.schema.yaml`
  - `.orbitos/schemas/inbox-triage.schema.yaml`
  - `.orbitos/schemas/validation-report.schema.yaml`
  - `.orbitos/schemas/core-change.schema.yaml`
- Added workflows:
  - `.orbitos/workflows/validate-sync.md`
  - `.orbitos/workflows/progress-sync.md`
  - `.orbitos/workflows/inbox-triage.md`
  - `.orbitos/workflows/core-change.md`
- Added validation eval cases under `.orbitos/evals/`.
- Added validation script:
  - `.orbitos/scripts/run-validation.ps1`
- Added internal documentation standards:
  - `.orbitos/docs/README-WRITING.md`
  - `.orbitos/docs/DOC-PROMOTION.md`
  - `.orbitos/docs/VERSIONING.md`
- Added MIT `LICENSE`.
- Added `README.zh-CN.md`.

### Changed

- Rebuilt OrbitOS in the current repository root.
- Archived the previous OrbitOS content under `99-归档/legacy-orbitos-20260611/`.
- Rewrote root README files as user onboarding pages instead of internal protocol manuals.
- Defined `02-时间线/今日.md` as the main human Dashboard.
- Defined `00-系统/` as the user-facing system manual layer.
- Defined `.orbitos/docs/` as the internal design and development documentation layer.
- Defined documentation promotion flow from `.orbitos/docs/` to `00-系统/`.
- Moved full changelog history to `.orbitos/CHANGELOG.md`.
- Reduced `00-系统/CHANGELOG.md` to current release summary only.
- Removed validation status and next-step planning from `00-系统/CHANGELOG.md`; those belong in Dashboard or internal release history.
- Rewrote `00-系统/DATA-LIFECYCLE.md` as a user-facing Obsidian folder-flow guide instead of an internal terminology page.
- Moved `00-系统/OBSIDIAN-STANDARD.md` to `.orbitos/docs/OBSIDIAN-STANDARD.md` because it constrains agent-authored Markdown rather than user-facing system understanding.

### Fixed

- Corrected README link strategy:
  - English README uses GitHub Markdown links.
  - Chinese README may use Obsidian wikilinks only for existing human-readable files.
  - Machine/internal paths use plain code paths.
- Fixed validation script behavior for JSON arrays and ISO timestamp strings.

### Validation

Validation command:

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

Current validation result:

```text
Validation eval passed: 8 case(s).
```

### Migration Notes

- Use `02-时间线/今日.md` as the main user Dashboard.
- Use `00-系统/CHANGELOG.md` for current release summary.
- Use `.orbitos/CHANGELOG.md` for complete version history.
- Use `.orbitos/docs/VERSIONING.md` before preparing commits, tags, or releases.

## Pre-release History - 2026-06-11

### Summary

Initial OrbitOS skeleton creation.

### Added

- Created OrbitOS skeleton.
- Moved legacy OrbitOS content to `99-归档/legacy-orbitos-20260611/`.
- Created root `AGENTS.md`.
- Created `.orbitos/AGENTS.md`.
- Created `.orbitos/docs/REQUIREMENTS.md`, `ARCHITECTURE.md`, and `DESIGN.md`.
- Created first versions of timeline, inbox, projects, knowledge, resources, outputs, and archive areas.
