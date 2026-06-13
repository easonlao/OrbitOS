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
  - `.orbitos/scripts/run-validation.mjs`
- Added Agent Profile baseline:
  - `.orbitos/agents/registry.yaml`
  - `.orbitos/schemas/agent-registry.schema.yaml`
  - `00-系统/agents/README.md`
  - `00-系统/agents/codex.md`
- Added Rule Evolution workflow:
  - `.orbitos/workflows/experience-capture.md`
  - `.orbitos/workflows/rule-evolution.md`
  - `.orbitos/rules/learned/INDEX.md`
- Added Agent Onboarding workflow:
  - `.orbitos/workflows/agent-onboarding.md`
- Added workflow checklist baseline:
  - `.orbitos/rules/core/workflow-writing.md`
  - optional `checklist` field in `.orbitos/schemas/event.schema.yaml`
  - checklist eval fixture for invalid status
- Added Node.js validation fallback for agent sandboxes that cannot launch `pwsh.exe`.
- Added Agent Profile experience recall to Startup Sync, so registered agents must read their own experience, pitfalls, pending sources, and learned-rule usage before acting.
- Clarified the Progress Sync source-of-truth contract between project `STATUS.md` files and `02-时间线/今日.md`: project status is updated first when project state changes, and today only summarizes and links to it.
- Added rules pool placeholders:
  - `.orbitos/rules/core/`
  - `.orbitos/rules/learned/`
- Added core execution rules:
  - `.orbitos/rules/core/readme-writing.md`
  - `.orbitos/rules/core/doc-promotion.md`
  - `.orbitos/rules/core/git-management.md`
  - `.orbitos/rules/core/markdown-writing.md`
  - `.orbitos/rules/core/versioning.md`
- Added MIT `LICENSE`.
- Added `README.zh-CN.md`.

### Changed

- Rebuilt OrbitOS in the current repository root.
- Strengthened root `AGENTS.md` from a principle summary into an actionable agent entry with start steps, task router, stop conditions, and output expectations.
- Reorganized root `AGENTS.md` to separate workflow entries from rule entries while keeping it under the 200-line constraint.
- Added a reusable first-contact prompt for new agents: read `AGENTS.md`, run read-only Startup Sync, stop if unregistered, collect required deployment fields, then register only through Agent Onboarding after user confirmation.
- Archived the previous OrbitOS content under `99-归档/legacy-orbitos-20260611/`.
- Rewrote root README files as user onboarding pages instead of internal protocol manuals.
- Defined `02-时间线/今日.md` as the main human Dashboard.
- Defined `00-系统/` as the user-facing system manual layer.
- Defined `.orbitos/docs/` as the internal design and development documentation layer.
- Defined `.orbitos/rules/core/` as the stable agent execution rule layer.
- Defined `.orbitos/rules/learned/INDEX.md` as the shared learned-rule index, with detailed assets kept in agent profiles and events.
- Closed the Rule Evolution loop through Progress Sync: agent profile records source experience, learned index keeps the system table, `今日.md` receives review projections, and core promotion requires user confirmation.
- Added Experience Capture as the input layer before Rule Evolution, so agents know when to record pitfalls, corrections, failures, and reusable practices.
- Added workflow checklist projection rule: workflow files define checklists, events record execution results, and `今日.md` only projects exceptions, blocks, review items, and key summaries.
- Defined documentation promotion flow from `.orbitos/docs/` to `00-系统/`, with stable execution rules kept in `.orbitos/rules/core/`.
- Moved full changelog history to `.orbitos/CHANGELOG.md`.
- Reduced `00-系统/CHANGELOG.md` to current release summary only.
- Removed validation status and next-step planning from `00-系统/CHANGELOG.md`; those belong in Dashboard or internal release history.
- Rewrote `00-系统/DATA-LIFECYCLE.md` as a user-facing Obsidian folder-flow guide instead of an internal terminology page.
- Moved agent-authored Markdown constraints to `.orbitos/rules/core/markdown-writing.md` because they are execution rules rather than user-facing system understanding or design notes.

### Fixed

- Corrected README link strategy:
  - English README uses GitHub Markdown links.
  - Chinese README may use Obsidian wikilinks only for existing human-readable files.
  - Machine/internal paths use plain code paths.
- Fixed validation script behavior for JSON arrays and ISO timestamp strings.
- Fixed validation portability after Nova exposed that HanaAgent sandbox cannot start `pwsh.exe`; PowerShell and Node validation now both check the actual agent registry.

### Validation

Validation command:

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

Current validation result:

```text
Validation eval passed: 15 case(s).
```

### Migration Notes

- Use `02-时间线/今日.md` as the main user Dashboard.
- Use `00-系统/CHANGELOG.md` for current release summary.
- Use `.orbitos/CHANGELOG.md` for complete version history.
- Use `.orbitos/rules/core/versioning.md` before preparing commits, tags, or releases.

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
