---
title: Progress Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-16
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
- 默认不写 `02-时间线/本周.md`；周级总结由 Weekly Review Workflow 负责。

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

## Event 文件命名

Event `id` 和 event 文件名使用不同格式：

- `id`：`evt_YYYYMMDD_HHMMSS_{agent_id}_{slug}`
- 文件名：`YYYYMMDD_HHMMSS_{slug}.yaml`

规则：

- 文件名不加 `evt_` 前缀。
- 文件名只使用小写字母、数字和下划线，不使用空格或连字符。
- `YYYYMMDD_HHMMSS` 必须与 `timestamp` 的本地时间一致。
- `slug` 用 3-6 个英文词表达主题，例如 `hindsight_mcp_retain_test`。
- `id` 用于 `related_events` 串联；文件名用于时间排序和人工查找。
- 历史 event 文件不批量重命名；从 2026-06-15 起的新 event 必须遵守本规范。

## 经验自检结果

Progress Sync 必须做经验自检，但不等于必须写经验或提炼规则。

在 event checklist 中记录 `experience_check`，并在 `note` 中使用以下结果之一：

| result | 含义 | 后续动作 |
|---|---|---|
| `not_applicable` | 本次没有可复用经验、踩坑、纠正、返工或规则使用反馈 | 不执行 Experience Capture / Rule Evolution |
| `captured` | 已记录到当前 agent profile，但不进入 learned index | 执行 Experience Capture，停止在 profile |
| `candidate_only` | 已形成规则候选或待观察经验，但暂不进入 learned index | 执行 Experience Capture，必要时投影到今日待确认 |
| `learned_updated` | 已更新 learned rule index 或记录 learned rule 使用反馈 | 执行 Rule Evolution，并记录来源证据 |

`not_applicable` 默认只写入 event checklist，不投影到 `今日.md`。

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
     - 时间边界：
     - `今日.md` 只展开当天发生的关键事实、当前待确认和下一步。
     - 前一天或更早的完成项不能放在“今日进展”中展开，只能作为待确认来源、背景一句话或链接到 `本周.md` / 项目 `STATUS.md`。
     - 已经稳定落实的背景能力不能长期占用今日展开区；只有异常、阻塞、需要用户动作或当天新增变化才展开。
     - 跨日历史流水应保存在 event log、本周视图或项目状态源中。
7. 如果有 pending review item，同步到 `02-时间线/待确认.md`。
8. 如果有 pending / blocked next step，同步到 `02-时间线/下一步.md`。
9. 不更新 `02-时间线/本周.md`；只有用户明确要求“本周回顾 / 更新本周 / 周总结 / 周复盘”时才转入 `.orbitos/workflows/weekly-review.md`。
10. Progress Sync 前必须自检：本次工作是否产生经验、踩坑、用户纠正、返工、验证失败、规则候选或 learned rule 使用反馈，并得出 `not_applicable / captured / candidate_only / learned_updated` 之一。
11. Progress Sync 前必须执行任务边界自检，参考 `.orbitos/rules/core/task-boundary.md`：
   - 是否只修改了用户请求或 workflow 所需范围。
   - 是否移动、删除或归档了用户内容。
   - 是否创建了知识卡片、ADR、正式产物或 core rule。
   - 是否先更新了正确状态源，再投影到 `今日.md`。
   - 人读视图中提到的现有可见 Markdown 是否使用 Obsidian 双链，避免用户手动找文件。
   - validation 是否通过。
12. 如果结果为 `captured` 或 `candidate_only`，先执行 `.orbitos/workflows/experience-capture.md`：
   - 更新当前 agent profile。
   - 记录来源、影响和下一步。
   - 需要用户确认时，投影到 `今日.md` 的“待确认”。
13. 如果结果为 `learned_updated`，或捕获内容足够通用、原子化、可执行、可验证，再执行 `.orbitos/workflows/rule-evolution.md`：
   - 先更新对应 agent profile。
   - 必要时更新 `.orbitos/rules/learned/INDEX.md`。
   - 需要用户判断时，投影到 `今日.md` 的“待确认”。
14. 如果修改 OrbitOS 系统层，更新 `00-系统/CHANGELOG.md`。

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
- [ ] 已执行任务边界自检。
- [ ] 已确认经验自检结果：`not_applicable / captured / candidate_only / learned_updated`。

### 执行检查

- [ ] 已生成 event draft。
- [ ] 已执行 Validate Sync 或 validation eval。
- [ ] 已写入 `.orbitos/logs/events/`。
- [ ] 如本次工作属于项目且项目状态变化，已先更新对应项目 `STATUS.md`。
- [ ] 已刷新 `02-时间线/今日.md`。
- [ ] 如本次工作属于某个项目，`今日.md` 已从项目 `STATUS.md` 投影摘要并链接对应项目。
- [ ] 如有 pending review item，已同步到待确认入口或今日待确认。
- [ ] 如有 pending / blocked next step，已同步到 `02-时间线/下一步.md`。
- [ ] 如结果为 `captured` 或 `candidate_only`，已执行 Experience Capture。
- [ ] 如结果为 `learned_updated` 或存在可泛化规则候选，已执行 Rule Evolution。

### 退出检查

- [ ] 已确认 event 中记录 checklist 结果。
- [ ] 已确认 event checklist 记录了 scope / user_content / formal_artifact / source_of_truth / validation。
- [ ] 已确认 event checklist 记录了 `experience_check` 结果和跳过原因。
- [ ] 已确认项目 STATUS 与今日投影的主从关系正确，或记录不适用原因。
- [ ] 已确认 `今日.md` 只投影异常、待确认、阻塞和关键摘要。
- [ ] 已确认人读视图中点名的现有可见 Markdown 已使用 Obsidian 双链；内部 `.orbitos/` 路径未使用双链。
- [ ] 已确认 validation 通过，或已记录失败和回退。
- [ ] 已记录所有跳过项和原因。

## 禁止

- 不把完整推理过程写进 event。
- 不把未确认内容提升为规则、ADR、知识卡片或正式产物。
- 不在校验失败时刷新 Dashboard。
- 不把 Hindsight 当作 OrbitOS 必需依赖。
- 不把 event YAML 文件列表直接投影到用户 Dashboard。
- 不在普通同步中更新 `本周.md`；周级页面只能由 Weekly Review Workflow 写入。
