---
title: Inbox Ingest Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-14
updated: 2026-07-13
tags:
  - orbitos
  - workflow
  - inbox
  - ingest
---

# Inbox Ingest Workflow

Inbox Ingest 在用户确认后，把原始输入移到 `01-收件箱/已入库/` 并登记 batch，避免后续 Agent 重复处理。

## 目标

- 移动已处理原件或来源集合并写入最小 ingest batch。
- 把主题、关联和后续方向投影到 `今日.md`，不塞进 batch。
- 按来源或内容集合保存原始文件，不按文件类型建立全局目录。

## 原件存放原则

- `single_source`：PDF、图片、Markdown、音频或其他独立原件原样进入 `已入库/`。
- `source_collection`：同一报告、网页存档、书籍材料或相互依赖的一组文件整体移动并保留目录结构；PDF、配图和摘录可以位于同一集合中。
- 不创建全局 `PDF/`、`图片/` 或 `Markdown/` 分类目录。
- 阅读、知识和项目后续优先链接原件；只有项目构建或发布真正需要的派生资产才进入项目 `repo/`。

## 最小 batch

batch 文件位于 `.orbitos/ingest/batches/`，文件名建议 `INB-YYYYMMDD-NNN.yaml`。

内容使用 JSON-compatible YAML，首版只记录：

```json
{
  "id": "INB-YYYYMMDD-NNN",
  "date": "YYYY-MM-DD",
  "items": [{ "file": "xxx.md", "status": "ingested" }]
}
```

状态只允许：`ingested`、`needs_review`、`discarded`。

## 执行流程

1. 读取用户确认的文件或来源集合清单。
2. 确认每个输入位于 `01-收件箱/` 内，且不是固定入口文件 `00-粘贴.md`；判断它是独立原件还是来源集合。
3. 单一原件原样移动；集合整体移动并逐文件登记 batch，不得按扩展名拆分。
4. 如发现主题、关联或后续方向，写入 `今日.md` 的待确认或可继续区块。
5. 执行 Validate Sync 与 Progress Sync。

## 异常分支

- 文件不在 `01-收件箱/`：停止该文件入库，记录为 blocked。
- 命中 `00-粘贴.md`：停止入库；先进入 `clipboard-flush.md`。
- 文件名冲突：停止移动，询问改名或跳过。
- batch 校验失败：不刷新 Dashboard，进入 validation 回退。
- `needs_review` 没有用户可见投影：标记异常。

## 禁止

- 不在用户确认前移动收件箱内容。
- 不把 `00-粘贴.md` 当作 ingest 原件移动或登记 batch。
- 不把同一来源的 PDF、图片与文字资料按文件类型拆散。
- 不把主题聚类、长理由或价值判断写进 batch。
- 不把低价值内容直接移动到 `99-归档/`；首版使用 `discarded` 留在 `已入库/`。
