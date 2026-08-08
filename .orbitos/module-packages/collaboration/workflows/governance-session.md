---
title: Collaboration Governance Session Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-18
updated: 2026-07-18
tags:
  - orbitos
  - collaboration
  - role
  - session
---

# Collaboration Governance Session Workflow

本 workflow 是 Hermes V3 角色治理在 OrbitOS 的落地点。它建立可追踪的治理 session、角色认领、证据门禁和独立审核，不复制业务状态。

## 主源分工

- `work-items.json`：普通工作的来源指针、项目、负责人、状态、租约、下一步和完成证据。
- handoff：跨 Agent 协作合同、接手边界、回交与归档。
- `maintenance.json`：维护事项的检测、修复、验证和关闭状态。
- `collaboration-sessions.json`：当前 Agent 以什么角色参与哪个 task/session，以及该 session 的租约、阶段和门禁摘要。

Session 只能通过 `task_ref` 指向上述主源，不复制其正文，也不能替代它们。

## Handoff binding

Formal handoffs use `.orbitos/scripts/handoff-control.py begin` and `close`.

- `begin` binds `task_ref` to the active handoff path and records `collaboration_session_id` in that handoff.
- `close` requires a closed hard-gate-passed session, archives the handoff, re-anchors the work item to the archive path, and writes a collaboration receipt.
- Validation rejects a governed handoff, work item, session, or receipt when their references disagree.

## 角色与 Session

角色目录位于 `.orbitos/module-packages/collaboration/roles.json`，当前包含 `coordinator`、`researcher`、`writer`、`builder`、`editor`。

- 多 Agent 模式使用 `mode=multi_agent_claim`，不同 Agent 可认领不同角色。
- 单 Agent 模式使用 `mode=single_agent_subsession`，子 session 必须有 parent session，并继承同一个 Agent 身份。
- Agent Profile 是长期身份和能力说明；session 才是当前任务角色分配主源。

## Session 生命周期与阶段边界

角色存在性、session 认领、租约、revision、证据指针和关闭门禁由脚本统一执行。单 Agent 子 session 只能实现角色视角隔离；它不能被当作独立审核主体。

使用 `.orbitos/scripts/collab-session.py` 管理 `open`、`claim`、`heartbeat`、`update`、`submit-research`、`review` 和 `list`。

## 第二阶段置信度门禁

Researcher 使用 `submit-research` 提交结构化证据：`ref|evidence_kind|source_state|verification_status`。脚本根据证据推导 `red / yellow / green`，不接受裸写的 high 或 green。

- `green` 才能作为 Writer/Builder 的下游输入。
- `yellow` 和 `red` 必须留在 Researcher 阶段，或通过 `returned` 回流补证据。
- Writer/Builder session 默认 `review_required=pending`，即使输入为 green，也不能在 Editor 审核前关闭。
- `returned` 或 `blocked` 必须携带 `--reason`；旧证据保留，修复证据追加，不覆盖原链。

## 第三阶段 Editor 审核

- Writer/Builder 完成工作后必须先把 session 更新为 `review_required`，并附执行证据。
- Editor 必须使用 `review_target_session_id` 单独认领待审 session；审核者 Agent 不能与执行者 Agent 相同。
- `review --decision approved` 必须附带 `verification_status=independently_reviewed` 的结构化证据，并把审核 session、审核 Agent、证据引用和时间写回被审 session。
- Editor 驳回必须携带原因；被审 session 回到 `returned`，保留原证据并记录审核结论，不能直接关闭。
- 只有审核状态为 `approved` 时，Writer/Builder 才能通过关闭门禁。审核结果受 target revision 保护，防止基于旧产出的误审。
