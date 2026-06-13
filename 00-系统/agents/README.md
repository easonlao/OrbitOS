---
title: Agent 看板
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - agents
---

# Agent 看板

这里记录已经确认接入 OrbitOS 的 agents。

这个区域回答三个问题：

1. 现在有哪些 agents。
2. 它们分别在哪里工作、如何接入 OrbitOS。
3. 它们做过什么、有哪些经验和踩坑可以复用。

## 当前 Agents

| Agent | 部署位置 | 局域网 IP | 接入方式 | 档案 |
|---|---|---|---|---|
| codex | Eason Windows desktop / Codex desktop session | 10.10.10.70 | local filesystem | [[codex]] |

## 使用规则

- 未知 agent 不允许自动注册，必须先向用户确认 `agent_id`。
- 部署位置必须记录到能让 agent 判断自己在哪里、局域网 IP 是什么、是否需要 SSH、如何访问 OrbitOS。
- agent 经验、踩坑和观察到的有效做法先进入单 agent 档案。
- 跨 agent 反复出现的经验，后续通过 Rule Evolution Workflow 提炼为 learned rule。

## 机器来源

- `.orbitos/agents/registry.yaml`
- `.orbitos/schemas/agent-registry.schema.yaml`
