# OrbitOS Agent 入口

OrbitOS 是一个多 agent 协作工作台。Obsidian 是人读界面，`.orbitos/` 是机器与运行时层。

本文件是所有 agent 使用 OrbitOS 的唯一入口契约，必须保持在 200 行以内。

## Startup Sync

开始任何工作前，先执行 Startup Sync：

1. 读取 `00-系统/MAP.md`、`00-系统/CONTEXT.md`、`00-系统/PRINCIPLES.md`。
2. 读取 `02-时间线/今日.md`、`02-时间线/待确认.md`、`02-时间线/下一步.md`。
3. 如果任务涉及具体项目，再读取目标项目的 `README.md` 和 `STATUS.md`。
4. 输出 5-8 行短状态摘要：当前状态、待确认事项、下一步入口。

Startup Sync 只同步状态，不推进任务，不做决策。

## Work Execution

只加载当前任务必需的最小上下文。

使用渐进式披露：

- 写入可见 Markdown 前，先读取对应区域规则。
- 只有处理具体项目时，才读取项目文件。
- 只有修改 OrbitOS 内核时，才读取 `.orbitos/AGENTS.md`。
- 没有明确需要时，不全量扫描或重写整个 vault。

## Progress Sync

完成实质性工作后，或用户说“同步”“同步进度”“更新进度”时，执行 Progress Sync。

Progress Sync 必须：

1. 至少在 `.orbitos/logs/events/` 写入一条 event。
2. 刷新相关人读视图，例如 `02-时间线/今日.md`、`待确认.md`、`下一步.md`。
3. 如果项目状态发生变化，更新项目 `STATUS.md`。
4. 对长期影响候选事项做记录，不静默提升为正式规则。

Progress Sync 不会自动写 ADR，不会自动提升规则，不会自动创建知识卡片。

## Facts And Views

`.orbitos/logs/events/` 是事实底座。

可见 Markdown 是人读视图或产物，必须可读、聚焦、可追踪。

## Git Boundary

创建新目录或生成大量内容前，先判断它是公开系统材料、用户数据还是运行时状态。

用户输入、资源、输出、归档、运行日志和本地工具状态默认不上传 Git。若新增这类路径，先更新 `.gitignore`，再写入内容。

已经被 Git 跟踪的私有文件不能只靠 `.gitignore`，需要用 `git rm --cached` 取消跟踪并保留本地文件。

## Visible Markdown

可见 Markdown 默认需要 frontmatter：

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

例外：`01-收件箱/粘贴.md` 是自由输入入口，不要求 frontmatter。

## Confirmation

以下事项必须由用户确认：

- rule candidate
- ADR candidate
- formal artifact candidate，包括知识卡片

Hindsight 不是 OrbitOS 运行必需项。若使用 Hindsight，必须记录 recall 或 retain 了什么。

## Development Boundary

如果要修改 OrbitOS 内核、schema、workflow、目录协议或系统规则，先读取：

`/.orbitos/AGENTS.md`
