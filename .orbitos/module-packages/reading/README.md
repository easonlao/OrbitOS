---
title: Reading Module
area: internal
purpose: guide
lifecycle: active
created: 2026-07-12
updated: 2026-07-24
tags:
  - orbitos
  - reading
  - module
---

# Reading Module

This module provides shared reading capabilities for every registered OrbitOS Agent. It is not tied to Claude, Codex, or any one Agent runtime.

## When To Load

- Import a book, article, text document, or already split chapter collection.
- Continue reading, split a long chapter into reading units, annotate source text, or prepare a reading unit video.
- Deep-read a reading unit with interactive discussion.
- Audit reading structure, source traceability, or Insight index health.

## Domain Model

See `CONTEXT.md` for the complete domain model: terminology, 9-segment note structure, object relationships, state machine (unit/chapter), deep reading protocol, persistence boundaries, and key decisions.

## Capability Map

- `skills/echo-reading/book-ingest/`: the single import capability. It handles either a source file that needs chapter splitting or an already split chapter collection that needs ordered mapping.
- `skills/echo-reading/chapter-split/`: turn one prepared chapter into reading units without changing its `raw.md`.
- `skills/echo-reading/annotate/`: add a sidecar annotation without changing source text.
- `skills/echo-reading/unit-video/`: prepare a video only when its required material exists.
- `workflows/reading-prepare.md`: OrbitOS inbox, confirmation, source-sidecar, and validation bridge.
- `workflows/deep-reading.md`: interactive deep reading protocol for reading units.

## Rules

- `rules/deep-reading.md`: interaction boundaries, write permissions, and completion semantics for deep reading.

## Completion Semantics

- **Unit complete**: 2-7 segments filled during deep reading, user confirmed.
- **Chapter distilled**: all units complete + chapter-level synthesis generated.
- **Chapter deep-read**: chapter distilled + independent review passed.
- **Split complete ≠ chapter deep-read**. Skeletons alone do not mark completion.

## Boundaries

- The imported echo-reading capability bundle is Agent-neutral module content, not an Agent-specific `.claude/` configuration.
- Do not install hooks, settings files, plugins, or dashboards as part of this module.
- Reading data remains in `05-阅读/`; `books/`, `progress.md`, annotations, and Insight do not become project state, knowledge, or Hindsight by default.
- `raw.md` is read-only; no workflow may modify or delete it.
- Segments 8/9 are user-owned: the module does not invent them. The Agent may transcribe the user's confirmed wording into segment 8, or write segment 9 only when the user explicitly asks for a revisit annotation.
