# ADR-0001：在 Product Repo 中保留决策历史

- 状态：accepted
- 日期：2026-06-19
- 范围：OrbitOS 产品架构决策

## 上下文

Architecture、Design 和项目 STATUS 会随系统演进更新，适合表达当前状态，但无法稳定保留当时的背景、备选方案和取舍。Event 能证明操作发生过，也不承担完整决策理由。

Runtime 是 Product Repo 的运行副本。如果在 Runtime 的 `00-系统/` 另建 ADR，会产生第二份权威来源。

## 决策

保留 ADR 作为产品仓库内的决策历史层。OrbitOS ADR 位于 Product Repo 的 `.orbitos/docs/adr/`，随产品 Git 历史版本化。

Runtime 不维护独立 ADR 索引。ADR 不参与默认启动读取，只在追溯重大决策或进行相关架构变更时按需加载。

## 备选方案

- 只保留 Architecture/Design：当前状态清楚，但历史理由会被覆盖。
- 只依赖 event：能追踪操作事实，但难以表达备选方案和长期取舍。
- 在 Runtime 的 `00-系统/ADR/` 保存：便于 Obsidian 阅读，但会与 Product Repo 形成双重权威来源。

## 后果

- 产品实现和决策理由使用同一 Git 历史。
- Runtime 不承担决策库维护责任，也不会增加启动读取量。
- 已接受 ADR 不改写原始理由；变化通过新 ADR 和 `superseded` 关系表达。
