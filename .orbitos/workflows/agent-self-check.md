---
title: Agent Self Check Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-21
updated: 2026-06-21
tags:
  - orbitos
  - workflow
  - agent
  - experience
---

# Agent Self Check Workflow

Agent Self Check 用于整理单个 agent 自己的经验文件。

它独立于 Progress Sync，不属于每次工作结束后的默认收尾动作。

## 目标

- 让 agent 定期收缩自己的经验文件，而不是无限追加。
- 把新踩坑提炼成原子经验。
- 清理已经失效、重复或已被吸收的内容。
- 只在必要时把规则候选交给 learned review。

## 触发条件

以下情况才执行：

- 用户明确说“做一次 agent 自检”“整理经验”“清理踩坑”“收缩 codex/nova/hermes/mimo 的经验”。
- 定时任务按低频策略触发。

默认不在 Startup Sync、Progress Sync 或普通任务收尾中自动执行。

## 范围

一次只处理一个 agent：

```text
00-系统/agents/{agent_id}.md
00-系统/agents/{agent_id}-experience.md
```

必要时可读取该 agent 最近相关 event 作为证据，但不默认横向扫描其他 agents。

## 输入

- 轻量 profile：定位、启动关注、经验入口
- 经验文件：`经验记录 / 踩坑 / 待确认来源 / 规则候选 / Learned Rule 使用记录`
- 必要的近期 event

## 执行流程

1. 确认目标 `agent_id`，读取轻量 profile 与 experience 文件。
2. 检查 `踩坑`：
   - 已被提炼成稳定经验的，删除原坑或合并为更高层经验。
   - 只是重复描述同一问题的，合并。
   - 已因系统修复失效的，删除。
3. 检查 `经验记录`：
   - 保留仍有复用价值的原子经验。
   - 将仍然过长、混杂多条结论的记录拆分。
4. 检查 `待确认来源`：
   - 已确认的，转入经验或规则候选。
   - 已证伪或已无价值的，删除。
5. 检查 `规则候选`：
   - 仍只适用于该 agent 的，回退为经验。
   - 足够通用但尚未进入公共层的，保留候选并标记可进入 learned review。
   - 长期无证据、无复用的，删除。
6. 检查 `Learned Rule 使用记录`：
   - 只保留仍需要回写 learned index 的反馈。
   - 已经回写并不再需要跟踪的旧反馈可以清理。
7. 如发现可共享候选，提示进入 `.orbitos/workflows/learned-review.md`。
8. 如本次修改了经验文件，按需写 event。

## 输出

- 更新后的 `00-系统/agents/{agent_id}-experience.md`
- 可选 event
- 可选“进入 learned review”的建议

## 与其他 Workflow 的关系

- 它可以调用 `.orbitos/workflows/experience-capture.md` 的分类逻辑。
- 它不会自动执行 `.orbitos/workflows/rule-evolution.md`。
- 需要进入公共规则层时，再单独进入 `.orbitos/workflows/learned-review.md`。

## 执行清单

### 进入检查

- [ ] 已由用户要求或定时任务触发。
- [ ] 已确认只处理一个 agent。
- [ ] 已读取轻量 profile 与 experience 文件。

### 执行检查

- [ ] 已清理已被吸收或失效的踩坑。
- [ ] 已收缩重复或过长的经验。
- [ ] 已处理待确认来源。
- [ ] 已判断哪些规则候选值得进入 learned review。

### 退出检查

- [ ] 未横向扫描其他 agents。
- [ ] 未自动提升 learned 或 core。
- [ ] 如有写入，已按需留痕。

## 禁止

- 不把它挂进每次 Progress Sync。
- 不默认横向读取所有 agent。
- 不在本流程中直接提升 core rule。
- 不把完整 event 历史复制进经验文件。
