---
title: Weekly Review Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-14
updated: 2026-06-16
tags:
  - orbitos
  - workflow
  - review
  - weekly
---

# Weekly Review Workflow

Weekly Review 生成 `02-时间线/本周.md`。

## 目标

- 以 `.orbitos/logs/events/` 为主要事实源。
- 按时间线展示本周核心工作。
- 再做主题归纳、风险和下周聚焦。
- 避免把周回顾写成无时间顺序的泛泛总结。

## 触发条件

- 用户说“本周回顾”“周总结”“周复盘”“这周做了什么”。
- 周日收口时需要整理本周工作。
- 用户要求从 events 回顾系统进展。

## 输入

- `.orbitos/logs/events/` 中本周 event。
- `02-时间线/今日.md`
- 相关项目 `STATUS.md`

如果 event 缺少标准 `timestamp`，按文件名日期归入对应日期，并在来源说明中标注。

## 输出

写入或更新：

- `02-时间线/本周.md`
- 如当前 `本周.md` 属于旧周，先归档到 `02-时间线/归档/YYYY-Www.md`

## 周切换与归档

`本周.md` 永远表示当前 ISO 周。

在写入当前周前必须检查现有 `02-时间线/本周.md` 的周期：

- 如果周期等于当前周，直接刷新 `本周.md`。
- 如果周期早于当前周，先把旧内容保存到 `02-时间线/归档/YYYY-Www.md`，再生成当前周。
- 如果目标归档文件已存在，不覆盖；先比较内容差异，必要时创建 `YYYY-Www_2.md` 并在 event 中说明。
- `02-时间线/归档/` 只保存时间线历史快照，不等同于 `99-归档/`。
- 当前周 `本周.md` 顶部应链接上一周归档；内部 workflow 中只记录示例路径，例如 `02-时间线/归档/2026-W24.md`。

## Scheduled Automation Mode

Scheduled Weekly Review is a constrained form of this workflow:

- It may refresh `本周.md` only when the file already belongs to the current ISO week.
- It must not archive, rename, move, or replace a weekly file at a week boundary.
- When the current page belongs to an earlier week, stop and leave the rollover
  for a user-confirmed Weekly Review run.
- Schedule this task within the current week when automatic weekly synthesis is desired.

## 执行流程

1. 确认本周时间范围，使用 ISO 周：周一到周日。
2. 检查现有 `02-时间线/本周.md` 的周期；如不是当前周，先执行周归档。
3. 扫描 `.orbitos/logs/events/` 中本周 event。
4. 提取每条 event 的：
   - `timestamp`
   - `event_type`
   - `summary`
   - `project`
   - `files_changed`
   - `review_required`
   - `next_steps`
5. 先生成“事件时间线”：
   - 按日期分组。
   - 同一天按时间升序。
   - 只列核心事件，不复制完整 event。
   - 每条控制在一句话。
6. 再生成主题归纳：
   - 本周主线
   - 关键洞察
   - 本周已落地
   - 风险与阻塞
   - 下周聚焦
7. 对 `今日.md` 做时间边界检查：
   - 当天以外的完成项不能继续在今日展开。
   - 旧事项只能作为待确认来源或链接到本周/项目状态。
8. 如本次修改了 `本周.md` 或周归档，执行 Validate Sync。
9. 完成后写 Progress Sync event。

## 推荐结构

```markdown
# 本周洞察

> 周期：YYYY-Www（YYYY-MM-DD 至 YYYY-MM-DD）

## 本周主线

## 事件时间线

### YYYY-MM-DD

- HH:mm：{event summary}

## 关键洞察

## 本周已落地

## 风险与阻塞

## 下周聚焦（YYYY-Www，YYYY-MM-DD 至 YYYY-MM-DD）

## 来源

- `.orbitos/logs/events/YYYYMMDD*`
```

## 执行清单

### 进入检查

- [ ] 已确认 Weekly Review 适用。
- [ ] 已确认本周时间范围。
- [ ] 已检查现有 `本周.md` 是否属于当前周。
- [ ] 如现有 `本周.md` 属于旧周，已先归档到 `02-时间线/归档/YYYY-Www.md`。
- [ ] 已读取本周 event。
- [ ] 已读取今日和相关项目状态；需要时再从今日中定位待确认和可继续入口。

### 执行检查

- [ ] 已先生成 event 时间线。
- [ ] 已再生成主题归纳。
- [ ] 已区分当天 Dashboard 和跨日周回顾。
- [ ] 已保留当前待确认和下周聚焦。

### 退出检查

- [ ] 已更新 `02-时间线/本周.md`。
- [ ] 如发生周切换，已确认旧周归档可从当前 `本周.md` 顶部跳转。
- [ ] 已确认 `02-时间线/今日.md` 没有堆积跨日完成项。
- [ ] 已运行 validation。
- [ ] 已写入 Progress Sync event。

## 禁止

- 不从记忆或印象直接编写周总结。
- 不把 event YAML 全文复制进 `本周.md`。
- 不把周回顾写成只有主题、没有时间线的总结。
- 不把上一天或更早完成项堆回 `今日.md`。
