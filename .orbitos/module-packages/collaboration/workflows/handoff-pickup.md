---
title: Handoff Pickup Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-13
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - handoff
  - pickup
---

# Handoff Pickup Workflow

本 workflow 承接“获取交接工作”“接手交接”或“查看待接手任务”。它从交接板定位当前 Agent 的正式 handoff，不要求用户提供路径或文件名。

## 前置条件

- 协作模块状态为 `ready`。
- 当前 Agent 已在 registry 中，因此可识别自身 `agent_id`。

## 选择规则

1. 只读取 `00-系统/agents/BOARD.md` 的当前交接区及其链接目标。
2. 优先选择 frontmatter `current_owner` 匹配当前 `agent_id` 的开放 handoff。
3. 没有匹配项时，才考虑 `current_owner: unassigned`。
4. 只有一个候选时直接读取；多个候选时让用户选择；没有候选时报告没有可接手工作。
5. 不扫描历史归档或所有项目目录寻找任务。

## 执行流程

1. 读取候选 handoff 的状态、目标、边界、已完成、未完成、风险、待确认和 `next_action`。
2. 简要告诉用户：当前目标、已完成、仍待确认与接手后的第一步。
3. 用户明确要求开始后，写入 `handoff_status: working`，并同步 BOARD 的状态、负责人和下一步。
4. 完成本轮后：
   - 仍要另一位 Agent 继续时，写入 `returned`，把 `current_owner` 和 `next_action` 改为下一位 Agent；用户未指定下一位 Agent 时，默认交回 `return_owner` 验收。
   - 协作合同已完成时，先更新项目 `STATUS.md`，再写为 `closed`、从 BOARD 移除并移入 `handoff/archive/`。
5. 按 Progress Sync 记录实际结果并通过 validation。

## 写入边界

- “获取交接工作”本身只读，不创建、抢占、归档或改变状态。
- 只有用户明确要求开始后才进入 `working`。
- `closed` handoff 是系统协作记录；按本流程归档不需要用户额外下达“收口”或“归档”指令。
- 活动目录只保留 `delegated`、`working`、`returned`；`closed` 必须位于归档目录。

## 禁止

- 不得要求用户提供路径、handoff 文件名或目录。
- 不得在多个候选存在时静默选择。
- 不得只读标题就开始执行；必须先读取任务边界与 `next_action`。
- 不得把完成后的协作记录继续当作项目问题池。
