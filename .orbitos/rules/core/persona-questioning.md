---
title: Persona Questionnaire Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-07-07
updated: 2026-07-07
tags:
  - orbitos
  - persona
  - questionnaire
  - agent-rule
---

# Persona Questionnaire Rule

本规则只约束动态人物模块的首轮基线提问阶段，目标是压缩 Agent 在问卷过程中的自由发挥空间。

## 核心原则

- 问卷阶段只负责收集答案，不负责当场解释人格。
- 基线提问必须标准化，尽量由脚本输出 canonical 题面，不靠 Agent 临场改写。
- 在用户没有明确要求批量回答时，默认一次只问 1 题。

## 标准流程

1. 先说明边界：这是一份 MBTI 种子问卷，不是官方 MBTI，也不是最终人格定论。
2. 先收集一条 `identity`，只要一句稳定底色描述。
3. 进入 24 题问卷后，按 `python .orbitos/scripts/persona/mbti.py --print-json` 导出的标准题面逐题提问。
4. 每题只接受 `-2 / -1 / 0 / 1 / 2` 五种回答。
5. 如果用户回答不在允许范围内，只重问当前题，不得擅自解释、转义或跳题。
6. 全部答完前，不得输出 MBTI 类型、人格判断或偏好结论。

## 单题格式

默认题面必须收敛到下面这个形状：

```text
第 N/24 题
- 左侧：...
- 右侧：...
请只回复一个值：-2 / -1 / 0 / 1 / 2。
```

如果用户忘记量表，可以补充一次：

```text
-2 = 明显偏左
-1 = 略偏左
0 = 中间 / 视情况
1 = 略偏右
2 = 明显偏右
```

## 禁止

- 在提问阶段解释 MBTI 理论、维度定义或人格模型。
- 擅自补充示例、诱导语、安慰语或题外分析。
- 一次混问多题，除非用户明确要求批量作答。
- 根据单题答案即时宣布“你就是某种类型”。
- 为了“更自然”而改写脚本导出的题意，导致同一题在不同 Agent 间漂移。

## 适用说明

- 本规则只约束 `persona-baseline.md` 的问卷提问阶段。
- `persona-calibration.md` 与 `persona-update.md` 不使用这套逐题问法。
