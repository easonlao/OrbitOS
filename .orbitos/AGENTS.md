# OrbitOS Internal Development Entry

This file is for developing or extending OrbitOS itself.

Read this only when modifying:

- directory protocols
- schemas
- workflows
- machine logs
- lifecycle rules
- system-facing Markdown rules
- `.orbitos/` internals

## Development Rules

1. Preserve the root `AGENTS.md` as the single usage entry.
2. Keep human-facing rules in `00-系统/`.
3. Keep implementation, schemas, and design docs in `.orbitos/`.
4. Record confirmed system changes in `00-系统/CHANGELOG.md`.
5. Use ADRs only for major, hard-to-reverse architecture decisions.
6. Do not promote brainstorm notes into rules without explicit confirmation.

## Design Docs

- `.orbitos/docs/REQUIREMENTS.md`: confirmed needs and constraints
- `.orbitos/docs/ARCHITECTURE.md`: system layers and object model
- `.orbitos/docs/DESIGN.md`: concrete directory and document design

## Change Flow

1. Clarify requirement.
2. Check existing docs and rules.
3. Make scoped changes.
4. Write an event log.
5. Update visible views if needed.
6. Update `CHANGELOG.md` for landed system-level changes.

