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

本 workflow 把 Matt Pocock `$handoff` 与“交给另一位 Agent 继续”等自然语言收口为正式 OrbitOS handoff。临时摘要只能作为输入，正式状态源始终是 handoff 与 BOARD。

## 执行流程

1. 确认协作模块为 `ready`，当前请求是 `$handoff` 或自然语言交接。
2. `$handoff` 有临时摘要时，只提取结论、未完成项与 Suggested skills；没有可读取路径时，不得扫描操作系统临时目录猜测文件，直接从当前对话生成紧凑摘要。
3. 只保留接手所需的结论、边界、未完成项、风险与第一步；已有 PRD、计划、ADR、issue、commit 或 diff 只引用路径。
4. 调用 `agent-handoff.md` 创建唯一正式 handoff：
   - 填写项目归属、边界、结论、已完成、未完成、风险和接手动作。
   - 写入 `handoff_status: delegated`。
   - 用户指定 Agent 时写入该 `current_owner`；否则写 `unassigned`。
   - 写入 `return_owner`：除非用户明确指定其他验收方，否则为当前原交出 Agent。
   - 写入具体 `next_action`。
5. 在 BOARD 当前交接区登记该条目。
6. 只向用户说明交接标题和对象；接手方只需说“获取交接工作”。

## 接手边界

接手 Agent 只通过 `handoff-pickup.md` 读取正式 handoff，不读取 Matt skill 的临时目录，因此可跨 Agent、跨会话和跨设备继续。

## 禁止

- 不把 `$handoff` 临时文件当作 OrbitOS 状态源。
- 不要求用户在自然语言交接时显式调用 `$handoff`。
- 不得扫描系统临时目录。
- 不复制完整对话、敏感信息或重复产物。
