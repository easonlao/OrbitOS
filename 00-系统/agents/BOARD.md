---
title: Agent 交接板
area: system
purpose: status
lifecycle: active
created: 2026-06-21
updated: 2026-06-27
tags:
  - orbitos
  - agents
  - handoff
---

# Agent 交接板

这里只记录 Agent 之间需要继续交接的 handoff 文档，不记录用户确认事项，也不记录项目总状态。

## 当前进行中的 handoff

- 暂无。

## 最近完成的 handoff

- [[handoff/data2motion-istoreos-demo|data2motion iStoreOS 模拟接手演练]]：✅ 已完成最小多 Agent 演练，并进一步真实跑通 `data2motion` 的最小 KPI build；当前已验证到协作闭环与构建闭环，未验证真机接入与浏览器视觉验收。
- [[handoff/hans-enhancement-review|Hans 模板增强方案 handoff]]：✅ 协作流程已收口，方案、审核、执行交接链完整；执行后发现的 `DNS` 泄露已转入项目 [[../../03-项目/openclash-config-tools/STATUS|STATUS]] 作为阻塞继续跟踪。

## 规则

- 需要跨 Agent 继续的工作先生成 handoff 文档。
- handoff 实例统一放在 `00-系统/agents/handoff/`。
- handoff 模板源统一放在 `.orbitos/templates/00-系统/agents/handoff/TEMPLATE.md`。
- BOARD 只负责索引当前状态，不负责承载完整反馈链。
- 接手方进入 handoff 后，先读顶部摘要区，再看审核结论与下一步动作。
- handoff 完成后把文件移入 `handoff/archive/`。
- handoff 的归档动作由最终审核方 B 执行；A 不自归档自己的 handoff。
- 若 handoff 已完成但尚未归档，BOARD 也应先把它移出“当前进行中”，避免把项目阻塞误写成协作仍未结束。
- handoff 必须经过审核把关后才能定版；提交方 A 负责写出结果，接手方 B 可以表达不同意见，最终由审核结论收口。
- 审核结论、异议和下一步动作必须直接写回 handoff 或 BOARD，不依赖用户充当传话人。

## handoff 入口

- `handoff/`
- `handoff/archive/`
