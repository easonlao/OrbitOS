---
title: Collaboration Governance Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-07-18
updated: 2026-07-18
tags:
  - orbitos
  - collaboration
  - governance
  - anti-hallucination
---

# Collaboration Governance Rule

## 分层

- Agent 身份由 registry/profile 定义，不能按单个任务临时改写。
- 角色由 collaboration role catalog 定义，说明职责、禁区和默认门禁。
- 当前任务分配由 `collaboration-sessions.json` 记录，包含 Agent、角色、task_ref、租约、阶段和证据。
- 项目状态、handoff 和维护状态继续由各自主源记录。

## 硬边界

- 未注册 Agent 不能打开或认领 session。
- 不存在于角色目录的角色不能认领。
- 单 Agent 子 session 必须挂在同一 Agent 的 parent session 下。
- 租约有效时其他 Agent 不能覆盖；租约过期后才允许接管。
- session 状态更新必须携带最新 revision。
- 有待审核标记或缺少证据时，不能关闭 session。
- Researcher 的 confidence 只能由结构化 evidence 推导；`agent_inference` 不能单独升级，黄色/红色不能流入 Writer/Builder。
- Writer/Builder 默认要求 Editor 审核；没有独立审核结论时不能关闭。
- `returned` / `blocked` 必须记录回流原因，旧证据链只能追加不能覆盖。
- Writer/Builder 必须先进入 `review_required`，不能绕过 Editor 直接关闭。
- Editor 必须声明 `review_target_session_id`，并使用独立的 target revision 审核；同一 Agent 即使切换 Profile 或 Session 也不能审核自己的产出。
- 批准审核必须包含 `independently_reviewed` 证据；驳回审核必须包含结构化证据和明确原因。
- 审核结果必须写回被审 session 的 `review` 记录，包含 reviewer session、reviewer agent、证据引用、结论和时间。
- 被驳回的产出只能回到 `returned` 重新修正，不能从驳回状态直接关闭。

## 队列硬边界

- 队列计划（launch card）必须先经用户显式确认，`plan_status` 才能从 `proposed` 变为 `confirmed`；任何阶段不得在确认前进入 `working`。launch card 的禁止事项与返回格式为必填。
- `return_owner` 在 launch 时持久化为权威值，后续命令一律从投影读取；调用方传入不一致值即拒绝。
- **每个阶段推进必须绑定该阶段的 governance session**（agent/role/task 匹配、未关闭），不能绕过 `handoff-control begin` 直接推进。
- Builder 与 Editor 阶段必须由不同工具承担；Builder 的 done 必须携带 diff 引用与验证证据引用；Editor 只能审核已完成的 Builder/Writer 阶段，其 session 必须声明 `review_target_session_id` 指向被审阶段 session（独立审核），且无论通过或驳回都必须携带 `reviewed_revision`（等于被审阶段当前 `output_revision`）与引用被审阶段的证据。
- 每次确认只给最新一条修订盖 `confirmed_at`；被取代的旧修订保持未确认，历史如实。
- **closure receipt 只能由受控 close 写入**（`_write_close_receipt`），不存在可伪造收据的公开命令。
- close 是可恢复的顺序收口：归档后任一步失败，重跑 close 恢复完成剩余步骤；全部完成后再次 close 返回 `already_closed`。
- Formal Handoff Markdown 是跨工具通信合同：阶段结果、证据、未决项与推进信息必须写回 Markdown（`## 阶段记录`），不能只存在机器层 JSON。
- 任一时刻只有一个 `current_owner` 与一个 `current_stage`；未来阶段的 Agent 不能提前认领或推进。
- 已完成阶段的结果、证据与未解决项不可变，只能追加不能改写。
- 阶段推进必须一致更新当前负责人、角色、阶段、下一负责人、下一步，并同步机器层投影与 BOARD。
- 同一阶段失败两次后必须 re-plan（failure 触发要求已失败两次）；未经用户确认的修订队列（`plan_revision` 单调递增）不能推进，替换 Agent 在确认与所有权更新前不能接手。未确认期间可继续提出新一轮修订，历史完整保留。
- 只有 `return_owner` 能接受并关闭整个交接；Builder 与 Editor 阶段工具不能关闭。
- 队列状态不可读（损坏、脚本执行失败，或 handoff 声明计划但投影记录丢失）时 begin/close 一律拒绝，不得按“无队列”放行。
- 关闭前所有计划阶段必须完成，closure receipt 保留有序历史、输出、独立审核证据、最终验收与归档引用。

## 独立性定义

同一 Agent 的不同 profile/session 只能表示角色视角隔离，不能直接声称独立审核。正式 `approved` 必须由不同 Agent 认领 Editor session，并留下可追溯的审核证据和审核结论。
