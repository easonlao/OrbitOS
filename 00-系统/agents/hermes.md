---
title: Hermes Agent 档案
area: system
purpose: status
lifecycle: active
created: 2026-06-14
updated: 2026-06-14
tags:
  - orbitos
  - agent
  - hermes
---

# Hermes Agent 档案

## 基本信息

| 字段 | 内容 |
|---|---|
| agent_id | hermes |
| display_name | Hermes |
| 当前定位 | Hermes Agent，负责通过 Ubuntu 映射文件系统接入 OrbitOS 执行协作任务。 |

## 部署信息

| 字段 | 内容 |
|---|---|
| deployment.location | Ubuntu host / Hermes Agent runtime on 10.10.10.33 |
| deployment.lan_ip | `10.10.10.33` |
| deployment.access | Ubuntu mapped filesystem |
| deployment.orbitos_path | `/home/lyx/orbitos` |
| notes | Windows Synology 同步后映射到 Ubuntu 环境；Python/Node/Git 可用，PowerShell 不可用。 |

## 最近工作

| 日期 | 事项 | 结果 |
|---|---|---|
| 2026-06-14 | Agent Onboarding | 用户确认后接入 OrbitOS。 |

## 待确认来源

- 暂无。

## 经验记录

- 2026-06-14｜本机 OrbitOS 正确挂载路径为 `/home/lyx/orbitos`，不得退回旧 `/home/lyx/orbit` 或旧 `.orbit/`。｜来源：Hermes onboarding 前置路径修复｜影响：后续 Startup Sync 和 runtime check 必须先确认 `.orbitos/` 完整。

## 踩坑

- 2026-06-14｜旧 `/home/lyx/orbit` 映射曾缺少 `.orbitos/`，导致 env-check 与 validation 被路径缺失阻塞。｜来源：Hermes runtime 测试｜影响：遇到 `.orbitos/` 缺失时立即停止并报告工作副本不完整，不得 fallback 到 `.orbit/`。
- 2026-06-14｜当前 Ubuntu 环境 PowerShell 不可用；Python、Node、Git 可用。｜来源：手动 runtime 检查｜影响：validation 优先使用 Python，必要时使用 Node fallback。

## 规则候选

- 暂无。

## Learned Rule 使用记录

- 暂无。
