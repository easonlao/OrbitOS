---
title: Markdown Writing Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-11
updated: 2026-06-20
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
- `01-收件箱/00-粘贴.md` is a free input entry and does not require frontmatter.

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

## Document Roles

Fixed-role files such as MAP, README, AGENTS, STATUS, ROADMAP, and ADR follow `.orbitos/rules/core/document-semantics.md`. This rule only adds visible Markdown formatting and linking requirements; it does not redefine their roles.

Before creating any visible Markdown, apply the Markdown creation gate in `document-semantics.md`. Do not create a new file merely because its filename or document type is conventional.

## Body

Every visible Markdown file should have one clear responsibility.

Do not put long execution traces, hidden reasoning, or implementation history into visible Markdown. Use event logs, internal docs, archive snapshots, or ADRs instead.

## Plain Language

- Write for the document's human audience before preserving internal terminology.
- Prefer ordinary Chinese descriptions when they express the same meaning; for example, use “自动检查” instead of exposing an internal validation name without explanation.
- Keep unavoidable stable terms only when they help users identify a real system object. Link the first meaningful occurrence to the matching glossary heading.
- A glossary link supplements a clear sentence; it must not be used to excuse jargon-heavy writing.

## Links

Use Obsidian wikilinks only for existing human-facing Markdown files that the user should open in Obsidian.

When visible Markdown mentions a specific existing human-facing Markdown file that the user may need to open, link it with an Obsidian wikilink instead of leaving it as plain text or an inline code path.

Examples:

- `[[../01-收件箱/示例资料|示例资料]]`
- `[[../04-知识/01-本地运维/WSL2 安装与自定义位置迁移指引|WSL2 安装与自定义位置迁移指引]]`

Use plain code paths for internal files, including:

- `.orbitos/`
- `.obsidian/`
- schemas
- scripts
- logs
- queues

This prevents Obsidian from creating blank files from accidental clicks.

## Glossary Links

Glossaries are on-demand explanation layers, not required pre-reading.

- Link system-wide OrbitOS concepts to `00-系统/06-术语表.md`.
- If a project has an explicitly confirmed glossary for genuinely specialized business or technical concepts, link those project-only terms there instead.
- Define each term in one authoritative glossary only; a project glossary may point to the system glossary but must not copy its definitions.
- When a visible Markdown page cannot avoid a scoped or technical term, link its first meaningful occurrence to the matching heading in the authoritative glossary.
- Do not create glossary entries for ordinary planning words, headings, identifiers, or phrases that are already clear from the sentence itself.
- Use a heading link such as `[[../00-系统/06-术语表#Event|Event]]`; adjust the relative path for the current file.
- Do not link every repeated occurrence. One link per term per page is normally enough.
- Do not link ordinary language merely because a matching glossary heading exists.
- Obsidian comments (`%% ... %%`) are hidden from readers and must not carry required explanations.
- Use footnotes only for context-specific clarification that does not belong in an authoritative glossary.
