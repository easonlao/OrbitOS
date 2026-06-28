---
title: Agent 接入与状态
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-06-21
tags:
  - orbitos
  - agents
---

# Agent 接入与状态

这里是已接入 Agent 的看板入口。执行规则不放在本页，而由根 `AGENTS.md` 和对应 workflow 管理。

第一次使用时，让 Agent 先执行 Startup Sync；如果它不在 registry 中，先确认 `agent_id`、部署位置、局域网 IP、接入方式和 OrbitOS 路径，再按 agent-onboarding workflow 注册。

## 当前 Agents

- [[codex|Codex]]：本地工作区实现与整合 Agent。
- [[nova|Nova]]：知识整理与结构化 Agent。
- [[hermes|Hermes]]：Ubuntu 映射运行时上的审阅与协同 Agent。
- [[mimo|MiMo]]：通过 WSL 接入本地 OrbitOS 的执行 Agent。
- [[workbuddy|WorkBuddy]]：本地开发与协作 Agent，支持多角色切换。

## 当前运行状态

- `.orbitos/agents/registry.yaml` 已登记 `codex / nova / hermes / mimo / workbuddy`。
- 后续新 Agent 注册后，在这里追加入口，并链接到 `[[{agent_id}|对应 Agent 档案]]`。

## 交接入口

- `BOARD.md`：Agent 之间需要继续交接的索引。
- `handoff/`：每次交接的实例区与归档位置。
- `.orbitos/templates/00-系统/agents/handoff/TEMPLATE.md`：handoff 模板源。
- `.orbitos/templates/00-系统/agents/PROFILE-TEMPLATE.md`：新 Agent 档案模板源。
- `.orbitos/scripts/prepare_agent_onboarding.py`：registry + profile 的 onboarding 预演/写入脚本。
- `.orbitos/scripts/generate_agent_profile.py`：新 Agent 档案生成脚本。

## 接入后会发生什么

- 新 Agent 先确认身份和部署信息，再完成注册。
- 已注册 Agent 使用轻量档案保存定位和部署信息，完整经验按需展开。
- 运行环境差异记录在本地，不预置到发布模板。
- 跨 Agent 可复用的经验只有经过确认后才会提升为公共规则。

## 机器来源

- `.orbitos/agents/registry.yaml`
- `.orbitos/state/env/`
- `.orbitos/logs/events/`
