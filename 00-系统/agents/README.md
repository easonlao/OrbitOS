---
title: Agent 看板
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-06-14
tags:
  - orbitos
  - agents
---

# Agent 看板

这里只看当前已接入 agents 的状态入口。详细经验、踩坑和待确认来源进入各自档案。

## 当前 Agents

| Agent | 定位 | 部署位置 | 局域网 IP | OrbitOS 路径 | 当前注意 |
|---|---|---|---|---|---|
| [[codex]] | 架构审查、规则/workflow/schema、Git 边界 | Windows desktop / Codex desktop | `10.10.10.70` | `E:\SynologyDrive\OrbitOS` | 当前主要维护 OrbitOS 内核与验证脚本 |
| [[nova]] | 知识管家、笔记整理、收件箱盘点 | Windows desktop / HanaAgent sandbox | `10.10.10.70` | `E:\SynologyDrive\OrbitOS` | `pwsh` 可能不可用；validation 优先 Python/Node |
| [[hermes]] | 24 小时在线 agent、Ubuntu 映射环境、定时任务 | Ubuntu host / Hermes runtime | `10.10.10.33` | `/home/lyx/orbitos` | PowerShell 不可用；已创建 validation watchdog |

## 当前运行状态

- 已注册 agents：Codex、Nova、Hermes。
- Hermes validation watchdog：
  - 任务 ID：`305ca17e29ad`
  - 频率：每 60 分钟
  - workdir：`/home/lyx/orbitos`
  - 行为：成功静默，失败通知
  - 2026-06-15 需要确认周期运行稳定性。
- Nova 的 2026-06-13 收件箱 dry run 已识别 6 个主题簇、57 个文件，等待用户确认后才迁移。
- Codex 当前负责 OrbitOS 架构、规则和系统脚本收口。

## 使用规则

- 未知 agent 不允许自动注册，必须先向用户确认 `agent_id`、部署位置、局域网 IP、接入方式和 OrbitOS 路径。
- 已注册 agent 启动时必须读取自己的档案，查看经验、踩坑和待确认来源。
- agent 经验先进入单 agent 档案；跨 agent 复用的内容再通过 Rule Evolution 提炼。
- 运行时能力差异要写清楚，例如 PowerShell 是否可用、Python/Node/Git 是否可用、是否需要 SSH 或映射目录。

## 机器来源

- `.orbitos/agents/registry.yaml`
- `.orbitos/state/env/`
- `.orbitos/logs/events/`
