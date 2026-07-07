---
title: Persona Baseline Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-07
updated: 2026-07-07
tags:
  - orbitos
  - workflow
  - persona
  - baseline
---

# Persona Baseline Workflow

## 目标

在用户明确启用动态人物模块时，用一轮 24 题、5 档倾向的基线问卷生成当前工作副本专属的 `00-系统/09-人物档案.md`，并把协作相关的派生结论投影到 `00-系统/08-本地协作偏好.md`。

## 触发条件

- 用户明确要求启用动态人物模块。
- 用户要求开始首轮人物问卷、创建人物档案或重新生成人物基线。

## 状态边界

- 本流程只处理当前工作副本里的本地实例，不修改 Product Repo 的用户内容边界。
- 问卷结果只作为 `hypothesis` 级别的初始定调，不得写成已确认事实。
- Startup Sync、定时任务和无人值守脚本不得自动触发本流程。

## 执行流程

1. 确认这是一次用户显式发起的基线初始化，而不是 Startup Sync 或自动巡检。
2. 先说明边界：这是一份 MBTI 种子问卷，不是官方 MBTI，也不是最终人格定论。
3. 收集一条稳定底色描述，作为 `--identity` 的输入。
4. 先读取 `persona-questioning.md`，再按 `python .orbitos/scripts/persona/mbti.py --print-json` 导出的标准题面逐题收集答案。
5. 默认一次只问 1 题；除非用户明确要求批量回答，否则不得一次混问多题。
6. 允许的答案档位只有 5 种：`-2 / -1 / 0 / 1 / 2`。
   - `-2`：明显偏左
   - `-1`：略偏左
   - `0`：中间 / 视情况
   - `1`：略偏右
   - `2`：明显偏右
7. 提问阶段只允许使用标准题面，不解释人格理论，不即时下结论；用户答非所问时只重问当前题。
8. 把答案写入临时 JSON（系统临时目录或 `.orbitos/tmp/`），不得在根目录散落中间文件。
9. 运行 `python .orbitos/scripts/persona/baseline.py --source 00-系统/09-人物档案.md --identity ... --answers ...` 生成主源。
10. 如当前工作副本已有 `00-系统/08-本地协作偏好.md`，再运行 `python .orbitos/scripts/persona/project.py --source 00-系统/09-人物档案.md --runtime . --collab` 写入派生协作段落。
11. 向用户说明生成结果：MBTI 种子类型、仅为假设、后续以真实行为证据校准。

## 执行清单

### 进入检查

- [ ] 已确认当前 workflow 适用。
- [ ] 已确认这是用户显式发起，不是 Startup Sync 或定时任务。
- [ ] 已向用户说明 MBTI 仅作种子假设。
- [ ] 已读取 `persona-questioning.md`。

### 执行检查

- [ ] 已收集稳定底色描述。
- [ ] 已按 24 题、5 档倾向格式收集答案。
- [ ] 提问阶段已使用标准单题格式，没有自由扩写题意。
- [ ] 已把问卷结果写入 `00-系统/09-人物档案.md`。
- [ ] 已按需把协作相关派生段落投影到 `00-系统/08-本地协作偏好.md`。

### 退出检查

- [ ] 已说明 MBTI 结果只是 hypothesis，不是 confirmed truth。
- [ ] 已运行或确认不需要运行 validation。
- [ ] 已记录跳过项和原因。

## 禁止

- 在用户未明确启用前擅自创建 `00-系统/09-人物档案.md`。
- 把问卷结果写成正式人格结论或医学/心理学判断。
- 在提问阶段解释理论、即时解读答案或一次混问多题。
- 自动生成独立的状态页、方向页或其他额外人物 Markdown。
- 在 Startup Sync、定时任务或只读巡检中偷偷触发本流程。
