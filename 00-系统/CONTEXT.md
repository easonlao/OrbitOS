---
title: 术语表
area: system
purpose: record
lifecycle: active
created: 2026-06-11
updated: 2026-06-11
tags:
  - orbitos
  - context
---

# 术语表

## Agent

具体执行体，例如 Hermes、HanaAgent、Codex、Claude Code。

## Role

可加载的专家身份，不绑定具体 agent。

## Thinking Mode

可组合的方法论，例如金字塔原理、SWOT、苏格拉底提问。

## Workflow

按阶段执行的协作流程。

## Event

机器事实日志，是 OrbitOS 的事实底座。

## Schema

严格结构约束。用于规定 event、queue、lifecycle item 等机器写入对象必须包含哪些字段、字段类型是什么、哪些枚举值合法。

## Lifecycle

内容对象从进入 OrbitOS 到被盘点、确认、处理、归档的状态流转。首版状态为 `raw -> triaged -> confirmed -> processed -> archived`。

## Queue

机器处理队列。记录 agent 的中间判断和待执行建议，例如收件箱盘点结果。Queue 不是用户主入口。

## Dashboard

用户每天打开的当前总控台。首版由 `02-时间线/今日.md` 承担，汇总当前状态、待确认、下一步、收件箱状态、项目状态和系统变更。

## Artifact

面向人阅读或复用的可见产物。

## Review

需要用户确认后才能长期生效的候选事项。

## Hindsight

可选记忆增强层，不是 OrbitOS 的事实底座。

## Validation

写入前结构校验。所有写入型 workflow 在刷新人读视图前，必须先校验 schema；失败时进入审核回退。

## Eval

最小验证集。用于确认 schema 和 workflow 能约束 agent 行为，例如必填字段缺失、枚举错误、生命周期非法跳转必须失败。
