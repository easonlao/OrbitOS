---
title: Inbox Ingest Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-14
updated: 2026-06-14
tags:
  - orbitos
  - workflow
  - inbox
  - ingest
---

# Inbox Ingest Workflow

Inbox Ingest 把收件箱根目录中的原始输入标记为已处理，避免后续 agent 重复处理。

## 目标

- 把已处理原始输入移动到 `01-收件箱/已入库/`。
- 写入一个最小 ingest batch 索引。
- 把主题、关联和后续方向投影到 `今日.md` 的待确认或可继续区块，不塞进 batch。
- 保持入库动作轻量、可自检、可追溯。

## 适用范围

适用于用户确认处理收件箱内容后。

它不是 inbox triage。区别是：

- `inbox-triage.md`：只盘点、聚类、提出建议，不移动文件。
- `inbox-ingest.md`：在用户确认后，把已处理原始输入移入 `已入库/` 并登记 batch。

## 输入

- 用户确认的待入库文件清单。
- 可选的 triage queue。
- 本次处理产生的待确认方向。

## 最小 batch

batch 文件放在：

```text
.orbitos/ingest/batches/
```

文件名建议：

```text
INB-YYYYMMDD-NNN.yaml
```

内容必须符合 `.orbitos/schemas/ingest-batch.schema.yaml`。

当前 validation 脚本读取 JSON-compatible YAML。实际 batch 文件虽然使用 `.yaml` 后缀，但内容应使用 JSON-compatible 写法，避免不同 agent 的 YAML 解析能力不一致。

首版只允许：

```json
{
  "id": "INB-YYYYMMDD-NNN",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "file": "xxx.md",
      "status": "ingested"
    }
  ]
}
```

`file` 默认指向：

```text
01-收件箱/已入库/{file}
```

## 状态

- `ingested`：已处理并保留原始输入。
- `needs_review`：已处理，但产生需要用户确认的后续方向。
- `discarded`：已处理，判断无后续价值，仅保留痕迹。

## 执行流程

1. 读取用户确认的文件清单。
2. 确认每个文件当前位于 `01-收件箱/` 根目录，且不是固定入口文件 `00-粘贴.md`。
3. 创建 `01-收件箱/已入库/`，如果不存在。
4. 把确认处理的原始文件移动到 `01-收件箱/已入库/`。
5. 写入一个 ingest batch 文件，只记录 `id/date/items.file/items.status`。
6. 如发现主题、关联或后续方向，写入 `今日.md` 的待确认或可继续区块。
7. 执行 Validate Sync。
8. 执行 Progress Sync。

## 异常分支

- 文件不在收件箱根目录：停止该文件入库，记录为 blocked。
- 命中固定入口文件 `00-粘贴.md`：停止入库；它属于持续复用的剪贴板，不是独立原件。
- 目标文件名冲突：停止移动，询问用户是否改名或跳过。
- batch 校验失败：不刷新 Dashboard，进入 validation 回退。
- `needs_review` 没有投影到用户可见待确认入口：自检应标记异常。

## 执行清单

### 进入检查

- [ ] 已确认用户允许本次入库。
- [ ] 已确认本次不是单纯 triage。
- [ ] 已读取必要的文件清单或 triage queue。
- [ ] 已确认不会移动、删除用户未确认的内容。

### 执行检查

- [ ] 已确认每个源文件位于 `01-收件箱/` 根目录，且不包含 `00-粘贴.md`。
- [ ] 已移动文件到 `01-收件箱/已入库/`。
- [ ] 已写入 ingest batch。
- [ ] 如有 `needs_review`，已投影到 `今日.md` 的用户可见待确认区块。
- [ ] 已执行 Validate Sync。

### 退出检查

- [ ] 已执行 Progress Sync 并写入 event。
- [ ] 已确认 batch 中的文件真实存在于 `已入库/`。
- [ ] 已记录所有跳过、失败或阻塞项和原因。

## 禁止

- 不在用户确认前移动收件箱内容。
- 不把 `00-粘贴.md` 当作 ingest 原件移动或登记 batch。
- 不把主题聚类、长理由、价值判断写进 ingest batch。
- 不把 `needs_review` 留在机器层而不投影给用户。
- 不把低价值内容直接移动到 `99-归档/`；首版使用 `discarded` 留在 `已入库/`。
