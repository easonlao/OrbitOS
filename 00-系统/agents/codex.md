---
title: Codex Agent 档案
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-06-13
tags:
  - orbitos
  - agent
  - codex
---

# Codex Agent 档案

## 基本信息

| 字段         | 内容                                            |
| ---------- | --------------------------------------------- |
| agent_id   | codex                                         |
| 部署位置       | Eason Windows desktop / Codex desktop session |
| 局域网 IP     | `10.10.10.70`                                 |
| 接入方式       | local filesystem                              |
| OrbitOS 路径 | `E:\SynologyDrive\OrbitOS`                    |

## 当前定位

Codex 当前主要用于 OrbitOS 架构审查、文档重构、schema/workflow 编写、验证脚本和 Git 边界处理。

## 已处理事项

| 日期 | 事项 | 结果 |
|---|---|---|
| 2026-06-12 | OrbitOS 首版骨架 | 已建立目录、schema、workflow、eval 和 README 基线 |
| 2026-06-12 | Git 边界 | 已让用户内容和运行时状态默认不进入仓库 |
| 2026-06-12 | 改造路线图项目化 | 已创建 `03-项目/OrbitOS/` |
| 2026-06-12 | Agent Profile 首版 | 已创建 registry、看板和 Codex 档案 |

## 经验记录

以下内容来自 2026-06-12 这轮 OrbitOS 改造协作，只代表当前已观察到的有效做法。它们还不是 learned rule，也不是 core rule。

- 2026-06-13｜Rule Evolution 需要 Experience Capture 前置输入，否则 agent 不知道什么时候记录踩坑和经验。｜来源：用户纠正｜影响：Progress Sync 前必须自检是否需要记录经验。
- 修改 OrbitOS 内核前先读取 `.orbitos/AGENTS.md`。
- 写入可见 Markdown 前先读取 `.orbitos/rules/core/markdown-writing.md`。
- 修改 schema/workflow 后运行 `pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1`。
- 对用户内容目录先确认 Git 边界，再写入或清理。

## 踩坑

- `.gitignore` 不能让已经被 Git 跟踪的私有文件自动消失，需要 `git rm --cached`。
- 中文 README 使用 Obsidian 双链时，如果目标文件不存在，会让用户误点创建空文件。
- event 写入必须符合 schema，对象数组不能简写成字符串列表。
- 2026-06-14｜PowerShell 与 Node validation 可能在运行时文件读取上表现不同；新增校验对象后必须两套脚本都跑，不能只看 Node fallback 通过。｜来源：首个 inbox-ingest 试跑｜影响：避免 PowerShell validation 对实际 batch 读取误报或漏报。
- 2026-06-14｜局域网/映射环境可能只同步到 `AGENTS.md` 和 `00-系统/`，但缺失 `.orbitos/`；这种情况必须判定为工作副本不完整并停止，不能退回旧 `.orbit/` 或读取其他 agent profile。｜来源：Hermes runtime 测试｜影响：避免在过期映射副本上执行写入型 workflow。

## 待确认来源

- 暂无。

## 规则候选

- 可见 Markdown 不应使用指向 `.orbitos/` 的 Obsidian 双链。已落成 core 级 Markdown 写作规则和 validation eval。

## Learned Rule 使用记录

- 暂无。

## 待改进

- 用真实多 agent 接入验证 Startup Sync 和 Agent Profile 的自动更新边界。
- 用真实经验验证 Rule Evolution Workflow 和 learned rules index。
