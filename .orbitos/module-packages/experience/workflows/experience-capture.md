---
title: Experience Capture Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-08-09
updated: 2026-08-09
tags:
  - orbitos
  - experience
  - module
---

# Experience Capture Workflow

把已完成工作中的可复用做法和踩坑，写入 agent 自己的经验文件。

## 触发（方案 A：软性自检）

- **自动**：完成实质工作并进入 Progress Sync 时，自检一句"本次有无可沉淀经验"。
- **用户触发**：用户说"记一下经验""这个教训记下来"等。
- 无经验可记时直接跳过，不强制、不计数、不设 KPI。

## 写入位置

- 当前 agent 的经验文件：`00-系统/agents/{agent_id}-experience.md`
- 文件不存在时：按 `templates/experience-entry.md` 创建空壳（frontmatter + 空的经验记录/踩坑段落）。
- 文件存在时：追加新条目，不重写已有条目。

## 条目格式

每条经验一行，用 `｜` 分隔四段：

```
- YYYY-MM-DD｜经验内容｜来源（项目/事件）｜影响（后续怎么做）
```

- 踩坑与正向经验都记录；踩坑放在 `## 踩坑` 段，正向放在 `## 经验记录` 段。
- 日期用当天日期，来源写具体项目或事件名，影响写可执行的做法。

## 流程

1. 判断本次工作是否产生可沉淀经验（踩坑、返工、用户纠正、验证过的新做法）。
2. 没有 → 跳过（Progress Sync 中记录 `experience_check: not_applicable`）。
3. 有 → 读现有经验文件；不存在则先创建空壳。
4. 追加条目（追加而非覆盖）。
5. 更新 frontmatter 的 `updated` 日期。
6. Progress Sync 的 event 中记录 `experience_check: captured`。

## 禁止

- 不把经验直接提升为 rule、ADR 或知识卡片——升级走 `rules/experience-record.md` 的显式路径。
- 不覆盖或删除历史条目（除非用户明确要求修正）。
- 不把只适用于单个项目的临时细节当作通用经验。
- 不记录隐私或未公开信息（见 `rules/experience-record.md`）。
