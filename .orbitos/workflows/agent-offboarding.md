---
title: Agent Offboarding Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-08-12
updated: 2026-08-12
tags:
  - orbitos
  - workflow
  - agent-offboarding
---

# Agent Offboarding Workflow

Agent Offboarding 用于把真实 agent 从 OrbitOS 注销下线。它覆盖 registry 生命周期状态推进、资源归档、依赖关系解绑，以及注销原因与时间的记录。

它不是 Startup Sync，也不是手写删除 registry 条目的捷径。注销是唯一被授权改动 agent 名下任务 owner 的正式流程，四步顺序不可跳过。

## 目标

- 把 registry 条目从 `active` 收敛到 `offboarded`，保留可机读的注销原因与时间。
- 归档 agent 的 profile / experience / env 到 `99-归档/agents-{id}-{YYYYMMDD}/`。
- 解绑名下 open handoff / collaboration session / work item，避免僵尸项。
- 写入 event 作为事实记录，不产生自创枚举值。

## 触发条件

统一入口，两种场景：

| 场景 | 触发条件 | `offboard_exception` | 语义 |
|---|---|---|---|
| 主动注销 | 用户明确说"注销 agent X""下线""移除接入" | `false` | 用户主导，资源可预期释放，流程可完整走完。 |
| 异常注销 | agent 运行失败不可恢复、账号/平台身份废弃、沙箱失效无法再进入 | `true` | 部分清理动作可能失败或必须跳过；终态需用户确认，event `review_required: true`。 |

## 前置确认

进入任何写入前必须完成：

- **核实真实 `agent_id`**：读取 `.orbitos/agents/registry.yaml` 确认注册 id，不接受用户口述的平台或项目名（事实依据：`00-系统/agents/workbuddy-experience.md` 2026-08-12 条目，openhanako 是项目名、注册 id 实为 hanako）。
- 确认归档目标目录名：`99-归档/agents-{id}-{YYYYMMDD}/`，对齐既有 `99-归档/agents-hanako-20260812/` 实物。
- 确认依赖归属：读取名下 open work item / collaboration session / handoff（`handoff-status.py --agent-id`、`task-context.py --agent-id`、`collab-session.py`）。
- 主动注销须确认交接对象（"转交"目标，可为 `user`）；异常注销不要求交接对象，但必须确认"残留如何标记"。

## 执行流程

注销段固定四步，顺序不可跳过：

```
① 状态清理 → ② 资源释放 → ③ 依赖关系解绑 → ④ 记录注销原因与时间
```

### ① 状态清理

- **输入**：registry 中目标条目、`agent_id`、当前 `status`。
- **输出**：registry 条目 `status` 置为 `offboarding`（进入终态前的"进行中"标记）；目标 agent 停止被 Startup Sync 认领。
- **动作**：在 `.orbitos/agents/registry.yaml` 上标记状态；不改动 `deployment` / `profile_ref` / `last_seen`。
- **禁止**：未经确认直接删除条目；把 `status` 之外的业务字段改写为占位值。

### ② 资源释放

- **输入**：`00-系统/agents/{agent_id}.md`（profile）、`00-系统/agents/{agent_id}-experience.md`、`.orbitos/state/env/{agent_id}.json`（env 报告）。
- **输出**：以上文件以 `moved` 语义移入 `99-归档/agents-{id}-{YYYYMMDD}/`（对齐 `agents-hanako-20260812/` 实物：hanako.md / hanako-experience.md / env-hanako.json）；profile 中 `lifecycle` frontmatter 置为 `archived`（人读标记）。
- **禁止**：硬删除原始文件（除非用户明确要求且确认无可追溯需求）；新归档目录已存在时重复创建覆盖（幂等要求：目录存在则复用）。
- **异常注销特殊项**：清理动作失败（如沙箱不可用、文件被锁）时标记 `skipped` 并在 event checklist 注明，不阻断终态记录。

### ③ 依赖关系解绑

- **输入**：`handoff-status.py --agent-id`、`task-context.py --agent-id`、`collab-session.py` 返回的名下 open 项。
- **输出**：名下 open handoff（`delegated` / `working` / `returned`）标记为"负责人已注销"（owner 置空或改交指定对象）；open collaboration session 收口或标记 stage 失效；open work item 标记需人工裁决。
- **默认策略**：**标记，不自动转交**（转交是高风险动作，必须用户指定对象；未指定则置空 owner + `next_action` 指向 user）。
- **禁止**：静默把名下任务自动改派给其他 agent；删除 handoff / session 记录（Startup Sync 只报告不改写这些项，Offboarding 是唯一允许改动 owner 的正式流程）。

### ④ 记录注销原因与时间

- **输入**：`offboard_reason`（前置确认所得）、`offboarded_at`（当天 `YYYY-MM-DD`）、`offboard_exception`。
- **输出**：registry 条目 `status: offboarded` + `offboarded_at` + `offboard_reason` + `offboard_exception` 落盘；README 中 agent 列表同步；写入 event。
- **event 表达**：`.orbitos/schemas/event.schema.yaml` 的 `files_changed[].change_type` 枚举为 created/updated/deleted/moved/renamed，`outputs[].status` 为 created/updated/unchanged/skipped/failed，均**无 archived**。归档文件记 `files_changed` `change_type=moved`，归档目录条目记 `outputs` `status=created`。`event_type` 使用 `agent_offboarding`（Slice 3 已将 `event.schema.yaml` 枚举扩展到 11 值，`write_event.py` / `offboard-agent.py` 同步支持）。
- **禁止**：自创 `archived` 枚举值导致 validation FAIL；未写 event 就宣告注销完成；`offboard_exception: true` 时跳过用户确认（event `review_required` 必须为 true）。

## 交叉约束

- **offboarded 不得重新 onboarding**：`agent-onboarding.md` 第 3 步已扩展——若现有条目 `status` 为 `offboarded`，不得重新注册，需用户明确决定。复活必须由用户明确决定并走独立路径。
- **重复注销幂等**：若条目已 `status: offboarded` 且归档目录已存在，直接返回成功；不重复归档、不覆盖既有 `offboard_reason`（除非用户明确要求修订），`offboarded_at` 若存在则保留首次值。
- **offboarding 中间态停止认领**：`status: offboarding` 的条目应停止被 Startup Sync 认领——不读取其 profile 投影、不推进其名下任务，直到收敛为 `offboarded`。正常流程应在同一轮工作内从 `offboarding` 收敛到 `offboarded`。

## 执行清单

### 进入检查

- [ ] 已确认本次是注销动作，而不是 Startup Sync 或 Onboarding。
- [ ] 已核实 registry 真实 `agent_id`，未用用户口述的平台/项目名替代。
- [ ] 已确认是主动注销还是异常注销，并确认对应确认门槛。
- [ ] 已确认归档目标目录名与依赖归属清单。

### 执行检查

- [ ] 已按固定四步序执行：状态清理 → 资源释放 → 依赖关系解绑 → 记录注销原因与时间，未跳步。
- [ ] 已把 registry 条目收敛到 `status: offboarded` 并携带 `offboarded_at` / `offboard_reason` / `offboard_exception`。
- [ ] 已归档文件（`moved`）并复用已存在的归档目录。
- [ ] 名下 open 项已标记"负责人已注销"，未静默自动转交。
- [ ] 未删除 handoff / session 记录。

### 退出检查

- [ ] 已运行 validation eval：`python .orbitos/scripts/run-validation.py`（Python 不可用时尝试 Node fallback / PowerShell wrapper，并记录手动校验范围）。`status=offboarded` 条目不再被 `actual.agent-collaboration-evidence` 判 profile 缺失（已豁免）；其四字段（`offboarded_at` / `offboard_reason` / `offboard_exception`）与归档目录完整性由 `actual.offboarding-consistency` 校验覆盖。
- [ ] 已写入 event，`change_type` / `status` 未使用 `archived` 等自创枚举值。
- [ ] 异常注销时 event `review_required: true` 且已请用户确认终态。
- [ ] 重复注销时未重复归档、未覆盖既有 `offboard_reason` 与首次 `offboarded_at`。

## 禁止

- 未经确认直接删除 registry 条目。
- 自创 `archived` 枚举值（event schema `change_type` 只有 created/updated/deleted/moved/renamed，`outputs.status` 只有 created/updated/unchanged/skipped/failed）。
- 跳过四步顺序（状态清理 → 资源释放 → 依赖关系解绑 → 记录注销原因与时间）。
- 静默把名下任务自动转交给其他 agent。
- 未写 event 就宣告注销完成。
- `offboard_exception: true` 时跳过用户确认。
- 对 `status: offboarded` 条目执行重复写入而绕过幂等检查。
- 把 `offboarded` 条目重新 onboarding，除非用户明确决定。
