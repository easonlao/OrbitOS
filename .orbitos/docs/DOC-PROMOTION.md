# Documentation Promotion Standard

This document defines how OrbitOS design discussion becomes user-facing system documentation.

## Core Rule

Design discussion, architecture exploration, implementation details, and unresolved tradeoffs start in `.orbitos/docs/`.

Only confirmed, user-facing, stable rules or explanations should be promoted into `00-系统/`.

## Layer Boundaries

### `.orbitos/docs/`

Use this layer for:

- working design notes
- requirements and constraints
- architecture alternatives
- implementation plans
- schema and workflow design rationale
- unresolved tradeoffs
- README writing standards
- documentation promotion rules

This layer is for agents and developers.

It may include implementation details, open questions, and historical reasoning.

### `00-系统/`

Use this layer for:

- user-facing system rules
- stable terminology
- readable operating principles
- data lifecycle explanations
- Obsidian writing standards
- changelog entries for landed changes
- maps to existing user-facing files

This layer is for the user reading OrbitOS in Obsidian.

It should explain the current system state, not expose raw design debate.

## Promotion Flow

```text
discussion / design draft
  -> .orbitos/docs/
  -> user confirmation
  -> rewrite from user perspective
  -> 00-系统/
  -> event log + changelog
```

## Promotion Requirements

Before moving or summarizing content into `00-系统/`, an agent must check:

1. Has the idea been confirmed by the user?
2. Is it stable enough to guide future behavior?
3. Is it written from the user's reading perspective?
4. Does it avoid internal implementation details unless the user needs them?
5. Does it point to `.orbitos/` for developer/internal details instead of duplicating them?
6. Does it avoid creating wikilinks to missing or machine-only files?

If any answer is no, keep the content in `.orbitos/docs/`.

## What Not To Promote

Do not promote these directly into `00-系统/`:

- raw brainstorm notes
- unresolved architecture alternatives
- detailed schema field lists
- detailed workflow implementation steps
- validation script internals
- queue formats
- event log examples
- machine runtime paths unless the user needs to know the boundary

Summarize these only when they become stable user-facing rules.

## Event And Changelog

Every promotion into `00-系统/` must:

- write an event under `.orbitos/logs/events/`
- update `00-系统/CHANGELOG.md` if it changes system behavior or user-facing guidance
- refresh `02-时间线/今日.md` when it changes current state

## Agent Instruction

When editing `00-系统/`, first ask:

```text
Is this a user-facing stable rule, or is it still internal design material?
```

If it is internal design material, write or update `.orbitos/docs/` instead.
