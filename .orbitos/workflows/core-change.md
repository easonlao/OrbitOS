---
title: Core Change Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-12
tags:
  - orbitos
  - workflow
  - core-change
---

# Core Change Workflow

Core Change 约束 OrbitOS 内核内容的编写和修改。

## 适用范围

修改以下内容前必须执行本流程：

- 根 `AGENTS.md`
- `.orbitos/AGENTS.md`
- `.orbitos/rules/`
- `.orbitos/schemas/`
- `.orbitos/workflows/`
- `.orbitos/scripts/`
- `.orbitos/evals/`
- 项目本地 `docs/`
- 目录协议
- 生命周期规则
- 写入校验规则
- 从项目本地 `docs/` 提升到 `00-系统/` 的规则

## 核心原则

1. 先判断这是内部设计变更，还是用户可见规则变更。
2. 内部设计先写项目本地 `docs/`。
3. 稳定执行规则写 `.orbitos/rules/core/`。
4. 用户可见规则必须经过确认，并改写成用户视角后进入 `00-系统/`。
5. 每次核心变更必须有 reason。
6. 每次核心变更必须说明 validation。
7. 核心变更完成后必须写 event。

## 执行流程

1. 读取 `.orbitos/AGENTS.md`。
2. 如涉及 README，读取 `.orbitos/rules/core/readme-writing.md`。
3. 如涉及 `00-系统/`，读取 `.orbitos/rules/core/doc-promotion.md`。
4. 生成 core-change draft，符合 `.orbitos/schemas/core-change.schema.yaml`。
5. 执行 Validate Sync。
6. 修改目标文件。
7. 写入 event。
8. 更新 `00-系统/07-系统变更.md`。
9. 如果影响当前状态，刷新 `02-时间线/今日.md`。
10. 运行 validation eval。
11. 运行 `python .orbitos/tests/test_runtime.py`；失败时不得 commit 或 push。

## 禁止

- 不解释 reason 就修改内核。
- 不记录 validation 就修改 schema/workflow/script。
- 不经确认就把内部设计讨论提升为用户规则。
- 不把 `.orbitos/` 细节直接塞进用户说明。
