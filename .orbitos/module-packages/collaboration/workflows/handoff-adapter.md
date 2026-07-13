---
title: Handoff Adapter Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-13
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - handoff
  - matt-pocock
---

# Handoff Adapter Workflow

本 workflow 把两种交接入口收口为同一份正式 OrbitOS handoff：

- 用户显式调用 Matt Pocock `$handoff`。
- 用户自然语言说“交给另一位 Agent 继续”“交接当前任务”或“把任务交给 {agent_id}”。

无论入口如何，正式主源始终是 OrbitOS handoff 与交接板。Matt skill 的临时摘要只是一种输入，不能替代正式 handoff、项目状态或接手路由。

## 入口与依赖

### 显式 `$handoff`

用户显式调用 `$handoff` 时，先按该 skill 的原约定在操作系统临时目录生成对话摘要。若本次会话运行在 OrbitOS 内，再立即进入本 workflow：

1. 使用 skill 产出的已知临时摘要作为压缩输入。
2. 提取其中的结论、未完成项和 `Suggested skills`。
3. 不复制已有 PRD、计划、ADR、issue、commit 或 diff 的正文，只引用其路径或链接。
4. 再通过 `agent-handoff.md` 写入正式 handoff 并登记交接板。

如果 skill 没有提供可读取的临时摘要路径，不得扫描系统临时目录猜测文件；改用当前对话生成等价的紧凑摘要，并继续正式交接。

### 自然语言交接

用户未显式调用 `$handoff` 时，不能自动调用该 skill，因为它要求显式 invocation。当前 Agent 直接采用同一份压缩契约：

- 只保留接手所需的结论、边界、未完成项、风险与第一步。
- 已有正式产物只引用，不复制正文。
- 不保留敏感信息。
- 根据下一步建议需要显式调用的 skills。

然后进入 `agent-handoff.md`，创建唯一正式 handoff 并登记交接板。

## 执行流程

1. 确认协作模块为 `ready`，并确定当前请求是显式 `$handoff` 还是自然语言交接。
2. 汇总当前对话与当前任务的最小接手上下文；不扫描无关项目、历史 handoff 或系统临时目录。
3. 如有 Matt skill 临时摘要，吸收其紧凑结论和建议技能；没有则按同一压缩契约生成。
4. 识别已存在的正式产物，只记录路径或 URL。
5. 移除 API key、密码、token、个人敏感信息及不必要的逐轮对话内容。
6. 调用 `agent-handoff.md`：
   - 写入项目归属、任务边界、最新结论、已完成、未完成、风险、待确认与接手动作。
   - 写入 `Suggested skills`，但不假设接手 Agent 已安装它们。
   - 用户指定接手 Agent 时填写其 `agent_id`；否则标记 `待接手`。
   - 登记到 `00-系统/agents/BOARD.md` 的当前交接区。
7. 返回给用户“已交接”，只说明交接标题、接手对象或待接手状态，以及接手方可使用“获取交接工作”。

## 接手边界

接手 Agent 不读取 Matt skill 的临时目录。它只通过 `handoff-pickup.md` 从交接板读取正式 handoff，因此可跨 Agent、跨会话和跨设备继续。

## 禁止

- 不把 Matt skill 的临时文件当作 OrbitOS 的状态源或交接入口。
- 不要求用户在自然语言交接时显式调用 `$handoff`。
- 不因推荐了某个 skill 就假设接手 Agent 已安装或可以使用它。
- 不把完整对话、敏感信息或重复产物复制进正式 handoff。
