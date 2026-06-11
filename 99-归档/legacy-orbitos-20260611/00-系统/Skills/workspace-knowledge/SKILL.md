---
name: workspace-knowledge
description: Use when maintaining OrbitOS `03-知识`, knowledge cards, topic notes, concept pages, study notes, processed clippings, or long-term knowledge memory.
triggers:
  - "知识卡片"
  - "主题笔记"
  - "知识沉淀"
---

# Workspace Knowledge Skill

## 工作区

`{VAULT}/03-知识`

## 规则来源

先读 `{VAULT}/03-知识/WORKSPACE.md`。

## 文件创建

- 仅根据主题写入收敛后的六大长期领域目录（如 `AI与Agent/YYYYMMDD_标题.md`、`软件与系统/YYYYMMDD_标题.md` 等），严禁写入历史已失效目录。
- 目录内部保持卡片扁平，不再建立二级主题目录。
- `type` 使用 `note` 或 `card`。

## 禁止

- 不保存原始网页全文。
- 不写项目执行文件。
- 不创建临时目录，不新增收敛领域以外的一级子目录。不确定归属时一律放回 `01-收件箱/待整理`。
- 严禁向已失效目录（如 `AI工程/`、`AI/`、`开发/`、`工具与工作流/` 等）写入新卡片。

## 自治维护回路

1. 判断内容是否已经被处理，原始网页全文不直接进入知识区。
2. 选择合适的长期领域目录（如 `AI与Agent`、`软件与系统`），不确定时移入 `01-收件箱/待整理`。
3. 补齐 `workspace=03-知识`、`type=note|card`、`topic`、`status=active` 及 `up`、`related` 关联字段。
4. 创建或移动知识卡片后，检查并更新对应领域目录根部的 `00_MAP_*.md`，追加 Wikilinks 引用。
5. 识别可产出内容，建议流转到 `06-输出`；识别项目执行内容，建议回流到 `04-项目`。

## 审计项

- 是否向历史失效目录（`AI工程/`、`AI/`、`开发/` 等）中写入了新文件。
- 是否存在孤立卡片（无 `up` 字段，且未在任何 `00_MAP_*.md` 地图中被引用）。
- 卡片是否缺 `topic`、`type`、`workspace` 等 Frontmatter。
- 卡片内部是否包含清晰的二级标题和尾部关联区。

## 修复策略

- 可自动修复：补基础 Frontmatter（含 `up: [[00_MAP_领域]]`），向对应 MAP 追加链接。
- 写队列：建议原始材料回 `01-收件箱` 或 `05-资源`。
- 必须 trace：跨工作区移动知识文件。
