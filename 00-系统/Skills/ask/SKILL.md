---
name: ask
description: Quick answers to questions without heavy note-taking overhead
---

# OBJECTIVE

快速回答问题，不生成笔记。只在答案包含可复用知识时，主动询问是否保存。

## Workflow

1. **检查知识库**（如相关）：
   - 快速搜索 `03-知识/` 和 `04-项目/` 中的已有内容
   - 如有相关，引用 `[[笔记名]]`

2. **直接回答**：
   - 简洁清晰，代码示例如有帮助则提供
   - 引用已有笔记时用 wikilinks

3. **可选保存**（仅在内容有价值时）：
   - 询问用户是否保存到知识库
   - 如保存，使用 9 字段 Frontmatter，存放于 `03-知识/<主题>/<概念>.md`
   - 琐碎问答不保存

## 9 字段 Frontmatter 模板

```yaml
---
title: "概念名称"
type: card                # card|note
topic: ai                 # ai|dev|reading|work|project|tools|writing|life|system
workspace: "03-知识"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["..."]
source: agent
status: active
---
```
