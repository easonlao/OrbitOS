---
title: Validate Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - workflow
  - validation
---

# Validate Sync Workflow

Validate Sync 是所有写入型 workflow 的前置校验层。

它的目标不是让 agent 写更多内容，而是防止半成品、缺字段、非法状态跳转被投影到 Obsidian 人读视图。

## 触发条件

以下动作前必须执行 Validate Sync：

- 写入 `.orbitos/logs/events/*.yaml`
- 写入 `.orbitos/queues/**/*.yaml`
- 更新 `.orbitos/state/lifecycle-index.yaml`
- 刷新 `02-时间线/今日.md`
- 刷新其他实际存在的人读状态页，例如 `02-时间线/本周.md`

## 校验对象

| 对象 | Schema |
|---|---|
| event | `.orbitos/schemas/event.schema.yaml` |
| lifecycle item | `.orbitos/schemas/lifecycle.schema.yaml` |
| inbox triage queue | `.orbitos/schemas/inbox-triage.schema.yaml` |
| inbox ingest batch | `.orbitos/schemas/ingest-batch.schema.yaml` |
| validation report | `.orbitos/schemas/validation-report.schema.yaml` |

## 执行顺序

1. 生成 draft 文件或内存对象。
2. 用对应 schema 校验 required、type、enum、additionalProperties。
3. 如果是 lifecycle item，额外校验状态跳转是否合法。
4. 校验通过后，才允许写入事实层、队列层和人读视图。
5. 校验失败时进入审核回退。

## 审核回退

校验失败时：

1. 不刷新任何人读状态页，例如 `今日.md` 或 `本周.md`。
2. 写入 validation report。
3. 尽量写入最小 `validation_failed` event。
4. 把系统校验失败投影到 `02-时间线/今日.md` 的待确认或系统健康区块。

如果连完整 event 都无法生成，允许写 fallback event，但必须包含：

```yaml
id:
timestamp:
actor:
event_type: validation_failed
summary:
reason:
actions: []
files_changed: []
review_required: true
next_steps:
```

## 本地验证脚本

优先运行 Python 主实现：

```powershell
python .orbitos/scripts/run-validation.py
```

Windows 本地也可以运行 PowerShell wrapper：

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

如果当前 agent sandbox 无法启动 `pwsh.exe`，仍应优先尝试 Python 主实现。

如果 Python 不可用，运行 Node.js fallback：

```powershell
node .orbitos/scripts/run-validation.mjs
```

Python、PowerShell wrapper 和 Node fallback 都不可用时，才允许手动校验。手动校验必须在 event checklist 中把 validation 标为 `skipped`，并写明：

- 哪个命令失败。
- 失败原因。
- 手动检查了哪些对象。
- 哪些风险仍未覆盖。

脚本必须至少覆盖：

- required 缺失失败
- enum 错误失败
- inbox triage item 缺 reason 失败
- lifecycle 非法跳转失败
- 可见 Markdown 不得使用指向 `.orbitos/` 的 Obsidian 双链
- runtime template 中的 `.orbitos/templates/.orbitos/agents/registry.yaml` 必须符合 agent registry schema
- 真实 `.orbitos/ingest/batches/*.yaml` 必须符合 ingest batch schema
- `01-收件箱/已入库/` 文件必须有 ingest batch 记录，batch 记录指向的文件必须存在

注意：validation 只能检查结构和路径一致性，不能替代任务边界判断。是否越界、是否错误创建正式产物、是否误移动用户内容，必须通过 Progress Sync checklist 和必要时的 Vault Audit 记录。

## Runtime Check

写入型 workflow 前建议先运行：

```powershell
python .orbitos/scripts/env-check.py --agent-id <agent_id>
```

如果报告状态为 `blocked`，停止写入并向用户说明缺失项。
