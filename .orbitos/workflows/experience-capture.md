---
title: Experience Capture Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-13
updated: 2026-06-15
tags:
  - orbitos
  - workflow
  - agent-experience
---

# Experience Capture Workflow

Experience Capture 定义 agent 什么时候记录对话内的踩坑、经验和规则候选。

它是 Rule Evolution 的前置输入层。

## 目标

- 让 agent 不再只在用户提醒时才记录经验。
- 把对话里的踩坑和有效做法先落到 agent 经验文件或项目经验文件。
- 为 Rule Evolution 提供稳定输入。
- 让用户可以用一句话触发记录。

## 触发条件

出现以下任一情况，agent 必须执行 Experience Capture 检查：

### 自动触发

- 任务中出现错误、返工、误解用户意图。
- 违反或差点违反 OrbitOS 规则。
- validation、测试、脚本或命令失败，并且原因有复用价值。
- 用户纠正了 agent 的理解、路径、边界或术语。
- agent 发现某个做法明显减少返工。
- agent 发现某个规则、workflow、schema 或文档不够清楚。
- 同一类问题在当前 agent 或多个 agents 中重复出现。
- 本次工作改变了 agent 以后进入 OrbitOS 的方式。

### 用户触发

用户说以下意思时，必须执行：

- “记录经验”
- “记录踩坑”
- “这个坑记一下”
- “这个以后注意”
- “同步经验”
- “沉淀这个经验”
- “为什么又犯这个错”

## 不需要记录

以下情况不记录：

- 普通执行步骤，没有复用价值。
- 一次性文件名、临时路径、临时命令。
- 已经由 event 足够表达、且没有经验增量。
- 只是 agent 的隐藏推理过程。
- 未经用户确认的个人偏好。

## 写入位置

默认先判断经验属于 agent 还是项目，再决定写入位置。

### Agent 级经验

以下内容默认写入当前 agent 的经验文件：

```text
00-系统/agents/{agent_id}-experience.md
```

适用内容：

- 跨项目仍成立的执行经验
- 当前 agent 的环境、工具、路径、shell 或同步坑
- OrbitOS workflow、schema、validation、Git 边界等系统级经验
- 会影响该 agent 以后进入 OrbitOS 方式的稳定约束

对应小节：

- `经验记录`
- `踩坑`
- `待确认来源`
- `规则候选`
- `Learned Rule 使用记录`

### 项目级经验

以下内容优先写入项目内：

```text
03-项目/{project}/docs/LESSONS-LEARNED.md
```

适用内容：

- 只对某个项目成立的发布经验、验证经验或领域约束
- 该项目特有的架构边界、配置坑、数据坑或运维坑
- 离开该项目后复用价值明显下降的经验

如果项目目录已存在但 `docs/LESSONS-LEARNED.md` 尚未建立，可按项目文档规则创建；若当前任务并未进入具体项目范围，则不要擅自新建项目经验文件。

轻量 profile `00-系统/agents/{agent_id}.md` 只保留启动所需信息和经验入口，不应继续膨胀为完整经验日志。

如果当前 agent 没有 profile，先停止并按 Startup Sync 的未知 agent 流程确认身份，不得自行创建。

## 判断原则

用这个问题判断写入位置：

```text
如果换一个项目，这条经验是否仍然成立？
```

- 如果答案是“基本成立”，写入 agent 经验文件。
- 如果答案是“主要只对当前项目成立”，写入项目 `docs/LESSONS-LEARNED.md`。
- 如果同时有跨项目抽象和项目实例，两边都可记录，但轻量 profile 只保留经验入口或少量启动关注，不复制整段经验细节。

## 写入格式

每条记录尽量短：

```markdown
- {日期}｜{一句话经验或踩坑}｜来源：{对话/event/文件}｜影响：{以后避免什么或应该怎么做}
```

规则候选使用：

```markdown
- {日期}｜候选：{一句话规则}｜范围：{适用范围}｜证据：{来源}｜下一步：{留在 profile / 进入 learned / 待用户确认}
```

## 与 Rule Evolution 的关系

Experience Capture 只负责捕获输入。

如果捕获内容满足以下条件，再执行 `.orbitos/workflows/rule-evolution.md`：

- 足够通用。
- 原子化。
- 可执行。
- 可验证。
- 对 OrbitOS 生态有必要。

否则保留在 agent 经验文件或项目 `LESSONS-LEARNED.md`，不进入 learned index。

## 输出结果

Experience Capture 给 Progress Sync 返回以下结果之一：

| result | 含义 |
|---|---|
| `not_applicable` | 检查后确认不需要记录，原因写入 event checklist |
| `captured` | 已写入 agent 经验文件或项目经验文件，当前不具备 learned 条件 |
| `candidate_only` | 已写入规则候选或待观察项，暂不进入 learned index |

Experience Capture 不直接返回 `learned_updated`；该结果只能由 Rule Evolution 更新 learned index 或 learned 使用反馈后产生。

## Progress Sync 要求

Progress Sync 前，agent 必须自检：

```text
本次工作是否产生经验、踩坑、纠正、失败、返工、规则候选或 learned rule 使用反馈？
```

如果答案是“是”：

1. 执行 Experience Capture。
2. 必要时执行 Rule Evolution。
3. 把需要用户确认的事项投影到 `今日.md`。
4. 在 event 中记录本次 capture 动作。

如果答案是“否”，Progress Sync 仍应在 event checklist 中记录 `experience_check: not_applicable` 和跳过原因。

## 执行清单

### 进入检查

- [ ] 已确认出现自动触发或用户触发条件。
- [ ] 已确认当前 agent 已注册并有 agent profile。
- [ ] 已判断本次内容不是普通流水账或隐藏推理。

### 执行检查

- [ ] 已判断记录类型：经验、踩坑、待确认来源、规则候选或 learned rule 使用记录。
- [ ] 已判断这条经验是 agent 级还是项目级。
- [ ] 已写入 `00-系统/agents/{agent_id}-experience.md` 或 `03-项目/{project}/docs/LESSONS-LEARNED.md`。
- [ ] 已记录来源、影响和下一步。
- [ ] 已给出结果：`not_applicable / captured / candidate_only`。
- [ ] 如内容足够通用，已触发或标记 Rule Evolution。
- [ ] 如需要用户确认，已投影到 `今日.md`。

### 退出检查

- [ ] 已在 event 中记录 capture 动作。
- [ ] 已确认没有把一次性问题强行泛化。
- [ ] 已记录所有跳过项和原因。

## 禁止

- 不记录长篇推理。
- 不把普通流水账写成经验。
- 不把用户未确认的偏好写成系统规则。
- 不绕过 agent 经验文件或项目经验文件直接写 learned index。
- 不把一次性问题强行泛化。
