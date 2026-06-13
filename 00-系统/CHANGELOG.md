---
title: 系统变更记录
area: system
purpose: record
lifecycle: active
created: 2026-06-11
updated: 2026-06-13
tags:
  - orbitos
  - changelog
---

# 系统变更记录

## 当前版本：v0.1.0

> 完整版本历史保存在 `.orbitos/CHANGELOG.md`。本页只展示当前 release 中用户需要知道的内容。

## 你需要知道的变化

- OrbitOS 已完成首个可运行系统基线。
- `02-时间线/今日.md` 是每天优先查看的当前 Dashboard。
- `00-系统/` 是用户需要阅读的系统说明书。
- `.orbitos/` 是内部运行和二次开发层，普通使用时不需要主动阅读。
- README 已改为用户上手入口，而不是内部协议说明书。
- `AGENTS.md` 已增强为 agent 上手入口：新 agent 能看到启动步骤、任务路由、停止条件和同步要求。
- `.orbitos/docs/` 只保留设计和解释文档；agent 必须遵循的稳定规则已放到 `.orbitos/rules/core/`。
- 新增 Rule Evolution 首版：agent 经验先保存在各自档案，足够通用、原子化并经讨论确认后才进入系统规则池。
- Rule Evolution 已接入 Progress Sync：经验、踩坑、规则候选和使用反馈会形成 profile -> learned index -> 今日待确认 -> core 确认的闭环。
- 新增 Experience Capture：agent 在出现错误、返工、用户纠正、validation 失败或明显有效做法时，先记录到自己的 Agent Profile，再决定是否进入规则演化。
- 根 `AGENTS.md` 已重排：工作流入口和规则入口分开，减少新 agent 误读。
- 新增 Agent Onboarding：新 agent 第一次接入时先只读同步，确认身份和部署信息后再注册。
- 新增 Node.js validation fallback：当 agent sandbox 无法启动 PowerShell 时，可运行 `.orbitos/scripts/run-validation.mjs`。
- Startup Sync 现在要求已注册 agent 行动前读取自己的 Agent Profile 经验、踩坑、待确认来源和 Learned Rule 使用记录。
- Progress Sync 明确了项目状态与今日投影的主从关系：项目 `STATUS.md` 是状态源，`今日.md` 只汇总和链接。
- 新增 workflow checklist：workflow 定义核对清单，event 记录执行结果，`今日.md` 只显示异常、阻塞、待确认和关键摘要。
- 收件箱第一轮处理方式是 triage：只盘点、粗分、给建议，不直接移动或沉淀。
- 新增 Agent 看板：`00-系统/agents/` 用于查看已接入 agents、部署位置、状态、经验和踩坑。

## 完整历史

- `.orbitos/CHANGELOG.md`
