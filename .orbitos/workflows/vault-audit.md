---
title: Vault Audit Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-14
updated: 2026-06-14
tags:
  - orbitos
  - workflow
  - audit
---

# Vault Audit Workflow

Vault Audit 自检 OrbitOS 最小内核是否保持一致。

## 目标

- 检查收件箱入库闭环是否完整。
- 发现已入库文件缺 batch、batch 指向文件不存在、`needs_review` 未投影等异常。
- 降低文件放置混乱导致的系统崩溃风险。

## 适用范围

适用于以下情况：

- 用户说“自检”“审核知识库”“检查收件箱”“系统检查”。
- Inbox Ingest 完成后。
- Progress Sync 发现收件箱状态异常。
- 每日或周期性状态刷新前。

## 审核范围

首版只审核最小内核：

- `01-收件箱/`
- `01-收件箱/已入库/`
- `.orbitos/ingest/batches/`
- `02-时间线/今日.md`
- `02-时间线/待确认.md`

不判断内容质量，不评价知识卡片深度，不重排项目结构。

## 执行流程

1. 扫描 `01-收件箱/` 根目录，排除 `已入库/`。
2. 扫描 `01-收件箱/已入库/` 文件。
3. 读取 `.orbitos/ingest/batches/*.yaml`。
4. 校验 batch 是否符合 `.orbitos/schemas/ingest-batch.schema.yaml`。
5. 检查 `已入库/` 中的文件是否都有 batch 记录。
6. 检查 batch 记录中的文件是否真实存在。
7. 检查 `needs_review` 是否能在 `今日.md` 或 `待确认.md` 找到对应待确认投影。
8. 输出简短审核结果。
9. 如有异常，写入 Progress Sync event，并投影到 `今日.md` 的待确认或系统健康。

## 异常类型

- `missing_batch_record`：已入库文件缺少 batch 记录。
- `missing_ingested_file`：batch 记录指向的文件不存在。
- `needs_review_not_projected`：`needs_review` 没有用户可见待确认。
- `stale_root_inbox`：收件箱根目录存在长期未入库文件。
- `invalid_batch_schema`：batch 文件结构不合法。

## 执行清单

### 进入检查

- [ ] 已确认本次是自检审核，不是内容整理。
- [ ] 已确认只审核最小内核范围。
- [ ] 已准备读取收件箱、已入库、ingest batches 和时间线待确认入口。

### 执行检查

- [ ] 已扫描收件箱根目录。
- [ ] 已扫描 `01-收件箱/已入库/`。
- [ ] 已读取并校验 ingest batches。
- [ ] 已检查已入库文件和 batch 记录是否互相对应。
- [ ] 已检查 `needs_review` 是否投影到用户可见入口。
- [ ] 已分类异常类型。

### 退出检查

- [ ] 已输出简短审核结果。
- [ ] 如有异常，已执行 Progress Sync。
- [ ] 已确认没有移动、删除或重写用户内容。
- [ ] 已记录跳过项和原因。

## 禁止

- 不在 Vault Audit 中移动文件。
- 不在 Vault Audit 中创建知识卡片。
- 不把内容价值判断写成审核异常。
- 不把完整 batch 列表塞进 `今日.md`。
