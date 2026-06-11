# OrbitOS Design

## Human-Facing Areas

- `00-系统/`: runtime rules and system explanations.
- `01-收件箱/`: low-friction raw input.
- `02-时间线/`: current time-based views.
- `03-项目/`: project boundary layer plus free project body.
- `04-知识/`: confirmed reusable knowledge.
- `05-资源/`: processed reference material and attachments.
- `06-输出/`: Markdown outputs produced inside Obsidian.
- `99-归档/`: lifecycle endpoint for inactive objects.

## Inbox

```text
01-收件箱/
  粘贴.md
  处理记录.md
```

`粘贴.md` is free-form and does not need frontmatter. Processing must leave an event log.

## Timeline

```text
02-时间线/
  今日.md
  本周.md
  待确认.md
  下一步.md
  归档/
```

`本周.md` is an insight view and replaces weekly review.

## Project Boundary

```text
03-项目/{project}/
  README.md
  STATUS.md
  main/
```

`README.md` and `STATUS.md` follow OrbitOS rules. `main/` follows the project's own structure.

## Markdown Frontmatter

```yaml
---
title:
area:
purpose:
lifecycle:
created:
updated:
tags:
---
```

Use `area + purpose + lifecycle`, not complex `doc_type`.

## MAP And STATUS

- `MAP.md` is navigation, not state.
- `STATUS.md` is current state, not navigation.
- Default: do not create MAP or STATUS unless conditions are met.
