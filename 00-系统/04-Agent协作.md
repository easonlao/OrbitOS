---
title: Agent 协作
area: system
purpose: guide
lifecycle: active
created: 2026-06-17
updated: 2026-06-17
tags:
  - orbitos
  - guide
  - agents
---

# Agent 协作

OrbitOS 允许不同设备、平台和能力的 Agent 使用同一个工作台，但不会把它们假设成完全相同的执行者。

## Agent 身份

每个接入的 Agent 都有稳定 `agent_id` 和自己的 [[06-术语表#Agent Profile|Agent Profile]]，记录：

- 部署设备和局域网位置。
- OrbitOS 路径与接入方式。
- 可用运行环境和限制。
- 做过的重要事项。
- 自己的经验、踩坑和待确认来源。

当前 Agent 入口见 [[agents/README|Agent 看板]]。

## 第一次接入

未知 Agent 不会自动注册。它应先报告以下信息，由你确认后再注册：

- `agent_id`
- 部署位置
- 局域网 IP
- 接入方式
- OrbitOS 路径

注册完成后，Agent 才能执行写入型工作流。

## 每次开始工作

已注册 Agent 会先读取自己的轻量档案。这样 Hermes 的 Linux 限制、Nova 的平台行为和 Codex 的本地上下文不会混在一起，也不会要求你每次重新解释。

完整经验、踩坑和规则候选不作为冷启动必读；只有任务命中相关领域、出现失败返工或需要排查历史问题时，Agent 才按档案中的经验入口按需展开。

不同 Agent 可以处理共享项目，也可以只处理自己的事项。项目文件和 event 负责交接当前事实，轻量 Agent Profile 负责保留启动所需上下文，完整经验文件负责保留执行者特有经验。

## 经验如何积累

当对话中出现错误、返工、用户纠正、校验失败或明显有效做法时，Agent 先把可复用事实记录到自己的档案。

如果多个场景证明某条经验足够通用、原子化、可执行，它可以成为 learned rule；只有经过你确认，才会提升为所有 Agent 必须遵守的 [[06-术语表#Rule|core rule]]。

长篇、特定任务的方法通常更适合未来形成 Skill，而不是塞进规则。

## Hindsight 的位置

[[06-术语表#Hindsight|Hindsight]] 是可选的跨会话记忆增强层：

- Recall 可以帮助 Agent 找回长期事实和经验。
- Retain 只应保存稳定、可复用、经过确认的信息。
- OrbitOS 文件、项目状态和 [[06-术语表#Event|Event]] 仍是最终可追溯依据。
- Hindsight 不可用时，OrbitOS 仍应正常运行。

## 定时 Agent

长期在线的 Agent 可以执行只读巡检和 validation watchdog。无人值守任务默认不移动文件、不创建知识、不修改规则；发现异常时报告，由你决定是否修复。

上一页：[[03-内容生命周期]]

下一页：[[05-安全与边界]]
