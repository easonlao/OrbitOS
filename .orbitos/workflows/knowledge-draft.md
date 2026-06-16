---
title: Knowledge Draft Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-15
updated: 2026-06-15
tags:
  - orbitos
  - workflow
  - knowledge
---

# Knowledge Draft Workflow

Knowledge Draft 把已入库原始输入转写成可读知识笔记。

## 目标

- 从 `01-收件箱/已入库/` 读取已处理原始输入。
- 在 `04-知识/00-草稿箱/` 新建面向用户阅读的 Markdown 草稿。
- 保留 `01-收件箱/已入库/` 中的原始输入，不修改原文。
- 用正文保留原始来源双链，保证可追溯。
- 让用户确认后再把知识从 `draft` 改为 `active`。

## 适用范围

适用于用户确认某个已入库原始输入值得整理成知识内容时。

它不是 inbox ingest。区别是：

- `inbox-ingest.md`：只把原始输入移动到 `已入库/`，避免重复处理。
- `knowledge-draft.md`：读取已入库原始输入，并新建 `04-知识/00-草稿箱/` 中可读、可复用的知识草稿。

## 输入

- 已入库原始文件。
- 用户给出的整理方向。
- 可选的上下文文件或相关知识笔记。

## 输出

输出文件放在：

```text
04-知识/00-草稿箱/
```

frontmatter 使用可见 Markdown 最小字段：

```yaml
---
title:
area: knowledge
purpose: knowledge
lifecycle: draft
created:
updated:
tags:
---
```

分类、主题、技术栈和使用场景优先写入 `tags`，不新增不必要字段。

正文必须包含来源区块：

```markdown
## 来源

- 原始输入：[[../01-收件箱/已入库/{原始文件名}]]
```

## 生命周期

- `draft`：agent 已转写，等待用户确认。
- `active`：用户确认后，作为长期可用知识。
- `archived`：过时或不再推荐，但保留历史。

首版不使用 `reviewed`，避免增加状态层级。

## 执行流程

1. 确认用户允许把已入库输入整理成知识草稿。
2. 读取目标原始文件，确认它位于 `01-收件箱/已入库/`。
3. 读取 `.orbitos/rules/core/markdown-writing.md`。
4. 判断目标知识笔记文件名，优先使用清晰中文标题。
5. 在 `04-知识/00-草稿箱/` 新建或更新知识草稿，`lifecycle` 必须为 `draft`。
6. 正文保留原始来源双链。
7. 不修改、覆盖、重命名或移动 `01-收件箱/已入库/` 中的原始输入。
8. 把需要用户确认的草稿投影到 `今日.md` 或 `待确认.md`。
9. 执行 Validate Sync。
10. 执行 Progress Sync。

## 确认定稿

用户确认草稿可用后：

1. 将对应知识笔记从 `04-知识/00-草稿箱/` 移动到 `04-知识/{NN-主题目录}/`。
2. 将 `lifecycle` 从 `draft` 改为 `active`。
3. 更新 `updated` 日期。
4. 写入 event。
5. 刷新 `今日.md` 或相关状态视图。

## 异常分支

- 原始文件不在 `01-收件箱/已入库/`：停止并询问是否先执行 inbox ingest。
- 原始文件内容不足以形成知识：只在待确认中记录原因，不强行生成。
- 目标知识文件已存在：先读取现有文件，再更新或询问是否另建。
- 用户未确认：保持 `lifecycle: draft`，不得改为 `active`。

## 执行清单

### 进入检查

- [ ] 已确认当前 workflow 适用。
- [ ] 已确认用户允许整理为知识草稿。
- [ ] 已确认原始输入位于 `01-收件箱/已入库/`。
- [ ] 已读取 Markdown 写作规则。

### 执行检查

- [ ] 已创建或更新 `04-知识/00-草稿箱/` 知识草稿。
- [ ] 已使用最小 frontmatter。
- [ ] 已保留原始来源双链。
- [ ] 已确认未修改已入库原始输入。
- [ ] 已保持 `lifecycle: draft`，未自动定稿。
- [ ] 已把待确认草稿投影到用户可见入口。

### 退出检查

- [ ] 已执行 Validate Sync 或 validation eval。
- [ ] 已执行 Progress Sync 并写入 event。
- [ ] 已记录所有跳过、失败或阻塞项和原因。

## 禁止

- 不把原始输入直接当作知识成品。
- 不修改 `01-收件箱/已入库/` 中的原始输入。
- 不在用户确认前把知识草稿改为 `active`。
- 不新增复杂 frontmatter 字段承担分类职责。
- 不把适合放在知识库的技术经验关进单个 agent profile。
- 不把知识笔记直接提升为 rule；只有经过 Rule Evolution 才能进入规则池。
