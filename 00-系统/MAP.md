---
title: 系统地图
area: system
purpose: map
lifecycle: active
created: 2026-06-11
updated: 2026-06-11
tags:
  - orbitos
  - system
---

# 系统地图

## 系统文档

- [[CONTEXT]]：术语与概念边界
- [[PRINCIPLES]]：运行时原则
- [[DATA-LIFECYCLE]]：数据生命周期
- [[CHANGELOG]]：已落地系统变更
- [[ADR/README]]：重大架构决策索引

## 常用视图

- [[../02-时间线/今日]]：当前日状态
- [[../02-时间线/本周]]：本周洞察
- [[../02-时间线/待确认]]：需要确认的事项
- [[../02-时间线/下一步]]：可推进入口

## 内核文档

- [[../.orbitos/docs/REQUIREMENTS|REQUIREMENTS]]：开发需求
- [[../.orbitos/docs/ARCHITECTURE|ARCHITECTURE]]：开发架构
- [[../.orbitos/docs/DESIGN|DESIGN]]：开发设计
- `.orbitos/docs/README-WRITING.md`：README 编写规范
- `.orbitos/docs/DOC-PROMOTION.md`：内部设计到用户文档的提升规则
- `.orbitos/docs/OBSIDIAN-STANDARD.md`：agent 写可见 Markdown 时遵守的 Obsidian 规范
- `.orbitos/docs/VERSIONING.md`：版本号、changelog、commit 和 release 流程
- `.orbitos/CHANGELOG.md`：完整版本历史

## 机器约束

- `.orbitos/schemas/event.schema.yaml`：事实日志结构
- `.orbitos/schemas/core-change.schema.yaml`：OrbitOS 内核变更结构
- `.orbitos/schemas/lifecycle.schema.yaml`：内容生命周期结构与合法跳转
- `.orbitos/schemas/inbox-triage.schema.yaml`：收件箱盘点结构
- `.orbitos/schemas/validation-report.schema.yaml`：校验报告结构

## 工作流

- `.orbitos/workflows/core-change.md`：内核文件修改流程
- `.orbitos/workflows/validate-sync.md`：写入前校验与审核回退
- `.orbitos/workflows/progress-sync.md`：完成工作后的事实记录与 Dashboard 刷新
- `.orbitos/workflows/inbox-triage.md`：收件箱盘点与去向建议
