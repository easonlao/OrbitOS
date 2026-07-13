---
title: Handoff Pickup Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-13
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - handoff
  - pickup
---

# Handoff Pickup Workflow

本 workflow 承接“获取交接工作”“接手交接”或“查看待接手任务”。它让当前 Agent 自然定位可接手的 handoff，而不要求用户提供目录、文件名或路径。

## 前置条件

- 协作模块状态为 `ready`。
- 当前 Agent 已在 registry 中，因此可识别自身 `agent_id`。

## 输入

- 当前 Agent 的 `agent_id`。
- `00-系统/agents/BOARD.md` 的“当前进行中的 handoff”区块。
- 被交接板指向的候选 handoff 文档。

只从交接板列出的当前 handoff 开始定位；不得为寻找交接而扫描整个 vault、历史归档或所有项目目录。

## 选择规则

1. 优先选择 `交给谁` 明确匹配当前 `agent_id` 的 handoff。
2. 若没有明确匹配项，才考虑 `交给谁` 为 `待接手` 或空白的 handoff。
3. 只有一个候选时，直接读取它。
4. 有多个候选时，向用户列出标题与一句目标，请用户选择；不得自行抢占其中一个。
5. 没有候选时，明确报告“当前没有可接手的交接工作”，不创建新 handoff。

## 执行流程

1. 读取交接板的“当前进行中的 handoff”区块。
2. 根据选择规则定位候选 handoff。
3. 读取选中的 handoff，依次确认：
   - `最新结论`
   - `任务边界`
   - `已完成`
   - `未完成`
   - `风险与阻塞`
   - `待确认判断`
   - `审核结论`
   - `接手动作`
4. 向用户简要返回：已获取的交接标题、当前目标、已完成、仍待确认和接手后的第一步。
5. 如果 handoff 缺少 `接手动作`、项目归属或关键边界，报告它尚不可安全接手，并指出缺口；不得自行补造内容。
6. 用户明确要求继续后，才按 handoff 的项目归属与接手动作进入实际任务。

## 写入边界

- “获取交接工作”默认只读：不创建 handoff、不改交接板、不勾选“最后确认”、不归档。
- 当前 Agent 真正开始执行并产生实质结果后，才按正常 Progress Sync 留痕。
- 交接完成后的归档仍由既有审核流程决定，不在本 workflow 自动发生。

## 禁止

- 不得要求用户提供 handoff 路径或目录。
- 不得把“获取交接工作”误解为搜索所有历史任务。
- 不得在多个候选存在时静默选择。
- 不得只读取交接板标题就开始执行；必须先读取 handoff 的接手动作与边界。
