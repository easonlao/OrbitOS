---
title: ADR Writing Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-19
updated: 2026-06-19
tags:
  - orbitos
  - adr
  - agent-rule
---

# ADR Writing Rule

ADR 保存重大决策的原因和取舍；Architecture、Design 和 STATUS 只描述当前有效状态。

## 触发条件

仅在决策同时满足以下条件时创建 ADR：

- 对架构、数据边界、运行方式或长期维护有明显影响。
- 难以回退，或未来很可能追问“为什么这样选择”。
- 存在真实备选方案与取舍。
- 用户已经确认结论。

普通实现选择、过程记录、临时方案和未决讨论不创建 ADR。

## 存放位置

- OrbitOS 产品决策：Product Repo 内 `.orbitos/docs/adr/NNNN_short_title.md`。
- 其他项目：优先遵循其版本控制仓库已有的 ADR 约定；没有约定时使用仓库内 `docs/adr/NNNN_short_title.md`。
- Runtime 项目管理目录不保存产品 ADR，也不创建第二份索引。

编号在所属目录内递增。一个决策只保留一个权威 ADR。

## 必要内容

ADR 必须简短说明：状态、日期、上下文、决策、备选方案、取舍与后果。

已接受的 ADR 不改写原始理由。决策变化时创建新 ADR，并把旧 ADR 标记为 `superseded`，互相链接。

## 边界

- ADR 不进入 Startup Sync 默认读取范围。
- ADR 必须跟随其产品仓库版本化，Runtime 只通过更新产品文件获得副本。
- Architecture/Design 更新为新现状时，不删除支持该现状的 ADR。
- Event 记录“发生了什么”，不能替代 ADR 的“为什么”。
- 未经用户确认，不得把候选决策提升为 ADR。
