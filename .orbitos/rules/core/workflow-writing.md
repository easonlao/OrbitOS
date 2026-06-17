---
title: Workflow Writing Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-13
updated: 2026-06-13
tags:
  - orbitos
  - workflow
  - agent-rule
---

# Workflow Writing Rule

This rule defines how OrbitOS workflows should be written and audited.

## Required Sections

Every workflow should include:

- `目标`
- `触发条件` or `适用范围`
- `执行流程`
- `执行清单`
- `禁止`

If a workflow is read-only, state that clearly.

## Checklist Shape

Use this structure:

```markdown
## 执行清单

### 进入检查

- [ ] 已确认当前 workflow 适用
- [ ] 已读取必要输入
- [ ] 已确认当前 agent 身份和权限

### 执行检查

- [ ] 已完成核心步骤
- [ ] 已处理异常分支
- [ ] 已记录必要事实

### 退出检查

- [ ] 已写入或确认不需要写入 event
- [ ] 已刷新或确认不需要刷新人读视图
- [ ] 已运行或确认不需要运行 validation
- [ ] 已记录跳过项和原因
```

## Skip Rule

If a checklist item does not apply, do not silently ignore it.

Record it in the event checklist as:

```json
{
  "item": "已运行 validation",
  "status": "skipped",
  "note": "Startup Sync 是只读流程，本次未修改文件。"
}
```

## Event Projection

Checklist results belong in event logs, not in full inside `今日.md`.

Progress Sync event 应优先由 `.orbitos/scripts/write_event.py` 生成。Workflow 不应要求 agent 重复填写可由脚本确定的时间、ID、actor 和默认 checklist。

`今日.md` only projects:

- `failed`
- `blocked`
- skipped items the user should know about
- validation failures
- review items
- state-changing workflow summary

## Status Values

Use only:

- `done`
- `skipped`
- `failed`
- `blocked`

## Prohibitions

- Do not use checklist as a substitute for event logs.
- Do not copy complete checklists into `今日.md`.
- Do not mark skipped without a reason.
- Do not mark done when the result is only assumed.

