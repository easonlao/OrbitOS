---
title: Persona Update Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-07
updated: 2026-07-07
tags:
  - orbitos
  - workflow
  - persona
  - update
---

# Persona Update Workflow

## 目标

在用户明确确认后，把人物模块中的稳定变化正式写回 `00-系统/09-人物档案.md`，并刷新 `00-系统/08-本地协作偏好.md` 的派生协作段落。

## 触发条件

- 用户确认首轮人物基线可以从 `seeded` 进入 `confirmed`。
- 用户明确接受某条校准建议，并要求把它提升为 confirmed pattern。
- 用户明确否决某条校准建议，并要求把它标记为 dismissed。
- 用户明确要求修正稳定底色描述或其他主源中的用户已确认内容。

## 状态边界

- 本流程只处理“用户已确认”的人物更新。
- 未确认的建议继续留在 `suggestions`，不得跳过确认直接进入 confirmed。
- 更新完成后，可以刷新协作偏好投影；但投影仍然不是独立真相源。

## 执行流程

1. 向用户复述本轮要确认的变更对象：
   - 基线确认
   - 接受某条建议并升级为 confirmed
   - 否决某条建议
   - 修正稳定底色描述
2. 按确认类型运行更新脚本：
   - 确认基线：`python .orbitos/modules/persona/scripts/update.py --source 00-系统/09-人物档案.md --runtime . --confirm-baseline`
   - 接受建议：`python .orbitos/modules/persona/scripts/update.py --source ... --runtime . --accept-suggestion <id> --confirmed-statement ... --evidence ...`
   - 否决建议：`python .orbitos/modules/persona/scripts/update.py --source ... --runtime . --dismiss-suggestion <id> --note ...`
   - 修正稳定底色：`python .orbitos/modules/persona/scripts/update.py --source ... --runtime . --identity ...`
3. 如无特殊理由，保持协作偏好投影刷新开启，让 `08-本地协作偏好.md` 同步最新派生段落。
4. 向用户说明写回结果：
   - 哪条建议被接受或否决
   - 哪条 confirmed pattern 新增
   - 基线状态是否变更
   - 协作偏好投影是否已刷新
5. 运行 validation，并在需要时同步进度。

## 执行清单

### 进入检查

- [ ] 已确认当前 workflow 适用。
- [ ] 已拿到用户对本轮人物更新的明确确认。
- [ ] 已明确区分本轮是“建议”还是“确认后的正式更新”。

### 执行检查

- [ ] 已运行 persona update 脚本。
- [ ] 已把结果写回 `00-系统/09-人物档案.md`。
- [ ] 已按需刷新 `00-系统/08-本地协作偏好.md` 的派生段落。

### 退出检查

- [ ] 已向用户解释本轮写回了什么。
- [ ] 已运行或确认不需要运行 validation。
- [ ] 已记录跳过项和原因。

## 禁止

- 不在没有用户确认时修改 baseline、confirmed 或 suggestion 状态。
- 不把 `open` 建议伪装成已确认模式。
- 不让本地协作偏好反向覆盖 `09-人物档案.md`。
