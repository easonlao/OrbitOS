---
title: 数据生命周期
area: system
purpose: rule
lifecycle: active
created: 2026-06-11
updated: 2026-06-11
tags:
  - orbitos
  - lifecycle
---

# 数据生命周期

## 基本流转

```text
raw input -> event log -> timeline/project view -> review -> artifact/archive
```

## 事实底座

所有实质性工作先写 event。可见 Markdown 是视图或产物，不是唯一事实来源。

## 需要确认

- rule candidate
- ADR candidate
- formal artifact candidate
- knowledge card candidate

## 不默认确认

Hindsight retain 不作为 OrbitOS 必经环节。

## 归档

`02-时间线/归档/` 只放时间线视图快照。

`99-归档/` 放退出当前使用的完整对象。

