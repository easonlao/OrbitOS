---
title: Reading Prepare Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-11
updated: 2026-07-11
tags:
  - orbitos
  - reading
  - inbox
---

# Reading Prepare Workflow

准备阅读材料，把一个经用户确认的收件箱输入交给 echo-reading 的 `book-ingest`。它统一处理单源文件和已拆章节集合：前者探测后拆章，后者保留既有顺序并逐章校验。本 workflow 只负责 OrbitOS 入口与来源桥接，不改写阅读内核。

## 前提

- 用户已明确确认指定材料进入阅读域。
- 源文件先位于 `01-收件箱/`，且不是 `00-粘贴.md`。
- 已完成 `inbox-ingest.md`：原件移动到 `01-收件箱/已入库/` 并写入 ingest batch。

## 流程

1. 读取 `05-阅读/AGENTS.md`、`.orbitos/modules/reading/README.md` 与 `skills/echo-reading/book-ingest/SKILL.md`。
2. 使用已入库输入执行 `book-ingest`：单文件执行格式探测、章节切分和原文完整性校验；已拆章节集合执行顺序映射与逐章原文校验，不重新合并或拆分。

   已拆章节集合使用 `book-ingest/scripts/import_presplit_collection.py`，以显式 `--chapter` 参数声明原有顺序；它只接受 `01-收件箱/已入库/` 下的集合目录，并拒绝覆盖已有书目录。
3. 只有 `book-ingest` 的原文写入与完整性校验通过后，才在 `05-阅读/books/<书名>/.orbitos-source.json` 写入。单文件使用 `inbox_path`，集合使用 `inbox_paths`：

```json
{
  "version": 1,
  "inbox_path": "01-收件箱/已入库/<原件文件名>",
  "ingest_batch": "INB-YYYYMMDD-NNN",
  "source_filename": "<原件文件名>",
  "prepared_at": "YYYY-MM-DD"
}
```

集合 sidecar 使用：

```json
{
  "version": 1,
  "source_kind": "collection",
  "inbox_paths": ["01-收件箱/已入库/<集合>/<章节文件>"],
  "ingest_batch": "INB-YYYYMMDD-NNN",
  "source_name": "<集合名称>",
  "prepared_at": "YYYY-MM-DD"
}
```

4. 简短投影书名、当前阅读位置和可继续入口到 `今日.md`；不复制书籍原文、进度清单或 Insight 正文。
5. 运行 `python .orbitos/scripts/reading-health-check.py`，再执行 Validate Sync。

## 禁止

- 不在用户确认前运行 `book-ingest`。
- 不跳过收件箱入库或伪造 ingest batch。
- 不改写 `raw.md`、`progress.md` 或原始 skills。
- 不把 Insight 自动提升为知识或 Hindsight。

## 后续

完成 `book-ingest` 后，用户可以：
1. 对长章执行 `chapter-split` 切分为阅读单元（见 `skills/echo-reading/chapter-split/SKILL.md`）。
2. 对切分后的单元执行 `deep-reading` 深读陪读（见 `workflows/deep-reading.md`）。
3. 在深读过程中使用 `annotate` 添加批注（见 `skills/echo-reading/annotate/SKILL.md`）。
