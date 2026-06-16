---
title: Rule Evolution Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-13
updated: 2026-06-15
tags:
  - orbitos
  - workflow
  - rules
---

# Rule Evolution Workflow

Rule Evolution 定义 agent 经验如何进入规则系统。

它不负责生成长流程、技能或设计文档；只处理可复用、原子化、可验证的执行规则。

## 目标

- 让 agent 自身经验先在 agent profile 中积累。
- 从经验中提炼足够通用、原子化、对 OrbitOS 生态有必要的 learned rule。
- 保留证据、来源和讨论结论。
- 防止规则池变成杂项笔记或未经确认的个人偏好。
- 提升 core rule 前必须让用户确认。

## 分层

### Agent Experience

位置：

```text
00-系统/agents/{agent_id}.md
```

用途：

- agent 自己踩过的坑
- agent 自己验证过的做法
- agent 当前待确认来源
- agent 认为可提炼的候选规则

这是规则资产的原始积累层。

### Learned Rules

位置：

```text
.orbitos/rules/learned/INDEX.md
```

用途：

- 记录已经可被 agents 参考使用的通用规则。
- 每条规则必须有来源、适用范围、证据和状态。
- 使用次数不是最重要指标，但使用结果需要能追踪。

learned rule 不要求用户逐条预确认；agent 可以先使用，但使用后要记录效果。

### Core Rules

位置：

```text
.orbitos/rules/core/
```

用途：

- 稳定、默认强制遵守的系统规则。
- 不记录使用次数。
- 只有足够通用、原子化、对整个 OrbitOS 生态有必要，并和用户讨论清楚后，才能进入。

## 什么可以进入 learned

必须同时满足：

1. 足够通用：不只适用于某一次对话。
2. 原子化：一句话能表达清楚，不能是一整套长流程。
3. 可执行：agent 读完知道要做什么或避免什么。
4. 可验证：能通过后续使用记录判断是否有效。
5. 有来源：来自 agent profile、event、validation failure、用户确认或多 agent 重复经验。

不满足时：

- 太具体：留在对应 agent profile。
- 太长：转为 workflow 或 skill。
- 还在讨论：放在 `.orbitos/docs/`。
- 只是用户当天偏好：投影到 `今日.md` 待确认，不直接进规则。

## Learned Index 格式

learned rules 使用一个总表维护，不按规则拆文件。

每条规则至少包含：

- `id`
- `rule`
- `scope`
- `source_agents`
- `evidence`
- `status`
- `last_used`
- `result`
- `core_candidate`
- `reason`

详细证据和长说明保留在 agent profile、event 或相关文档中，INDEX 只做索引和判断。

## 触发条件

以下情况触发 Rule Evolution 检查：

- Progress Sync 的经验自检结果为 `learned_updated`，或需要判断 `candidate_only` 是否可进入 learned。
- Progress Sync 发现本次工作产生了经验、踩坑、返工或验证失败。
- 用户说“提炼规则”“同步规则”“这个以后要记住”“规则演化”。
- agent profile 中新增了可复用经验或待确认来源。
- 多个 agents 在相似位置重复踩坑。
- learned rule 被使用后需要记录效果。
- learned rule 被认为可能提升为 core。
- Experience Capture 判断某条记录满足 learned 条件。

如果只是普通任务完成，且没有经验、踩坑、规则候选或使用反馈，可以跳过。

## 与 Progress Sync 的解耦

Progress Sync 只负责强制做经验自检，不强制执行 Rule Evolution。

Rule Evolution 只在以下情况下写入 `.orbitos/rules/learned/INDEX.md`：

- 候选满足通用、原子化、可执行、可验证、有来源。
- learned rule 的使用反馈需要更新。
- 用户明确要求提炼规则，并且候选通过边界判断。

如果候选还不成熟，结果保持为 `candidate_only`，留在 agent profile 或今日待确认，不写 learned index。

## 闭环总览

```text
agent 工作 / 失败 / 成功经验
  -> 记录到 agent profile
  -> Progress Sync 触发 Rule Evolution 检查
  -> 初筛：profile / learned / workflow / skill / docs / 今日待确认
  -> 可泛化规则进入 learned INDEX
  -> 后续 agent 使用 learned rule 并记录效果
  -> 反例则回退或拆分
  -> 足够通用且与用户讨论清楚
  -> 今日.md 待确认
  -> 用户确认后进入 core
```

## 闭环记录点

### 1. Agent Profile

agent profile 是规则资产的原始来源。

建议维护以下小节：

```markdown
## 待确认来源

## 规则候选

## Learned Rule 使用记录
```

写入原则：

- 只写该 agent 自己遇到、使用、验证过的内容。
- 不在 profile 中直接宣布系统通用规则。
- 如果需要用户确认，标明“待确认”，并由 Progress Sync 投影到 `今日.md`。

### 2. Learned Index

`.orbitos/rules/learned/INDEX.md` 是系统级规则总表。

写入原则：

- 只收可泛化、原子化、可执行、可验证的规则。
- 总表只写判断和索引，不写长解释。
- 详细证据保留在 agent profile、event 或相关文档。

### 3. 今日 Dashboard

`今日.md` 是用户确认入口。

以下事项必须投影到 `今日.md` 的“待确认”：

- 建议提升 core 的 learned rule。
- 与现有 core rule 冲突的 learned rule。
- 需要用户判断适用范围的规则。
- agent 认为会影响整个 OrbitOS 操作方式的规则。

## 执行流程

### 1. 收集

Progress Sync 或 agent 自检时，从以下位置收集候选：

- `00-系统/agents/{agent_id}.md`
- `.orbitos/logs/events/`
- validation failure
- 用户明确指出的规则需求
- 多 agent 重复踩坑

### 2. 初筛

判断候选属于哪一类：

- 留在 agent profile
- 写入 `.orbitos/rules/learned/INDEX.md`
- 转为 workflow
- 转为 skill
- 放入 `.orbitos/docs/` 继续设计
- 投影到 `今日.md` 待用户确认

初筛问题：

1. 这是否只属于某个 agent 的部署、能力或习惯？
2. 这是否能用一句话表达成可执行规则？
3. 这是否对多个 agent 或整个 OrbitOS 生态有价值？
4. 这是否已有证据或明确来源？
5. 这是否其实更像 workflow、skill 或 design note？

### 3. 写入 learned

只有满足 learned 条件时，才加入 learned index。

写入时必须：

- 保持规则原子化。
- 记录来源 agent。
- 记录证据引用。
- 标明适用范围。
- 标明当前状态。

如果 learned index 仍是空表，先删除 `_empty_` 占位行，再写入第一条规则。

### 4. 使用与反馈

agent 使用 learned rule 后，更新 learned index：

- `last_used`
- `result`
- `evidence`
- 必要时补充反例或失败说明

使用结果建议值：

- `helped`：减少返工或避免错误。
- `neutral`：未明显影响结果。
- `failed`：规则导致误判或不适用。
- `not_applicable`：本次任务看似相关但实际不适用。

如果规则效果不好：

- 降级为 agent experience。
- 拆分成更小规则。
- 标记为 conflict 或 deprecated。

### 5. 今日投影

每次 Rule Evolution 产生以下结果时，Progress Sync 必须刷新 `今日.md`：

- 新 learned rule 已写入。
- learned rule 有失败或冲突。
- learned rule 建议提升 core。
- 用户需要判断是否把 agent profile 中的经验提炼成系统规则。

`今日.md` 中只写摘要，不复制 learned index 全表。

### 6. 提升 core

进入 core 前必须满足：

- 足够通用。
- 足够原子化。
- 对整个 OrbitOS 生态有必要。
- 没有明显反例，或反例已被限定适用范围。
- 已和用户讨论清楚并获得确认。

次数不是最重要标准。

用户确认后：

1. 更新 `.orbitos/rules/core/` 对应规则文件。
2. 在 `.orbitos/rules/learned/INDEX.md` 标记为 `promoted_to_core`。
3. 执行 Progress Sync。
4. 更新 `今日.md`。

### 7. 回退

以下情况必须回退：

- 规则太具体：回退到对应 agent profile。
- 规则太长：转为 workflow 或 skill。
- 规则证据不足：标记 `watching`。
- 规则与 core 冲突：标记 `conflict` 并投影到 `今日.md`。
- 规则长期无效：标记 `deprecated`。

回退不能删除证据，必须保留来源和原因。

## 执行清单

### 进入检查

- [ ] 已确认有 Experience Capture、agent profile、event、validation failure 或用户触发来源。
- [ ] 已确认候选不是一次性偏好或普通流水账。
- [ ] 已读取相关 agent profile 和必要证据。

### 执行检查

- [ ] 已完成初筛：profile / learned / workflow / skill / docs / 今日待确认。
- [ ] 如进入 learned，已保持规则原子化并更新 `.orbitos/rules/learned/INDEX.md`。
- [ ] 如只是 agent 私有经验，已保留在 agent profile。
- [ ] 如需要用户判断，已投影到 `今日.md`。
- [ ] 已在 Progress Sync event 中记录最终结果：`candidate_only` 或 `learned_updated`。
- [ ] 如建议提升 core，已确认需要用户明确确认。
- [ ] 如存在失败或冲突，已标记 conflict / deprecated / watching 或回退。

### 退出检查

- [ ] 已保留来源证据。
- [ ] 已记录 learned rule 使用反馈或跳过原因。
- [ ] 已在 event 中记录 Rule Evolution 动作。
- [ ] 已确认未绕过用户确认提升 core。

## 状态

learned rule status 使用：

- `active`：可被 agent 参考使用。
- `watching`：可试用，但证据不足。
- `conflict`：和现有规则或实际结果冲突，等待处理。
- `deprecated`：不再建议使用。
- `promoted_to_core`：已提升到 core。

## 禁止

- 不把一次性偏好直接写成 rule。
- 不把大段流程写进 learned rule。
- 不因使用次数多就自动提升 core。
- 不绕过用户确认提升 core。
- 不把 agent 私有经验强行变成系统通用规则。
- 不把 learned index 写成长篇解释文档。
- 不让 learned rule 只进入总表而没有来源证据。
- 不让待确认事项只停留在 agent profile 而不投影到 `今日.md`。
