---
title: Naming Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-15
updated: 2026-06-20
tags:
  - orbitos
  - naming
  - agent-rule
---

# Naming Rule

This rule defines stable naming for OrbitOS directories and files.

## Principles

- Names should make the system easier to read and harder for agents to misplace files.
- Human-facing names may use Chinese when it improves Obsidian reading.
- Machine-facing names use lowercase English `snake_case`.
- Do not rename user content or imported raw files just to satisfy style.
- Do not create naming variants such as `final_v2_new`, random IDs, or session IDs.

## Root Directories

Root visible OrbitOS directories use numeric prefixes to show the stable knowledge flow:

```text
00-系统
01-收件箱
02-时间线
03-项目
04-知识
05-资源
06-输出
99-归档
```

Meaning:

- `00-系统`: how OrbitOS works and how users read the system.
- `01-收件箱`: raw inputs and unprocessed material.
- `02-时间线`: today, this week, and archived timeline views.
- `03-项目`: active workspaces and project state.
- `04-知识`: confirmed, rewritten, human-readable knowledge.
- `05-资源`: reusable references and supporting materials.
- `06-输出`: Obsidian-produced outputs, drafts, articles, scripts, or publishable work.
- `99-归档`: old or closed material that should not stay active.

Rules:

- Keep root directory numbers stable. Do not renumber them for local convenience.
- Do not insert new root numbered directories without user confirmation.
- If a new root area is needed, discuss its lifecycle role first.
- Hidden/tool directories such as `.orbitos`, `.obsidian`, `.git`, and external tool folders are not part of the visible numbered flow.

## Visible Markdown

For human-facing Markdown:

- Prefer readable Chinese titles for knowledge, system guides, and user-facing notes.
- Use stable names that can be linked from Obsidian.
- Keep fixed navigation and state files uppercase when already established: `MAP.md`, `README.md`, `STATUS.md`, `ROADMAP.md`.
- Avoid date prefixes unless the note is inherently time-based.
- Fixed entry files may use a numeric prefix when their reading position must remain stable, such as `01-收件箱/00-粘贴.md`.

Examples:

```text
04-知识/01-本地运维/WSL2 安装与自定义位置迁移指引.md
03-项目/OrbitOS/STATUS.md
02-时间线/今日.md
02-时间线/归档/2026-W24.md
```

## Timeline Files

`02-时间线/` contains current timeline views and timeline snapshots.

Rules:

- `今日.md` is the current daily Dashboard.
- `本周.md` is the current ISO-week review only.
- Old weekly reviews are archived under `02-时间线/归档/YYYY-Www.md`, for example `2026-W24.md`.
- Timeline archives stay in `02-时间线/归档/`; do not move weekly snapshots to `99-归档/`.
- Weekly archive names use ISO week numbers and uppercase `W`.

## Visible Subdirectories

Stable first-level subdirectories under visible numbered root areas should also use numeric prefixes:

```text
NN-名称
```

Use this for stable reading categories, processing stages, and topic areas.

Examples:

```text
04-知识/00-草稿箱
04-知识/01-本地运维
```

Rules:

- The number expresses stable reading order, not creation time.
- Do not renumber existing stable subdirectories unless the user confirms a migration.
- Temporary raw imports may keep their original names until triage or ingest.
- Numeric prefixes for fixed entry files do not authorize renaming user-provided raw inputs.
- Project directories under `03-项目/` use the project name as the stable identifier and do not need numeric prefixes.
- Fixed system areas and external tool folders do not need numeric prefixes unless they become user-facing reading categories.
- System-specific fixed names such as `README.md`, `STATUS.md`, `MAP.md`, and project code folders follow their local convention.
- If a visible area has only loose raw material, do not invent a numbered taxonomy too early.

## Machine Files

For `.orbitos/` files:

- Use lowercase English `snake_case`.
- Use `.md` for workflows/rules/docs, `.yaml` for structured records, `.py` / `.mjs` for scripts.
- Do not use spaces, Chinese, uppercase words, or hyphens in new machine filenames unless a standard already exists.

Examples:

```text
.orbitos/workflows/progress-sync.md
.orbitos/schemas/event.schema.yaml
.orbitos/logs/events/20260615_213619_event_naming_bank_strategy.yaml
```

## Event Files

Event `id` and event filename are different:

- `id`: `evt_YYYYMMDD_HHMMSS_{agent_id}_{slug}`
- filename: `YYYYMMDD_HHMMSS_{slug}.yaml`

新 event 应由 `.orbitos/scripts/write_event.py` 生成。脚本输出 JSON-compatible YAML，避免手写结构和命名漂移。

The filename is for time sorting and file lookup. The `id` is for `related_events`.

## Raw Inputs

For `01-收件箱/` and `01-收件箱/已入库/`:

- Do not rename raw files unless the user confirms.
- Use ingest batch records to track processed status.
- If a raw filename is unclear, create a readable knowledge draft instead of rewriting the raw source.

## Projects

Project directories may contain code, apps, documents, and intermediate work.

Minimum recommended project files:

```text
AGENTS.md
STATUS.md
```

Add `ROADMAP.md` only when the project has a meaningful multi-stage route. Add README only for a releasable repository, independently usable module, or explicit user entry after applying the Markdown creation gate.

Recommended project experience file for long-lived or technical projects:

```text
docs/LESSONS-LEARNED.md
```

Architecture decisions use a stable sequence within their owning scope:

```text
docs/adr/NNNN_short_title.md
```

Project internals do not need to follow OrbitOS-wide visible directory naming, but project status files should stay stable.

When a project has both local management material and a releasable/product repository, keep them separated:

```text
03-项目/{Project}/
  AGENTS.md            # project goal, stable architecture, rules, and routing
  STATUS.md
  ROADMAP.md           # optional milestone dependencies, goals, and exits
  docs/                # reviews, research, design records, and handoffs
  repo/                # actual product/release Git repository
```

Rules:

- Keep current project control files at the project root so humans and agents can find the state without another navigation layer.
- `docs/` is for supporting development records; it is not the project status source.
- `docs/LESSONS-LEARNED.md` is the preferred home for project-specific pitfalls, operating constraints, validation lessons, and domain-scoped experience that should stay with the project.
- OrbitOS local design ADRs stay in the project `docs/adr/` layer; product repositories may define their own ADR convention when they truly need product-versioned decision history.
- `repo/` is for release/product code and its own Git history.
- A project-level `AGENTS.md` may route agents to the canonical development rules inside `repo/`, but must not copy those rules.
- Do not use symlinks or directory junctions as the routing contract across Windows, Synology, and Linux environments.
- Do not mix local status, review, or handoff files into the product repository unless the user explicitly promotes them.

## Do Not

- Do not rename existing directories for style without a migration plan.
- Do not create parallel names for the same concept.
- Do not mix human-facing Chinese names into `.orbitos/` machine paths.
- Do not use one-off timestamps for permanent knowledge notes.
