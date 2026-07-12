---
title: Inbox Triage Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-07-10
tags:
  - orbitos
  - workflow
  - inbox
---

# Inbox Triage Workflow

Inbox Triage 是 `01-收件箱/` 的第一轮处理流程。

它只做盘点和去向建议，不移动、不删除、不创建持久化草案、不提炼为知识卡片。

## 触发条件

- 用户要求整理收件箱。
- 用户丢入一批旧内容后要求盘点。
- Progress Sync 发现收件箱积压明显。

## 输入

- `01-收件箱/*`
- 可选：用户指定的文件列表

## 输出

- 当前会话中的文件级去向建议与理由。
- 用户确认后，转入 `inbox-ingest.md`。

Triage 本身不创建持久化草案、event 或状态索引。

## 执行流程

1. 扫描 `01-收件箱/`，排除 `00-粘贴.md` 等固定入口文件。
2. 只读取必要标题、文件名和少量内容片段，避免全量深加工。
3. 生成主题簇。
4. 为每个文件生成去向建议：
   - `knowledge_candidate`
   - `reading_candidate`
   - `project_material`
   - `resource_material`
   - `output_candidate`
   - `timeline_log_candidate`
   - `archive_candidate`
   - `keep_in_inbox`
   - `unclear`
5. 为每个建议写明 `reason`。
6. 在当前会话中按主题簇呈现建议，并明确哪些文件需要用户确认。
7. 用户确认后，直接进入 `inbox-ingest.md`；未确认时保持原文件不动。

## 禁止

- 不移动收件箱文件。
- 不删除收件箱文件。
- 不创建知识卡片。
- 不创建正式输出。
- 不创建 lifecycle index 或其他持久化草案。
