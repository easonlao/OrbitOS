---
title: Inbox Triage Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - workflow
  - inbox
---

# Inbox Triage Workflow

Inbox Triage 是 `01-收件箱/` 的第一轮处理流程。

它只做盘点和去向建议，不移动、不删除、不提炼为知识卡片。

## 触发条件

- 用户要求整理收件箱。
- 用户丢入一批旧内容后要求盘点。
- Progress Sync 发现收件箱积压明显。

## 输入

- `01-收件箱/*`
- 可选：用户指定的文件列表
- 可选：历史 triage queue

## 输出

- `.orbitos/queues/inbox-triage/YYYYMMDD_HHMMSS.yaml`
- `.orbitos/logs/events/YYYYMMDD_inbox_triage.yaml`
- `.orbitos/state/lifecycle-index.yaml` 的状态更新
- `02-时间线/今日.md` 的“收件箱状态”区块
- 必要时同步 `02-时间线/今日.md` 中的待确认和可继续区块

## 执行流程

1. 扫描 `01-收件箱/`，排除 `00-粘贴.md` 等固定入口文件。
2. 只读取必要标题、文件名和少量内容片段，避免全量深加工。
3. 生成主题簇。
4. 为每个文件生成去向建议：
   - `knowledge_candidate`
   - `project_material`
   - `resource_material`
   - `output_candidate`
   - `timeline_log_candidate`
   - `archive_candidate`
   - `keep_in_inbox`
   - `unclear`
5. 为每个建议写明 `reason`。
6. 生成 triage queue draft。
7. 执行 `validate-sync.md`。
8. 校验通过后写入 queue、event、lifecycle index。
9. 投影摘要到 `02-时间线/今日.md`。

## Dashboard 投影

`今日.md` 只显示摘要：

- 收件箱文件数量
- 最近盘点时间
- 主要主题簇
- 待确认去向数量
- 下一步建议
- 来源 queue / event

完整文件级建议只保留在 `.orbitos/queues/inbox-triage/`，由 agent 查询。

## 禁止

- 不移动收件箱文件。
- 不删除收件箱文件。
- 不创建知识卡片。
- 不创建正式输出。
- 不把 triage queue 当用户主入口。

