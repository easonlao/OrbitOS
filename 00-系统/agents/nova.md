---
title: Nova Agent 档案
area: system
purpose: status
lifecycle: active
created: 2026-06-13
updated: 2026-06-15T22:14
tags:
  - orbitos
  - agent
  - nova
---

# Nova Agent 档案

## 基本信息

| 字段 | 内容 |
|---|---|
| agent_id | nova |
| 部署位置 | Eason Windows desktop / HanaAgent 平台 |
| 局域网 IP | `10.10.10.70` |
| 接入方式 | local filesystem (HanaAgent sandbox) |
| OrbitOS 路径 | `E:\SynologyDrive\OrbitOS` |

## 当前定位

Nova 定位为知识管家，负责笔记整理、知识库组织和概念拆解。

## 已处理事项

| 日期 | 事项 | 结果 |
|---|---|---|
| 2026-06-13 | Agent Onboarding | 完成注册，已接入 OrbitOS |
| 2026-06-13 | 收件箱盘点 dry run | 识别 6 个簇 57 个文件，写入 triage queue |

## 经验记录

- 2026-06-13｜HanaAgent sandbox 可能无法启动 `pwsh.exe`，OrbitOS validation 需要先尝试 Node fallback，再手动校验。｜来源：Nova onboarding event｜影响：后续不要把 pwsh 当成唯一校验入口。
- 2026-06-15｜Hindsight MCP connector 在会话中途启用后，工具不会立即注入当前 agent 工具列表，需要新 session 才能直接使用 MCP tools。｜来源：Hindsight MCP recall 测试｜影响：测试 MCP 时先确认工具是否已注入；中途启用后可用 REST API 做只读验证，但下次新会话再验证 MCP 工具调用。
- 2026-06-15｜triage queue 中的 action（如 move_to_project）只代表去向建议，不包含确切目标路径。不能在用户确认前自行补全具体的归档目录或子路径名称。｜来源：用户纠正 Nova 越界补全工作日志归档路径｜影响：收件箱迁移时必须等用户确认目标路径后再移动文件。

## 踩坑

- 2026-06-13｜注册过程中直接运行 `pwsh` 和 `cmd /c pwsh` 都失败，原因是 sandbox 的 CreateProcessAsUserW 进程隔离限制。｜来源：Nova onboarding｜影响：改用 `node .orbitos/scripts/run-validation.mjs` 执行校验。
- 2026-06-13｜edit 工具参数名曾把 `newText` 写成 `new_str`，被工具 validation 拦截。｜来源：Nova onboarding｜影响：以后编辑前核对工具 schema 参数名。
- 2026-06-13｜inbox triage 报告 file_count 时仅目测估算，实际应为 57 而非 48。漏算了 书/目录下 8 个文件和 1 个脚本文件。｜来源：用户审计纠正｜影响：报告前必须用实际文件计数验证，不能目测。用 `ls` 结果逐条计数或命令行统计。
- 2026-06-15｜用户说"收拢"被误解为执行 triage 迁移；实际只需要更新今日.md 收口状态。｜来源：用户纠正｜影响：收到模糊指令时优先做最小可逆动作（读规则、确认意图），不自行扩大为批量迁移。

## 待确认来源

- 暂无。

## 规则候选

- 暂无。

## Learned Rule 使用记录

- 暂无。
