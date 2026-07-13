---
title: Agent 交接板
area: system
purpose: status
lifecycle: active
created: 2026-06-21
updated: 2026-07-13
tags:
  - orbitos
  - agents
  - handoff
---

# Agent 交接板

这里只索引仍需继续的 handoff。不记录用户确认事项，不记录项目总状态，也不记录已完成历史。

## 当前交接

- 暂无。

## 使用规则

- 每条当前交接写成：`handoff 链接 | 状态：<delegated/working/returned> | 当前负责人：<agent_id> | 下一步：<一句动作>`。
- BOARD 只索引开放 handoff；完整边界、证据和结果留在 handoff 文档。
- `delegated`、`working`、`returned` 留在 `handoff/`；完成后更新项目 `STATUS.md`、从 BOARD 移除并移入 `handoff/archive/`。
- Agent 启动时只检查自己名下的开放 handoff；只提示，不自动开始。
- 接手 Agent 通过“获取交接工作”定位任务，用户不需要提供路径。

## 入口

- `handoff/`：开放 handoff。
- `handoff/archive/`：已关闭的协作记录。
