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
- validation 主实现已切换为 Python；PowerShell 保留为 Windows 本地 wrapper，Node 继续作为 fallback。
- 新增 agent 运行环境检查：agent 可运行 `.orbitos/scripts/env-check.py` 生成本地 runtime 报告，确认 Python、Node、Git、PowerShell 等可用性。
- 新增默认任务边界规则：用户给短指令时，agent 默认只做最小可逆动作，Progress Sync 需要记录是否越界、是否移动用户内容、是否创建正式产物、validation 是否通过。
- 新增定时任务边界规则：Hermes 这类无人值守任务默认只读，写入型定时任务必须明确允许写哪些路径，失败时只报告不自动扩权修复。
- 明确 `今日.md` 的时间边界：只展开当天发生的关键事实、当前待确认和下一步；跨日历史完成项应进入本周、项目状态或 event log，不再堆积在今日。
- 新增本周回顾工作流：`本周.md` 必须先按 event 时间线展示本周核心工作，再做主题总结、风险和下周聚焦。
- 新增本周归档规则：`本周.md` 只展示当前 ISO 周；更新当前周前必须把旧周保存到 `02-时间线/归档/YYYY-Www.md`。
- Startup Sync 现在要求已注册 agent 行动前读取自己的 Agent Profile 经验、踩坑、待确认来源和 Learned Rule 使用记录。
- Progress Sync 明确了项目状态与今日投影的主从关系：项目 `STATUS.md` 是状态源，`今日.md` 只汇总和链接。
- 新增 workflow checklist：workflow 定义核对清单，event 记录执行结果，`今日.md` 只显示异常、阻塞、待确认和关键摘要。
- 收件箱第一轮处理方式是 triage：只盘点、粗分、给建议，不直接移动或沉淀。
- 新增收件箱入库最小内核：已确认处理的原始输入进入 `01-收件箱/已入库/`，避免重复扫描。
- 新增入库自检：系统会检查已入库文件是否有批次记录、批次记录指向的文件是否存在。
- 新增知识草稿流程：已入库原始输入保留在 `01-收件箱/已入库/`，agent 另行转写到 `04-知识/00-草稿箱/` 作为 `draft`，用户确认后才移入 `04-知识/{NN-主题目录}/` 并变为 `active`。
- 新增可见 Markdown 链接约束：人读视图点名现有可见 Markdown 文件时必须使用 Obsidian 双链，避免用户在 Obsidian 中手动找文件；内部 `.orbitos/` 路径仍使用普通代码路径。
- 新增 workflow 解耦约定：Progress Sync 必须做经验自检，但通过 `not_applicable / captured / candidate_only / learned_updated` 区分结果，不再把每次同步都强制串到 Experience Capture 或 Rule Evolution。
- 新增 Hindsight Bridge 试点流程：先使用 `orbitos-test` 测试 bank，retain 必须使用结构化输入、tag 白名单和 event 审计，避免污染现有 `eason` bank。
- 新增 Hindsight MCP 试点验证结论：`orbitos-test` single-bank MCP recall / retain 可用，传输层能隔离 bank；正式主 bank 将新建，当前局域网可信部署暂不要求认证。
- 新增 event 文件命名约束：从 2026-06-15 起，新 event 文件统一使用 `YYYYMMDD_HHMMSS_slug.yaml`，不再使用 `evt_` 前缀或连字符。
- 新增命名规则：根目录和稳定一级子目录用数字前缀表达稳定阅读顺序；人读笔记可以使用中文标题，机器层文件使用英文小写 snake_case。
- 新增项目目录约定：项目本地管理材料放在 `main/`，实际 release/product Git 仓库放在 `repo/`，避免把状态、handoff 和发布仓库混在一起。
- 明确 `02-时间线/归档/` 只保存旧时间线视图快照，不等同于全局 `99-归档/`。
- 新增 Agent 看板：`00-系统/agents/` 用于查看已接入 agents、部署位置、状态、经验和踩坑。

## 完整历史

- `.orbitos/CHANGELOG.md`
