# OrbitOS Internal Development Entry

This file is for developing or extending OrbitOS itself.

Read this only when modifying:

- directory protocols
- schemas
- workflows
- machine logs
- lifecycle rules
- system-facing Markdown rules
- root README positioning or writing rules
- promotion between `.orbitos/docs/` and `00-系统/`
- versioning, changelog, commit, or release rules
- Git ignore, repository boundary, or tracked-file cleanup rules
- `.orbitos/` internals

## Development Rules

1. Preserve the root `AGENTS.md` as the single usage entry.
2. Keep human-facing rules in `00-系统/`.
3. Keep implementation, schemas, and design docs in `.orbitos/`.
4. Record confirmed system changes in `00-系统/CHANGELOG.md`.
5. Use ADRs only for major, hard-to-reverse architecture decisions.
6. Do not promote brainstorm notes into rules without explicit confirmation.
7. When changing root README files, read `.orbitos/docs/README-WRITING.md` first.
8. When moving design material into `00-系统/`, read `.orbitos/docs/DOC-PROMOTION.md` first.
9. When changing OrbitOS core files, follow `.orbitos/workflows/core-change.md` and validate against `.orbitos/schemas/core-change.schema.yaml`.
10. When preparing version, changelog, commit, or release changes, read `.orbitos/docs/VERSIONING.md` first.
11. When changing Git tracking rules or creating new generated-content areas, read `.orbitos/docs/GIT-MANAGEMENT.md` first.

## Design Docs

- `.orbitos/docs/REQUIREMENTS.md`: confirmed needs and constraints
- `.orbitos/docs/ARCHITECTURE.md`: system layers and object model
- `.orbitos/docs/DESIGN.md`: concrete directory and document design
- `.orbitos/docs/README-WRITING.md`: root README audience, content, and link rules
- `.orbitos/docs/DOC-PROMOTION.md`: how internal design becomes user-facing system docs
- `.orbitos/docs/GIT-MANAGEMENT.md`: Git boundary, ignore rules, and tracked-file cleanup
- `.orbitos/docs/OBSIDIAN-STANDARD.md`: how agents write visible Obsidian Markdown
- `.orbitos/docs/VERSIONING.md`: version numbers, changelog layers, commit rules, and release flow

## Core Workflows

- `.orbitos/workflows/core-change.md`: required workflow for modifying OrbitOS core files

## Change Flow

1. Clarify requirement.
2. Check existing docs and rules.
3. Make scoped changes.
4. Write an event log.
5. Update visible views if needed.
6. Update `.orbitos/CHANGELOG.md` for full release history when version/release content changes.
7. Update `00-系统/CHANGELOG.md` only with the current release summary.
