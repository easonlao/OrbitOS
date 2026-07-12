---
title: Reading Module
area: internal
purpose: guide
lifecycle: active
created: 2026-07-12
updated: 2026-07-12
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
- Audit reading structure, source traceability, or Insight index health.

## Capability Map

- `skills/echo-reading/book-ingest/`: the single import capability. It handles either a source file that needs chapter splitting or an already split chapter collection that needs ordered mapping.
- `skills/echo-reading/chapter-split/`: turn one prepared chapter into reading units without changing its `raw.md`.
- `skills/echo-reading/annotate/`: add a sidecar annotation without changing source text.
- `skills/echo-reading/unit-video/`: prepare a video only when its required material exists.
- `workflows/reading-prepare.md`: OrbitOS inbox, confirmation, source-sidecar, and validation bridge.

## Boundaries

- The imported echo-reading capability bundle is Agent-neutral module content, not an Agent-specific `.claude/` configuration.
- Do not install hooks, settings files, plugins, or dashboards as part of this module.
- Reading data remains in `05-阅读/`; `books/`, `progress.md`, annotations, and Insight do not become project state, knowledge, or Hindsight by default.
