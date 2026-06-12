---
title: OrbitOS Validation Evals
area: internal
purpose: eval
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - eval
  - validation
---

# OrbitOS Validation Evals

本目录保存最小结构校验集，用来确认 schema 和 workflow 可以约束 agent 写入行为。

## 运行

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

## 覆盖范围

- event 必填字段缺失必须失败。
- event enum 错误必须失败。
- inbox triage item 缺少 `reason` 必须失败。
- lifecycle 非法状态跳转必须失败。
- 合法样例必须通过。

## 文件命名

脚本根据文件名前缀选择 schema：

- `event.*.yaml`
- `inbox-triage.*.yaml`
- `lifecycle.*.yaml`

脚本根据文件名判断预期：

- 包含 `.valid.` 代表应通过。
- 包含 `.missing-` 或 `.invalid-` 代表应失败。
