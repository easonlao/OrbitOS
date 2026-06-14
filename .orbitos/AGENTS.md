# OrbitOS Internal Development Entry

This file is for developing or extending OrbitOS itself.

Read this only when modifying:

- directory protocols
- schemas
- workflows
- machine logs
- lifecycle rules
- system-facing Markdown rules
- stable agent execution rules
- root README positioning or writing rules
- promotion between `.orbitos/docs/`, `.orbitos/rules/`, and `00-系统/`
- versioning, changelog, commit, or release rules
- Git ignore, repository boundary, or tracked-file cleanup rules
- `.orbitos/` internals

## Development Rules

1. Preserve the root `AGENTS.md` as the single usage entry.
2. Keep human-facing rules in `00-系统/`.
3. Keep stable agent execution rules in `.orbitos/rules/core/`.
4. Keep implementation, schemas, workflows, and design docs in `.orbitos/`.
5. Record confirmed system changes in `00-系统/CHANGELOG.md`.
6. Use ADRs only for major, hard-to-reverse architecture decisions.
7. Do not promote brainstorm notes into rules without explicit confirmation.
8. When changing root README files, read `.orbitos/rules/core/readme-writing.md` first.
9. When moving design material into `00-系统/`, read `.orbitos/rules/core/doc-promotion.md` first.
10. When changing OrbitOS core files, follow `.orbitos/workflows/core-change.md` and validate against `.orbitos/schemas/core-change.schema.yaml`.
11. When preparing version, changelog, commit, or release changes, read `.orbitos/rules/core/versioning.md` first.
12. When changing Git tracking rules or creating new generated-content areas, read `.orbitos/rules/core/git-management.md` first.
13. Keep root `AGENTS.md` actionable for a newly arrived agent: start steps, task router, stop conditions, sync requirements.
14. Do not let root `AGENTS.md` become a long design document; detailed behavior belongs in linked workflows and rules.

## Design Docs

- `.orbitos/docs/README.md`: docs boundary
- `.orbitos/docs/REQUIREMENTS.md`: confirmed needs and constraints
- `.orbitos/docs/ARCHITECTURE.md`: system layers and object model
- `.orbitos/docs/DESIGN.md`: concrete directory and document design
- `.orbitos/docs/RUNTIME.md`: minimum runtime contract for agents

## Core Rules

- `.orbitos/rules/core/README.md`: rules index
- `.orbitos/rules/core/markdown-writing.md`: visible Markdown writing rules
- `.orbitos/rules/core/readme-writing.md`: root README audience, content, and link rules
- `.orbitos/rules/core/doc-promotion.md`: how internal design becomes user-facing system docs
- `.orbitos/rules/core/git-management.md`: Git boundary, ignore rules, and tracked-file cleanup
- `.orbitos/rules/core/versioning.md`: version numbers, changelog layers, commit rules, and release flow
- `.orbitos/rules/core/workflow-writing.md`: workflow checklist and audit rules
- `.orbitos/rules/core/task-boundary.md`: default scope and self-check rules for agent actions

## Core Workflows

- `.orbitos/workflows/core-change.md`: required workflow for modifying OrbitOS core files
- `.orbitos/workflows/startup-sync.md`: read-only entry workflow and unknown-agent gate
- `.orbitos/workflows/agent-onboarding.md`: workflow for registering a confirmed new agent
- `.orbitos/workflows/progress-sync.md`: required closeout workflow after substantive work
- `.orbitos/workflows/inbox-ingest.md`: workflow for moving confirmed inbox inputs into the ingested area
- `.orbitos/workflows/vault-audit.md`: workflow for auditing the inbox ingest kernel
- `.orbitos/workflows/experience-capture.md`: workflow for recording agent experience and pitfalls before rule evolution
- `.orbitos/workflows/rule-evolution.md`: workflow for extracting agent experience into learned/core rules

## Change Flow

1. Clarify requirement.
2. Check existing docs and rules.
3. Make scoped changes.
4. Write an event log.
5. Update visible views if needed.
6. Update `.orbitos/CHANGELOG.md` for full release history when version/release content changes.
7. Update `00-系统/CHANGELOG.md` only with the current release summary.
