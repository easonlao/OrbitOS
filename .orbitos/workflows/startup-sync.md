---
title: Startup Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-19
tags:
  - orbitos
  - workflow
  - startup-sync
---

# Startup Sync Workflow

## 目标

用最小读取确认 agent 身份、runtime 可用性和当前工作入口。Startup Sync 不推进任务，不做决策。

## 触发条件

每个 agent 新会话进入 OrbitOS 时执行一次。根 `AGENTS.md` 已提供入口和硬边界，不在这里重复读取用户说明书。

## 状态边界

Startup Sync 不修改用户内容、registry、profile、event、项目或时间线。

允许 `env-check.py` 刷新 `.orbitos/state/env/{agent_id}.json`；这是本地环境报告，不是协作状态。

## 执行流程

1. 确认以下路径存在：
   - `.orbitos/`
   - `.orbitos/agents/registry.yaml`
   - `.orbitos/workflows/startup-sync.md`
   - `02-时间线/今日.md`
2. 读取 registry，确认自己的 `agent_id`、`deployment` 和 `profile_ref`。
3. 如果当前 agent 未注册，立即停止；只询问用户确认 `agent_id`，确认后另行进入 `agent-onboarding.md`。
4. 只读取自己的轻量 profile：部署信息、当前定位、最近工作、启动关注和经验入口。
5. 不默认读取 experience 文件；仅在任务命中、失败返工或排查历史问题时按入口展开。
6. 运行 `python .orbitos/scripts/env-check.py --agent-id {agent_id}`；已有当日报告且本次只读时可以直接读取。
7. 读取 `02-时间线/今日.md`，从其中获取当前摘要、待确认和可继续入口。
8. 输出短摘要：`agent_id`、runtime 状态、当前状态、待确认和可继续入口。

## 异常处理

- 工作副本缺失必要路径：停止并报告当前路径与缺失项。
- registry 不可读：停止，不读取任何 profile 或经验文件。
- agent 未注册：停止，不创建 registry、profile 或 event。
- Python 不可用或 runtime `blocked`：停止写入型工作流并报告原因。
- 下一步仍不明确：只报告已知状态和可选入口，不扩大任务范围。

## 执行清单

### 进入检查

- [ ] 必要路径存在，当前 `agent_id` 已在 registry 中。
- [ ] 已确认 Startup Sync 不推进任务。

### 执行检查

- [ ] 只读取当前 agent 的轻量 profile，未默认展开经验文件。
- [ ] runtime 环境未 blocked。
- [ ] 默认只读 `今日.md`，其他时间线均按需展开。

### 退出检查

- [ ] 已输出短状态摘要。
- [ ] 未修改用户内容或协作状态。

## 禁止

- 未经用户确认自动注册 agent。
- registry 不可读时查看其他 agent 的 profile 或经验。
- 把用户说明书、完整经验或整个 vault 纳入固定冷启动读取。
- 在 Startup Sync 中读取项目 `AGENTS.md`、`README.md`、`STATUS.md` 或任务文件。
- 把 Startup Sync 当作任务执行、决策或 Progress Sync。
