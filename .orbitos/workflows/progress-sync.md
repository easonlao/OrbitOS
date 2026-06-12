---
title: Progress Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - workflow
  - progress-sync
---

# Progress Sync Workflow

Progress Sync 在完成实质性工作后执行，或用户说“同步”“同步进度”“更新进度”时执行。

## 目标

- 写入事实 event。
- 校验写入对象。
- 刷新 Obsidian Dashboard。
- 保持待确认、下一步、项目状态与事实层一致。

## 输入

- 用户请求或任务结果
- 已发生的文件变更
- 需要确认的事项
- 可继续的下一步
- 可选 Hindsight recall / retain 摘要

## 必填 event 字段

Progress Sync 至少生成包含以下字段的 event：

- `id`
- `timestamp`
- `actor`
- `event_type`
- `summary`
- `reason`
- `actions`
- `files_changed`
- `review_required`
- `next_steps`

## 执行流程

1. 汇总本次实质性动作。
2. 生成 event draft。
3. 执行 `validate-sync.md`。
4. 校验通过后写入 `.orbitos/logs/events/`。
5. 刷新 `02-时间线/今日.md`：
   - 当前状态
   - 今天发生
   - 正在进行
   - 待确认
   - 下一步
   - 收件箱状态
   - 项目状态
   - 系统变更
   - 来源
     - 来源只写摘要，不逐条列出 `.orbitos/logs/events/*.yaml`。
     - 如需追溯机器事实，写“机器事实记录保存在 `.orbitos/logs/events/`”即可。
6. 如果有 pending review item，同步到 `02-时间线/待确认.md`。
7. 如果有 pending / blocked next step，同步到 `02-时间线/下一步.md`。
8. 如果修改 OrbitOS 系统层，更新 `00-系统/CHANGELOG.md`。

## 禁止

- 不把完整推理过程写进 event。
- 不把未确认内容提升为规则、ADR、知识卡片或正式产物。
- 不在校验失败时刷新 Dashboard。
- 不把 Hindsight 当作 OrbitOS 必需依赖。
- 不把 event YAML 文件列表直接投影到用户 Dashboard。
