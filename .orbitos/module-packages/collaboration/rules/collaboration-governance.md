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

## 独立性定义

同一 Agent 的不同 profile/session 只能表示角色视角隔离，不能直接声称独立审核。正式 `approved` 必须由不同 Agent 认领 Editor session，并留下可追溯的审核证据和审核结论。
