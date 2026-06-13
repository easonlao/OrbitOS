---
title: Progress Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - workflow
  - progress-sync
---

# Progress Sync Workflow

Progress Sync 在完成实质性工作后执行，或用户说“同步”“同步进度”“更新进度”时执行。

## 目标

- 写入事实 event。
- 校验写入对象。
- 刷新 Obsidian Dashboard。
- 保持待确认、下一步、项目状态与事实层一致。

## 输入

- 用户请求或任务结果
- 已发生的文件变更
- 需要确认的事项
- 可继续的下一步
- 可选 Hindsight recall / retain 摘要

## 必填 event 字段

Progress Sync 至少生成包含以下字段的 event：

- `id`
- `timestamp`
- `actor`
- `event_type`
- `summary`
- `reason`
- `actions`
- `files_changed`
- `review_required`
- `next_steps`

## 执行流程

1. 汇总本次实质性动作。
2. 生成 event draft。
3. 执行 `validate-sync.md`。
4. 校验通过后写入 `.orbitos/logs/events/`。
5. 如果本次工作属于具体项目，并且改变了项目阶段、完成项、待确认或下一步，先更新对应 `03-项目/{project}/STATUS.md`。
6. 刷新 `02-时间线/今日.md`，使用层级式 Dashboard：
   - `1. 总览`
     - 当前判断
     - 当前阶段
     - 系统健康
   - `2. 待确认`
     - 当前需要用户确认
     - 规则判断或确认来源
   - `3. 今日进展`
     - 按主题分组，不写流水账
   - `4. 可继续`
     - 推荐下一步
     - 可并行推进
     - 暂不推进
   - `5. 各区状态`
     - 收件箱
     - 项目
     - Agents
   - `6. 来源`
     - 来源只写摘要，不逐条列出 `.orbitos/logs/events/*.yaml`。
     - 如需追溯机器事实，写“机器事实记录保存在 `.orbitos/logs/events/`”即可。
7. 如果有 pending review item，同步到 `02-时间线/待确认.md`。
8. 如果有 pending / blocked next step，同步到 `02-时间线/下一步.md`。
9. Progress Sync 前必须自检：本次工作是否产生经验、踩坑、用户纠正、返工、验证失败、规则候选或 learned rule 使用反馈。
10. 如果有经验输入，先执行 `.orbitos/workflows/experience-capture.md`：
   - 更新当前 agent profile。
   - 记录来源、影响和下一步。
   - 需要用户确认时，投影到 `今日.md` 的“待确认”。
11. 如果捕获内容足够通用、原子化、可执行、可验证，再执行 `.orbitos/workflows/rule-evolution.md`：
   - 先更新对应 agent profile。
   - 必要时更新 `.orbitos/rules/learned/INDEX.md`。
   - 需要用户判断时，投影到 `今日.md` 的“待确认”。
12. 如果修改 OrbitOS 系统层，更新 `00-系统/CHANGELOG.md`。

## 项目状态与今日投影

项目 `STATUS.md` 是项目状态源。`今日.md` 是当天聚合视图，不是项目状态源。

当本次工作明确属于某个项目时：

1. 先判断项目状态是否变化。
2. 如果项目阶段、完成项、待确认或下一步变化，先更新 `03-项目/{project}/STATUS.md`。
3. 再把项目 `STATUS.md` 的关键变化投影到 `今日.md`。
4. `今日.md` 的“项目”区块必须链接到对应项目状态页，例如 `[[../03-项目/OrbitOS/STATUS|OrbitOS]]`。
5. 对应项目 `STATUS.md` 的“来源”区块必须回链 `[[../../02-时间线/今日]]`。
6. 如果只是当天临时提醒、不改变项目长期状态，可以只写 `今日.md`，但要说明不更新项目 STATUS 的原因。

这条规则解决的是项目长期状态与当天 Dashboard 的主从关系。状态从项目流向今日，而不是从今日反推项目。

## 执行清单

### 进入检查

- [ ] 已确认本次工作完成了实质性动作，或用户明确要求同步。
- [ ] 已汇总本次文件变更、状态变化、待确认事项和下一步。
- [ ] 已确认是否需要 Experience Capture 或 Rule Evolution。

### 执行检查

- [ ] 已生成 event draft。
- [ ] 已执行 Validate Sync 或 validation eval。
- [ ] 已写入 `.orbitos/logs/events/`。
- [ ] 如本次工作属于项目且项目状态变化，已先更新对应项目 `STATUS.md`。
- [ ] 已刷新 `02-时间线/今日.md`。
- [ ] 如本次工作属于某个项目，`今日.md` 已从项目 `STATUS.md` 投影摘要并链接对应项目。
- [ ] 如有 pending review item，已同步到待确认入口或今日待确认。
- [ ] 如有 pending / blocked next step，已同步到 `02-时间线/下一步.md`。
- [ ] 如有经验输入，已执行 Experience Capture。
- [ ] 如有可泛化规则候选，已执行 Rule Evolution。

### 退出检查

- [ ] 已确认 event 中记录 checklist 结果。
- [ ] 已确认项目 STATUS 与今日投影的主从关系正确，或记录不适用原因。
- [ ] 已确认 `今日.md` 只投影异常、待确认、阻塞和关键摘要。
- [ ] 已确认 validation 通过，或已记录失败和回退。
- [ ] 已记录所有跳过项和原因。

## 禁止

- 不把完整推理过程写进 event。
- 不把未确认内容提升为规则、ADR、知识卡片或正式产物。
- 不在校验失败时刷新 Dashboard。
- 不把 Hindsight 当作 OrbitOS 必需依赖。
- 不把 event YAML 文件列表直接投影到用户 Dashboard。
