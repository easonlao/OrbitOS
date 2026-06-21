---
title: Learned Review Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-21
updated: 2026-06-21
tags:
  - orbitos
  - workflow
  - learned-rules
---

# Learned Review Workflow

Learned Review 用于低频整理公共经验层。

它不是单个 agent 的日常自检，而是横向审查哪些候选值得进入、更新或退出 learned index。

## 目标

- 从多个 agent 的候选和反馈中整理可共享规则。
- 更新 learned index 的状态、证据和使用结果。
- 把仍然不成熟的内容留在各自 agent experience。
- 只在真正需要时把候选推到 core 确认入口。

## 触发条件

以下情况才执行：

- 用户明确说“做一次 learned 巡检”“提炼公共规则”“看看哪些经验可以共享”。
- 定时任务按低频策略触发。

默认不在普通任务、Startup Sync 或 Progress Sync 中自动执行。

## 输入

- `.orbitos/rules/learned/INDEX.md`
- 相关 agent 的 `规则候选` 与 `Learned Rule 使用记录`
- 必要的 event 或 validation 证据

## 执行流程

1. 读取 learned index。
2. 读取目标范围内 agent experience 的 `规则候选` 和 `Learned Rule 使用记录`。
3. 初筛候选：
   - 只适用于单个 agent 的，留在对应 experience。
   - 足够通用、原子化、可执行、可验证的，进入 learned。
   - 更像 workflow 或 design note 的，不写入 learned。
4. 更新已有 learned rule：
   - 根据使用反馈更新 `last_used / result / evidence`。
   - 证据不足的可标记 `watching`。
   - 出现反例或冲突的可标记 `conflict` 或 `deprecated`。
5. 如某条 learned 已足够稳定且影响系统边界，投影到用户确认入口，等待是否进入 core。
6. 如本次修改了 learned index，按需写 event。

## 输出

- 更新后的 `.orbitos/rules/learned/INDEX.md`
- 可选 event
- 可选“建议提升 core”的待确认事项

## 与其他 Workflow 的关系

- 单个 agent 的经验整理先走 `.orbitos/workflows/agent-self-check.md`。
- 本流程需要时可使用 `.orbitos/workflows/rule-evolution.md` 的判断标准。
- 未经用户确认，不进入 core rule 修改。

## 执行清单

### 进入检查

- [ ] 已由用户要求或低频定时任务触发。
- [ ] 已确认本次需要横向整理公共经验层。
- [ ] 已读取 learned index 与必要候选。

### 执行检查

- [ ] 已完成候选初筛。
- [ ] 已更新 learned rule 的状态或反馈。
- [ ] 已把不成熟候选留在对应 agent experience。
- [ ] 如涉及 core 候选，已投影到用户确认入口。

### 退出检查

- [ ] 未把单个 agent 私有经验强行公共化。
- [ ] 未绕过用户确认提升 core。
- [ ] 如有写入，已按需留痕。

## 禁止

- 不把它当作每次工作收尾动作。
- 不因为单次成功就把经验写进 learned。
- 不把 learned index 写成长篇解释文档。
- 不在未确认前直接修改 core rules。
