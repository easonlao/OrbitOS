---
title: OrbitOS Validation Evals
area: internal
purpose: eval
lifecycle: active
created: 2026-06-12
updated: 2026-06-19
tags:
  - orbitos
  - eval
  - validation
---

# OrbitOS Validation Evals

本目录保存最小结构校验集，用来确认 schema 和 workflow 可以约束 agent 写入行为。

## 运行

优先运行 Python 主实现：

```powershell
python .orbitos/scripts/run-validation.py
```

Windows 本地也可以运行 PowerShell wrapper：

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

如果 agent sandbox 无法启动 `pwsh.exe`，仍应优先尝试 Python 主实现。

如果 Python 不可用，使用 Node.js fallback：

```powershell
node .orbitos/scripts/run-validation.mjs
```

## 覆盖范围

- event 必填字段缺失必须失败。
- event enum 错误必须失败。
- inbox triage item 缺少 `reason` 必须失败。
- ingest batch 缺少 `file` 必须失败。
- ingest batch 状态枚举错误必须失败。
- lifecycle 非法状态跳转必须失败。
- 合法样例必须通过。
- 可见 Markdown 不得使用指向 `.orbitos/` 的 Obsidian 双链。
- 可见 Markdown 的双链目标必须存在；代码块中的示例不参与检查。
- 可见 Markdown 不得恢复 `.orbit/`、`02-日记/`、`03-知识/` 或 `04-项目/` 等旧路径与旧目录编号。
- 可见 Markdown 不得把 Hindsight、今日、event 或 active knowledge 描述成违背当前架构边界的角色。
- 全局文档语义规则必须存在、覆盖固定角色，并由根 `AGENTS.md` 路由。
- 2026-06-15 起的新 event 文件名必须符合 `YYYYMMDD_HHMMSS_slug.yaml`，不使用 `evt_` 前缀、空格或连字符。
- 根目录编号流必须存在且不冲突：`00-系统`、`01-收件箱`、`02-时间线`、`03-项目`、`04-知识`、`05-资源`、`06-输出`、`99-归档`。
- `04-知识/` 一级目录必须使用 `NN-名称`，保持知识分类的稳定阅读顺序。
- 真实 agent registry 必须符合 schema。
- 真实 ingest batch 必须符合 schema，且 `01-收件箱/已入库/` 文件与 batch 记录要互相对应。

## 文件命名

脚本根据文件名前缀选择 schema：

- `event.*.yaml`
- `inbox-triage.*.yaml`
- `ingest-batch.*.yaml`
- `lifecycle.*.yaml`

文档一致性样例位于 `doc-consistency/`，使用相同的 `.valid.` / `.invalid.` 命名约定。

脚本根据文件名判断预期：

- 包含 `.valid.` 代表应通过。
- 包含 `.missing-` 或 `.invalid-` 代表应失败。
