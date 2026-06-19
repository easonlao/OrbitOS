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
- experience check 结果。

时间、event ID、actor、默认 checklist 和空置扩展字段由脚本生成。

## 执行流程

1. 确认本次存在需要持久化的实质结果。
2. 具体项目任务先按 `project-management.md` 分类：当场完成只准备 event；需要跨会话才更新 STATUS；ROADMAP 变化必须已有用户确认。
3. 如果属于具体项目且项目状态变化，更新 `STATUS.md`；满足已确认的 ROADMAP 完成条件时，同步勾选条件、日期和总体状态。
4. 运行 `python .orbitos/scripts/run-validation.py`。
5. validation 失败时停止，不刷新 Dashboard；报告失败原因。
6. 使用 `.orbitos/scripts/write_event.py` 写入完成凭证。
7. 按实际变化刷新 `今日.md`、`待确认.md`、`下一步.md`；没有变化的页面不写。
8. 再运行一次 validation，确认最终状态。
9. 最终 validation 失败时报告 event 路径和失败原因，不把失败结果描述为完成。

最小示例：

```bash
python .orbitos/scripts/write_event.py \
  --agent-id codex \
  --slug progress_sync_compiler \
  --summary "Progress Sync 已改为脚本生成最小完成凭证。" \
  --reason "减少手写 event 的格式错误和 agent 执行负担。" \
  --project OrbitOS \
  --file "updated:.orbitos/workflows/progress-sync.md:收缩同步流程" \
  --validation passed \
  --experience-check not_applicable
```

Windows PowerShell 可在同一行执行，或使用反引号换行。

## 待确认与扩展

- 有待确认事项时使用 `--review-required`，并至少提供一个 `--review-item`。
- 移动、删除或归档用户内容时增加 `--user-content-changed`；该动作仍必须事先获得用户确认。
- `captured / candidate_only / learned_updated` 只表示经验检查结果；对应内容仍按 Experience Capture 或 Rule Evolution 处理。
- 使用 Hindsight 时，以 `--hindsight-recall` 或 `--hindsight-retain` 记录引用；Hindsight 不是 Progress Sync 必需项。

## 人读投影

- `今日.md` 只展开当天关键变化、当前待确认和可继续入口。
- 项目 `STATUS.md` 是项目状态源；今日只投影当天变化。
- `本周.md` 只由 Weekly Review 更新。
- 历史流水留在 event，不复制到 Dashboard。

## 执行清单

### 进入检查

- [ ] 本次存在实质性持久化结果，或用户明确要求同步。
- [ ] 已确认变更范围、待确认事项和经验检查结果。
- [ ] 项目任务已分类，ROADMAP 或当前优先级变化已有用户确认。

### 执行检查

- [ ] 项目状态变化时已先更新项目 `STATUS.md`。
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
