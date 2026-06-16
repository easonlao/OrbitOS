---
title: Markdown Writing Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-11
updated: 2026-06-15
tags:
  - orbitos
  - obsidian
  - agent-rule
---

# Markdown Writing Rule

This rule constrains how agents write visible Markdown in OrbitOS.

## Frontmatter

Visible Markdown should include:

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

Exceptions:

- `README.md` and `README.zh-CN.md` are GitHub-facing project pages and do not require frontmatter.
- `01-收件箱/粘贴.md` is a free input entry and does not require frontmatter.

## Fields

`area` describes where the file belongs:

- `system`
- `timeline`
- `inbox`
- `project`
- `knowledge`
- `resource`
- `output`
- `archive`
- `internal`

`purpose` describes what the file is doing:

- `map`
- `status`
- `rule`
- `workflow`
- `record`
- `knowledge`
- `resource`
- `output`
- `review`
- `guide`

`lifecycle` describes its current state:

- `draft`
- `active`
- `reviewed`
- `archived`

## MAP

MAP files are navigation files. They do not carry status.

Do not create MAP files by default. Create them only when an area has enough stable files that a human or agent needs a local navigation entry.

## STATUS

STATUS files describe the current state of a lifecycle object. They are not navigation files.

For projects, `03-项目/{project}/STATUS.md` is the project state source. Daily timeline files may summarize it, but should not become the authoritative project status.

Recommended structure:

```markdown
## 当前状态
## 最近变化
## 待确认
## 可继续
## 来源
```

## Body

Every visible Markdown file should have one clear responsibility.

Do not put long execution traces, hidden reasoning, or implementation history into visible Markdown. Use event logs, internal docs, archive snapshots, or ADRs instead.

## Links

Use Obsidian wikilinks only for existing human-facing Markdown files that the user should open in Obsidian.

When visible Markdown mentions a specific existing human-facing Markdown file that the user may need to open, link it with an Obsidian wikilink instead of leaving it as plain text or an inline code path.

Examples:

- `[[../01-收件箱/20260615_Hermes技能更新前PR提醒|Hermes 技能更新前 PR 提醒]]`
- `[[../04-知识/01-本地运维/WSL2 安装与自定义位置迁移指引|WSL2 安装与自定义位置迁移指引]]`

Use plain code paths for internal files, including:

- `.orbitos/`
- `.obsidian/`
- schemas
- scripts
- logs
- queues

This prevents Obsidian from creating blank files from accidental clicks.
