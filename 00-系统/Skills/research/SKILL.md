---
name: research
description: Deep research workflow — 深度调研，整理到 03-知识/
---

# OBJECTIVE

深度调研一个话题，输出结构化笔记和原子概念到知识库。遵循渐进式加载协议。

## Step 0: 加载上下文

1. 读取 `.orbit/schema/subsystems.yaml`，确认 `03-知识` 约束（allowed_types: note/card/study/spec/skill/roadmap，一级子目录）
2. 读取 `03-知识/WORKSPACE.md`（如存在）
3. 加载 `workspace-knowledge` Skill

## Step 1: 规划

1. 检查 `04-项目/` 中是否有相关活跃项目
2. 搜索 `03-知识/` 避免重复研究
3. 确定输出结构：
   - 主研究笔记：`03-知识/<主题>/<主题>.md`（type: study）
   - 原子概念：`03-知识/<主题>/<概念>.md`（type: card）
   - 示例代码（如适用）：`03-知识/<主题>/` 下以独立 .md 存放

## Step 2: 调研

1. 使用 web_search 搜索最新信息
2. 使用 web_fetch 阅读关键文档
3. 提取可复用的原子概念

## Step 3: 输出

### 主研究笔记 Frontmatter（9 字段）

```yaml
---
title: "研究主题"
type: study
topic: ai            # ai|dev|reading|work|project|tools|writing|life|system
workspace: "03-知识"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["research", ...]
source: web
status: active
---
```

### 原子概念 Frontmatter

```yaml
---
title: "概念名称"
type: card
topic: ai
workspace: "03-知识"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["concept", ...]
source: web
status: active
---
```

### 主研究笔记结构

```
# 标题

## 概述
## 核心概念（wikilinks 到原子概念）
## 工作原理
## 示例
## 最佳实践
## 常见陷阱
## 参考资源
```

## Step 4: 记录到工作日志

在 `02-日记/工作日志/YYYYMMDD_工作日志_周X.md` 的 `## 重点记录` 中追加研究完成记录。

## 规则

- `03-知识/` 只保留一级子目录，不创建多层嵌套
- 不保存原始网页全文到知识区
- 不确定归属时放 `01-收件箱/待整理/`
- 所有文件使用 9 字段 Frontmatter
