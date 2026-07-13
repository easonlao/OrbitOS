---
title: Agent Handoff Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-26
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - handoff
  - agents
---

# Agent Handoff Workflow

Agent Handoff 承接 `execution_mode=delegated` 的跨 Agent 或跨会话工作。它记录协作链，不替代项目 `STATUS.md`、event 或长期知识。

## 状态机

| 状态 | 当前负责人 | 含义 | 下一步 |
|---|---|---|---|
| `delegated` | 目标 Agent 或 `unassigned` | 已交出，尚未开始 | 接手方开始 |
| `working` | 执行 Agent | 正在处理 | 回交或关闭 |
| `returned` | `return_owner` 或指定 Agent | 本轮已完成，等待验收或下一步 | 负责人继续 |
| `closed` | 无 | 协作合同完成且项目状态已回写 | 移入归档 |

前三种状态留在 `00-系统/agents/handoff/` 并出现在 BOARD。`closed` handoff 必须立即移入 `handoff/archive/`；这是系统协作记录的收口，不需要用户额外说“归档”。

## 创建与更新

1. 确认当前工作确实需要 `execution_mode=delegated`，而不是普通项目状态更新。
2. 使用 `.orbitos/templates/00-系统/agents/handoff/TEMPLATE.md` 新建或更新 handoff。
3. frontmatter 必须填写：
   - `handoff_status`
   - `current_owner`
   - `return_owner`
   - `next_action`
4. 新交接一律从 `delegated` 开始；目标未定时使用 `current_owner: unassigned`。除非用户指定其他验收方，`return_owner` 必须是原交出 Agent。
5. 填写项目归属、目标、边界、已完成、未完成、风险、证据与接手动作。
6. 在 `00-系统/agents/BOARD.md` 当前交接区登记链接、状态、负责人和下一步。
7. 接手方真正开始时改为 `working`；本轮完成且要他人继续时改为 `returned`。用户未指定下一位负责人时，`current_owner` 默认回填 `return_owner`，并更新下一步。
8. 协作合同完成时，最后处理的 Agent 先更新项目 `STATUS.md`，再写为 `closed`、从 BOARD 移除并移入归档。
9. 在 Progress Sync 前运行 `python .orbitos/scripts/run-validation.py`。

## 最小内容

- 项目归属、路径与是否项目内任务。
- 本轮目标、范围和明确不处理项。
- 当前结论、已完成、未完成、风险与 `next_action`。
- 当前阶段、完成证据与交付合同。
- 已确认判断、待确认判断与真实执行判定。

## 状态源分工

- handoff：协作边界、负责人、状态和下一步。
- `STATUS.md`：项目当前事实、阻塞与下一步项目工作。
- event：实际操作凭证。
- BOARD：仅索引开放 handoff，不承载完整内容。

## 禁止

- 不把 direct 的简单任务包装成 handoff。
- 不把 handoff 当项目长期问题池。
- 不让已完成或已交回的记录停留在错误负责人或旧状态。
- 不把低置信度结论伪装成已确认判断。
