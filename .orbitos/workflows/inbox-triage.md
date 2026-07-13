---
title: Inbox Triage Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - inbox
---

# Inbox Triage Workflow

Inbox Triage 是 `01-收件箱/` 的第一轮处理流程。它只盘点与提出去向建议，不移动、不删除、不创建持久化草案或知识卡片。

## 触发条件

- 用户要求整理收件箱。
- 用户丢入一批旧内容后要求盘点。
- Progress Sync 发现收件箱积压明显。
- 用户要求处理 `00-粘贴.md` 时，先由 `clipboard-flush.md` 物化条目；本 workflow 不直接消费剪贴板。

## 执行流程

1. 扫描 `01-收件箱/`，排除 `00-粘贴.md` 等固定入口文件；粘贴内容必须先经 `clipboard-flush.md` 物化为独立原件。
2. 只读取必要标题、文件名和少量内容片段，避免全量深加工。
3. 生成主题簇，并判断每个输入的存放形态：
   - `single_source`：独立文件原样入库。
   - `source_collection`：同一来源、同一主题或相互依赖的一组文件整体入库，保留原有目录结构。
   - 不按 PDF、图片、Markdown 等文件类型建立全局分类目录。
4. 为每个文件或集合生成去向建议：
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

- 不移动或删除收件箱文件。
- 不创建知识卡片、正式输出、lifecycle index 或其他持久化草案。
- 不因为文件扩展名不同而拆散同一来源集合。
