---
title: Progress Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-17
tags:
  - orbitos
  - workflow
  - progress-sync
---

# Progress Sync Workflow

Progress Sync 把已经完成的自然工作编译成可校验的 OrbitOS 记录。它不是任务状态机，也不约束 agent 的对话或思考方式。

## 目标

- 用脚本生成最小完成凭证，避免 agent 手写 event。
- 以 validation 作为持久化结果的完成门。
- 只刷新真正发生变化的人读状态。
- 不自动提升知识、规则、ADR 或正式产物。

## 触发条件

- 完成了会改变文件或长期状态的实质性工作时自动触发。
- 用户说“同步”“同步进度”或“更新进度”。

用户不需要主动说出同步命令。纯讨论、只读查询和没有形成持久化结果的短对话不需要 Progress Sync。

## 最小输入

Agent 只需要整理：

- 一句话 `summary`。
- 本次动作的 `reason`。
- 实际变更文件及变更类型。
- 是否存在待确认事项。
- validation 结果。

时间、event ID、actor、默认 checklist 和空置扩展字段由脚本生成。

## 执行流程

1. 确认本次存在需要持久化的实质结果。
2. 具体项目任务先按 `project-management.md` 分类：当场完成只准备 event；需要跨会话才更新 STATUS；ROADMAP 变化必须已有用户确认。
3. 需要跨会话、跨 Agent 或并行推进的普通工作，创建或更新 `.orbitos/state/work-items.json` 索引；索引只记录 `source_type/source_ref`、负责人、下一步、租约和证据，不复制项目 STATUS、handoff 或 maintenance 的正文。
4. 如果本轮使用角色治理 session，先通过 `.orbitos/scripts/collab-session.py` 同步角色、租约、revision、阶段和证据；session 只通过 `task_ref` 指向业务主源，不复制正文。
5. 如果属于具体项目且项目状态变化，更新 `STATUS.md`；满足已确认的 ROADMAP 完成条件时，同步勾选条件、日期和总体状态。
6. 如果本轮处理 handoff，确认其状态、当前负责人、下一步和 BOARD 投影已同步；协作完成时先更新项目 `STATUS.md`，再关闭和归档 handoff，并同步 work index 指针。
7. 如果本轮处理维护事项，先用 `.orbitos/scripts/maintenance-control.py` 读取当前状态；领取、修复、验证和关闭都必须携带最新 `revision`，存在有效租约时不得覆盖其他执行者。只有新鲜验证 receipt 才能关闭；无法安全继续时进入 `blocked` 并请求用户确认。维护事项不转写为普通 work item。
8. 运行 `python .orbitos/scripts/run-validation.py`。
9. validation 失败时停止本轮业务投影并报告失败原因；System Check 可由自动化契约更新维护状态和受管健康区块。
10. 使用 `.orbitos/scripts/write_event.py` 写入完成凭证；event 记录历史事实，不替代当前维护状态。
11. 对普通 work item，只有原始来源已完成、验证/证据已记录且无用户待确认时，才将索引更新为 `done`；`work-control.py update --status done` 必须携带 completion evidence。对 collaboration session，只有租约有效、证据存在且没有待审核门禁时，才能关闭。
12. 按实际变化刷新 `今日.md`；维护状态投影只显示当前开放项，`closed` 与 `expired` 不得继续作为当前故障。
13. 再运行一次 validation，确认最终状态。
14. 最终 validation 失败时报告 event 路径和失败原因，不把失败结果描述为完成。

最小示例：

```bash
python .orbitos/scripts/write_event.py \
  --agent-id codex \
  --slug progress_sync_compiler \
  --summary "Progress Sync 已改为脚本生成最小完成凭证。" \
  --reason "减少手写 event 的格式错误和 agent 执行负担。" \
  --project OrbitOS \
  --file "updated:.orbitos/workflows/progress-sync.md:收缩同步流程" \
  --validation passed
```

Windows PowerShell 可在同一行执行，或使用反引号换行。

## 待确认与扩展

- 有待确认事项时使用 `--review-required`，并至少提供一个 `--review-item`。
- 移动、删除或归档用户内容时增加 `--user-content-changed`；该动作仍必须事先获得用户确认。
- 使用 Hindsight 时，以 `--hindsight-recall` 或 `--hindsight-retain` 记录引用；Hindsight 不是 Progress Sync 必需项。

## 人读投影

- `今日.md` 只展开当天关键变化、当前待确认和可继续入口。
- 项目 `STATUS.md` 是项目状态源；今日只投影当天变化。
- `本周.md` 只由 Weekly Review 更新。
- 历史流水留在 event，不复制到 Dashboard。

## 执行清单

### 进入检查

- [ ] 本次存在实质性持久化结果，或用户明确要求同步。
- [ ] 已确认变更范围和待确认事项。
- [ ] 项目任务已分类，ROADMAP 或当前优先级变化已有用户确认。

### 执行检查

- [ ] 项目状态变化时已先更新项目 `STATUS.md`。
- [ ] handoff 任务已同步状态、负责人、下一步和 BOARD；关闭项已归档。
- [ ] 当场完成的小修改未被写成 STATUS 事项；跨会话事项和 ROADMAP 条件按规则更新。
- [ ] 写 event 前 validation 已通过。
- [ ] 已使用 `write_event.py` 生成完成凭证。
- [ ] 只刷新发生变化的人读视图。

### 退出检查

- [ ] 最终 validation 已通过。
- [ ] 未静默提升知识、规则、ADR 或正式产物。
- [ ] 用户内容移动、删除或归档已经确认。

## 禁止

- 不要求用户或 agent 在普通对话中使用结构化话术。
- 不手写完整 event YAML。
- 不在 validation 失败时刷新 Dashboard。
- 不为了同步而重写没有变化的人读页面。
- 不把 STATUS 自动提升为 ROADMAP，也不把 ROADMAP 自动展开为 STATUS。
- 不把完整推理、命令输出或 event 文件列表写入 Dashboard。
