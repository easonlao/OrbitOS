---
title: Startup Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-10-03
tags:
  - orbitos
  - workflow
  - startup-sync
---

# Startup Sync Workflow

目标：最小确认身份与状态，不推进任务、不做决策、不修改任何文件。

## 流程

1. 确认 `.orbitos/`、`.orbitos/agents/registry.yaml`、`02-时间线/今日.md` 存在；缺失时停止并报告缺失项。
2. registry 中查本 agent：缺失→停止，请用户确认 `agent_id` 后走 `agent-onboarding.md`；`offboarding` / `offboarded`→停止，前者提示等待收敛，后者提示走复活判定，不静默 onboarding。
3. 读 `02-时间线/今日.md`，输出短摘要：agent_id、当前任务面板、待确认、可继续入口。

## 按需工具（不默认执行，任务或排查需要时才跑）

- 统一任务上下文（环境、工作项、维护摘要、项目入口）：`python .orbitos/scripts/task-context.py --agent-id {id}`。
- 开放 handoff：collaboration 模块为 `ready` 时 `python .orbitos/scripts/handoff-status.py --agent-id {id}`，只读不领取。
- 维护状态排查：读 `.orbitos/state/maintenance.json`，只同步状态，不自动领取或关闭。

## 禁止

- 未经用户确认自动注册 agent；registry 不可读时查看其他 agent 的 profile 或经验。
- 在本流程中推进任务、做决策或修改用户内容。
- 把完整经验或整个 vault 纳入固定冷启动读取。
