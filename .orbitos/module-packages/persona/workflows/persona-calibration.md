---
title: Persona Calibration Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-07
updated: 2026-07-07
tags:
  - orbitos
  - workflow
  - persona
  - calibration
---

# Persona Calibration Workflow

## 目标

基于当前工作副本里的真实行为证据，生成可审阅的校准建议，并只写入 `00-系统/09-人物档案.md` 的建议区；不改写稳定基线，不自动确认任何人格结论。

## 触发条件

- 用户要求校准人物模块。
- 用户要求检查当前人物档案与真实协作方式是否矛盾。
- Agent 在人物模块命中任务中发现明显矛盾，并先征得用户同意执行校准检查。

## 状态边界

- 本流程只追加或更新开放校准建议，不改 baseline、不改 confirmed。
- 本流程属于 `manual_supported`：需要用户或 Agent 显式触发，不自动巡检写入。
- 校准建议默认是 `open`，必须经过后续更新流程才可进入 confirmed 或影响稳定基线。

## 执行流程

1. 确认 `00-系统/09-人物档案.md` 已存在，且不是 `baseline_status: pending` 的未初始化骨架。
2. 向用户说明：本轮只生成校准建议，不会自动改写人物主源中的稳定基线。
3. 运行 `python .orbitos/modules/persona/scripts/calibrate.py --source 00-系统/09-人物档案.md --runtime .`。
4. 读取新增的建议，向用户说明：
   - 观测到什么行为证据
   - 与哪条假设或基线有冲突
   - 建议如何理解或后续如何确认
5. 如果用户暂不处理，建议保留 `open` 状态，等待后续更多证据。
6. 如果用户已明确判断，应转入 `.orbitos/modules/persona/workflows/persona-update.md`，而不是在本流程里直接改 confirmed 或 baseline。

## 执行清单

### 进入检查

- [ ] 已确认当前 workflow 适用。
- [ ] 已确认人物主源已完成首次基线，不是 pending 骨架。
- [ ] 已向用户说明本流程只产出建议，不自动改写主源稳定部分。

### 执行检查

- [ ] 已运行校准脚本。
- [ ] 已把新增建议写入主源建议区。
- [ ] 已向用户解释本轮建议的证据、冲突点和后续动作。

### 退出检查

- [ ] 未改写 baseline 或 confirmed。
- [ ] 如需落地确认，已转入 `.orbitos/modules/persona/workflows/persona-update.md`。
- [ ] 已运行或确认不需要运行 validation。

## 禁止

- 不把校准建议直接写成 confirmed。
- 不静默改写 `09-人物档案.md` 的稳定底色或 MBTI 种子说明。
- 不在定时任务或 Startup Sync 中自动写入校准建议。
