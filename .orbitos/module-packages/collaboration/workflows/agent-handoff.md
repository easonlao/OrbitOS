---
title: Agent Handoff Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-26
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - handoff
  - agents
---

# Agent Handoff Workflow

Agent Handoff 承接 `execution_mode=delegated` 的跨 Agent 或跨会话工作。它记录协作链，不替代项目 `STATUS.md`、event 或长期知识。

## 状态机

| 状态 | 当前负责人 | 含义 | 下一步 |
|---|---|---|---|
| `delegated` | 目标 Agent 或 `unassigned` | 已交出，尚未开始 | 接手方开始 |
| `working` | 执行 Agent | 正在处理 | 回交或关闭 |
| `returned` | `return_owner` 或指定 Agent | 本轮已完成，等待验收或下一步 | 负责人继续 |
| `closed` | 无 | 协作合同完成且项目状态已回写 | 移入归档 |

前三种状态留在 `00-系统/agents/handoff/` 并出现在 BOARD。`closed` handoff 必须立即移入 `handoff/archive/`；这是系统协作记录的收口，不需要用户额外说“归档”。

多阶段接力时，frontmatter 额外携带 `plan_status`（`proposed`/`confirmed`）、`plan_revision`（单调递增）与 `current_stage`；队列本体与阶段记录由 `.orbitos/state/handoff-queues.json` 机器层投影承载，handoff 正文的 `## 阶段队列` 与 `## 计划修订` 段落保持人工可读。

## 多阶段接力队列（Formal Handoff Queue）

两个以上独立 Agent 工具接力时，走 `handoff-queue.py` 的队列契约；它不替代 `handoff-control.py begin/close` 的治理链，而是约束“谁在哪个阶段可以做什么”。

1. **launch（提出计划）**：发起 Agent 用 `handoff-queue.py launch` 提出 launch card——参与工具、角色、执行顺序、交付物、范围、**禁止事项（--prohibited，必填）**、验收条件、**返回格式（--return-format，必填）**与 `return_owner`。队列必须由**至少两个不同工具**承担，且阶段链不允许末段回环。`return_owner` 在 launch 时校验（含与 handoff frontmatter 一致性）并持久化为权威值，后续命令不得篡改；Builder 与 Editor 阶段必须由不同工具承担。任何阶段进入 `working` 之前，都必须先得到一次显式用户确认。
2. **confirm（用户确认）**：确认必须携带 `--receipt`（用户确认回执/引用），写入投影 `confirmed_receipt` 供审计。确认后 `plan_status: confirmed`、`current_stage` 指向首个阶段；未确认前任何 advance 都被拒绝。确认与后续推进都从投影读取权威 `return_owner`，调用方传入不一致的值会被拒绝。
3. **接力（advance）**：只有 `current_owner` 且角色匹配当前阶段的 Agent 可以 `advance`。**每个阶段推进只能使用 begin 绑定到该阶段投影的 governance session（--session-id）**——先 open session 再直接 advance 的路径被拒绝，任何阶段都不能绕过 `handoff-control begin`。done 推进还要求该 session 已交付工作（`returned`/`review_required`/`closed`），不能从 `claimed` 直接推进。完成阶段必须写回结果、证据、未解决项与 outcome，**同步写入 handoff Markdown 的 `## 阶段记录`**（含 diff_ref、validation_ref、output_revision、reviewed_revision 与 session_id）——Formal Handoff Markdown 是跨工具通信合同，下一个独立 Agent 只读 Markdown 即可接手；阶段记录一经完成不可变。每次 done 使该阶段 `output_revision` +1。Builder 的 done 必须携带实现 diff 引用（--diff-ref）、验证证据引用（--validation-ref）与**未解决风险（--risk，必填）**。Editor 阶段必须紧跟已完成的 Builder/Writer 阶段：其 session 必须声明 `review_target_session_id` **等于被审阶段实际产出的 session（producer.session_id）**——同一 Builder 的其他虚假 session 无法冒充；且被审 session 的 review 必须已提交（approval 要求 review_status=approved），Editor 自身 session 必须已提交审核（closed）后才能推进。无论通过或驳回都必须携带 `--reviewed-revision`（等于被审阶段当前 `output_revision`）与引用被审阶段的证据。推进时同步更新当前负责人、角色、阶段、下一负责人与下一步，并一致更新机器层投影与 BOARD（顺序写入 + 预校验，非事务性，因此失败会在写入前被拦截）。每次推进的用户可见响应必须指名下一 Agent 工具与 pickup 指令（“获取交接工作”）。最后一个阶段完成后把棒交回 `return_owner` 验收。
4. **失败与阻塞**：阶段第一次失败记为 `blocked` 并计数；同一阶段失败两次后，任何继续推进都会被拒绝，必须走 re-plan（failure 触发要求已失败两次）。Editor 驳回同样必须携带审核证据与被审 revision。
5. **re-plan（修订计划）**：Agent 不可用、任务超出已确认范围或同阶段第二次失败时，当前 Agent 停止推进，用 `handoff-queue.py replan` 记录触发原因、受影响阶段、仍有效结果（--valid-results，必填）、失效假设（--invalidated-assumptions，必填）与替换角色（--replacement-role，必填），并同步写入 Markdown 的 `## 计划修订` 段；同时提议修订后的剩余队列（已完成阶段与证据保持不可变），`plan_revision` 单调 +1，等待用户再次确认。未确认的修订队列不允许任何 Agent 推进；修订确认后替换 Agent 才能接手。未确认期间可继续提出新一轮修订（历史完整保留），但**每次确认只给最新一条修订盖 `confirmed_at`**，被取代的旧修订保持未确认，历史如实。队列状态不可读（损坏、脚本失败、记录丢失但 handoff 仍声明计划）时 begin/close 一律拒绝，不按“无队列”放行。
6. **验收关闭**：只有 `return_owner` 可以 `handoff-control.py close`；Builder 与 Editor 阶段工具不能关闭整个交接。关闭前所有计划阶段必须完成且最新修订已确认；`--output` 格式（KIND|REF|STATUS[|NOTE]）在副作用前预校验。**closure receipt 只能由受控 close 写入投影（`_write_close_receipt`），不存在可伪造收据的公开命令**。关闭是**可恢复的顺序收口**而非原子操作：任一步失败（包括归档后、work/event 前崩溃）后直接重跑 close，会恢复完成剩余步骤（补 receipt/frontmatter/BOARD/work item/event/validation），全部完成后再次 close 返回 `already_closed` 成功。故障注入测试覆盖该恢复路径。

## 创建与更新

1. 确认当前工作确实需要 `execution_mode=delegated`，而不是普通项目状态更新。
2. 使用 `.orbitos/templates/00-系统/agents/handoff/TEMPLATE.md` 新建或更新 handoff。
3. frontmatter 必须填写：
   - `handoff_status`
   - `current_owner`
   - `return_owner`
   - `next_action`
4. 新交接一律从 `delegated` 开始；目标未定时使用 `current_owner: unassigned`。除非用户指定其他验收方，`return_owner` 必须是原交出 Agent。
5. 填写项目归属、目标、边界、已完成、未完成、风险、证据与接手动作。
6. 在 `00-系统/agents/BOARD.md` 当前交接区登记链接、状态、负责人和下一步。
7. 为需要跨 Agent 或跨会话继续的交接创建一个 `source_type=handoff` 的 work item，`source_ref` 指向 handoff 文件；work item 只记录负责人、状态、租约、下一步和证据，不复制 handoff 正文。
8. 接手方真正开始时，使用 `.orbitos/scripts/handoff-control.py begin`；它创建 `multi_agent_claim` governance session、claim 对应 work item，并把该 session 绑定到队列投影的当前阶段（`bind-session`），然后写入 `working`、`governance_required: true`、`collaboration_session_id` 并同步 BOARD。不得手工绕过这条链，也不得用手工 open 的 session 直接推进阶段——阶段 advance 只接受 begin 绑定过的 session。存在队列计划时，begin 只允许队列的当前负责人与当前角色执行。
9. 本轮完成且要他人继续时改为 `returned`，同步 work item 为 `waiting`。用户未指定下一位负责人时，`current_owner` 默认回填 `return_owner`，并更新下一步。
10. 协作合同完成时，最后处理的 Agent 先更新项目 `STATUS.md`，再使用 `.orbitos/scripts/handoff-control.py close`。它只接受已通过 hard gate 的 session（含恢复路径，重跑 close 不会跳过治理门）；存在队列计划时还要求全部阶段完成、无未确认修订，且只有 `return_owner` 可以关闭。关闭是**可恢复的顺序收口**（见上文第 6 条）：归档 handoff、回写 work item `done` 与 archive source_ref、写入带 role/output/review 的完成 event、在队列投影记录验收——任一步失败后重跑 close 恢复完成剩余步骤，work/event 缺失会失败而不会静默返回成功。
11. 在 Progress Sync 前运行 `python .orbitos/scripts/run-validation.py`。

## 最小内容

- 项目归属、路径与是否项目内任务。
- 本轮目标、范围和明确不处理项。
- 当前结论、已完成、未完成、风险与 `next_action`。
- 当前阶段、完成证据与交付合同。
- 已确认判断、待确认判断与真实执行判定。

## 状态源分工

- handoff：协作边界、负责人、状态和下一步。
- `STATUS.md`：项目当前事实、阻塞与下一步项目工作。
- event：实际操作凭证。
- BOARD：仅索引开放 handoff，不承载完整内容。

## 禁止

- 不把 direct 的简单任务包装成 handoff。
- 不把 handoff 当项目长期问题池。
- 不让已完成或已交回的记录停留在错误负责人或旧状态。
- 不把低置信度结论伪装成已确认判断。
