---
title: OrbitOS命名与副作用规范
type: spec
topic: system
workspace: "00-系统"
created: "2026-06-07 11:00:00"
modified: "2026-06-07 11:00:00"
tags: ["spec", "orbitos", "agent"]
source: agent
status: active
---

# OrbitOS 命名与副作用规范

## 目标

让不同 Agent 看到函数、命令或 Skill 名称时，能准确判断它是否会读文件、创建内容、同步系统资产、安装机器级配置或写事件日志。

## 命名前缀

- `locate*`：只定位路径，不写文件。
- `classify*`：只做分类或路由判断，不写文件。
- `build*`：构造对象或数据结构，不写文件。
- `render*`：生成文本内容，不写文件。
- `create*`：创建用户内容文件。
- `sync*`：同步 vault 内系统资产。
- `install*`：写机器级配置，例如 Git Hook、crontab、Agent 全局配置。
- `record*`：记录事件，允许写入工作日志或 raw event log。
- `append*`：追加内容到具体文件。
- `audit*`：只检查并返回结果；只有显式 `--write-report` 才允许写报告或维护队列。

## CLI 副作用边界

- 命令名包含 `create`、`sync`、`install`、`record`、`append` 时，Agent 必须视为写操作。
- 命令名包含 `locate`、`classify`、`render`、`audit` 时，默认只读；例外必须在帮助文本和 Skill 中声明。
- 旧命令可以保留 alias，但文档必须指向新的标准命名。

## 推荐迁移

| 旧名 | 标准名 | 理由 |
|---|---|---|
| `detectWorkspace` | `locateWorkspaceByPath` | 明确是按路径定位，不是按意图分类 |
| `routeIntent` | `classifyIntentRoute` | 明确只分类，不落盘 |
| `routeCreate` | `createRoutedNote` | 明确会创建文件 |
| `ensureWorklog` | `ensureDailyWorklog` | 明确目标是每日工作日志 |
| `ensureRuntimeAssets` | `syncRuntimeTemplates` | 区分 vault 内模板同步和机器安装 |
| `installRuntime` | `installMachineRuntime` | 明确会写机器级配置 |
| `captureGitCommit` | `recordGitCommitEvent` | 统一事件记录语义 |
| `recordAgentEvent` | `recordAgentWorkEvent` | 区分 Agent 工作事件和通用事件 |

## Agent 要求

Agent 在调用 OrbitOS CLI 前，必须根据命名前缀判断副作用。写操作前应确认目标 workspace、managed path 和 local rules。
