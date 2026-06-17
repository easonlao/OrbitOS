---
title: Agent 看板
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-06-17
tags:
  - orbitos
  - agents
---

# Agent 看板

这里只看当前已接入 agents 的状态入口。详细经验、踩坑和待确认来源进入各自档案。

当前仓库是发布模板，不预置任何真实 agent。第一次使用时，请让 agent 先执行 Startup Sync；如果它不在 registry 中，必须先向你确认 `agent_id`、部署位置、局域网 IP、接入方式和 OrbitOS 路径，再按 agent-onboarding workflow 注册。

## 当前 Agents

- 暂无。请通过 agent-onboarding workflow 注册第一个 agent。

## 当前运行状态

- `.orbitos/agents/registry.yaml` 当前为空。
- 第一个 agent 注册后，应在这里追加对应入口，并链接到 `00-系统/agents/{agent_id}.md`。
- 运行时环境差异、定时任务和踩坑只记录到你自己的 runtime，不作为发布模板预置内容。

## 使用规则

- 未知 agent 不允许自动注册，必须先向用户确认 `agent_id`、部署位置、局域网 IP、接入方式和 OrbitOS 路径。
- 已注册 agent 启动时必须读取自己的档案，查看经验、踩坑和待确认来源。
- agent 经验先进入单 agent 档案；跨 agent 复用的内容再通过 Rule Evolution 提炼。
- 运行时能力差异要写清楚，例如 PowerShell 是否可用、Python/Node/Git 是否可用、是否需要 SSH 或映射目录。

## 机器来源

- `.orbitos/agents/registry.yaml`
- `.orbitos/state/env/`
- `.orbitos/logs/events/`
