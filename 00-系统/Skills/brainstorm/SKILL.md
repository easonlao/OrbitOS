---
name: brainstorm
description: >-
  互动式头脑风暴。当用户说"头脑风暴"、"brainstorm"、"帮我想想"、"打磨想法"时触发。
  帮助用户打磨和完善想法，可选择转为项目或沉淀到知识库。
triggers:
  - 头脑风暴
  - brainstorm
  - 帮我想想
  - 打磨想法
  - 想法讨论
---

# OBJECTIVE

互动式头脑风暴。帮助用户打磨和完善想法，可选择转为项目或沉淀到知识库。

## Phase 1: 头脑风暴

- 提出探索性问题，加深理解
- 建设性地质疑假设
- 从技术、实践、创意、策略多角度探讨
- 识别与现有知识库的关联

## Phase 2: 总结

概括关键洞察和捕获的想法。

## Phase 3: 行动选择

```
## 下一步想做什么?

1. **创建项目** — 将想法转为结构化项目
   → 使用 kickoff 流程，在 `04-项目/<分类>/` 下创建

2. **整理知识** — 将概念沉淀到知识库
   → 在 `03-知识/<主题>/` 下创建笔记（一级子目录）

3. **继续探索** — 保存本次对话到收件箱
```

### Option 1: 创建项目

委托给 kickoff Skill，传递头脑风暴摘要。

### Option 2: 沉淀知识

1. 在 `03-知识/` 下创建一级主题目录
2. 主笔记用 type: study，原子概念用 type: card
3. 所有文件使用 9 字段 Frontmatter：

```yaml
---
title: "标题"
type: study              # study|card|note
topic: ai                # ai|dev|reading|work|project|tools|writing|life|system
workspace: "03-知识"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["..."]
source: manual
status: active
---
```

### Option 3: 保存到收件箱

创建 `01-收件箱/<主题>.md`，9 字段 frontmatter，`status: draft`。
