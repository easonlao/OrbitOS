---
title: Agent 接入与状态
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-06-17
tags:
  - orbitos
  - agents
---

# Agent 接入与状态

这里是你查看已接入 Agent 及其运行状态的入口。Agent 的执行规则不放在本页，而由根 `AGENTS.md` 和对应 workflow 管理。

当前仓库是发布模板，不预置任何真实 agent。第一次使用时，请让 agent 先执行 Startup Sync；如果它不在 registry 中，必须先向你确认 `agent_id`、部署位置、局域网 IP、接入方式和 OrbitOS 路径，再按 agent-onboarding workflow 注册。

## 当前 Agents

- 暂无。请通过 agent-onboarding workflow 注册第一个 agent。

## 当前运行状态

- `.orbitos/agents/registry.yaml` 当前为空。
- 第一个 agent 注册后，应在这里追加对应入口，并链接到 `[[{agent_id}|对应 Agent 档案]]`。
- 运行时环境差异、定时任务和踩坑只记录到你自己的 runtime，不作为发布模板预置内容。

## 接入后会发生什么

- 新 Agent 会先向你确认身份和部署信息，再完成注册。
- 已注册 Agent 使用轻量档案保存定位和部署信息，完整经验按需展开。
- 运行环境差异会记录在本地，例如 Python、Node、Git、PowerShell、SSH 或映射目录是否可用。
- 跨 Agent 可复用的经验只有经过确认后才会提升为公共规则。

## 机器来源

- `.orbitos/agents/registry.yaml`
- `.orbitos/state/env/`
- `.orbitos/logs/events/`
