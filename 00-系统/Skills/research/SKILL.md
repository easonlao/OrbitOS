---
name: research
description: >-
  深度调研工作流。当用户说"研究一下"、"帮我调研"、"深入了解"、"research"时触发。
  输出结构化研究笔记和原子概念到 03-知识/。
  支持领域persona自动匹配（金融/技术/健康/认知）。
triggers:
  - 研究
  - 调研
  - 深入了解
  - research
  - 帮我查一下
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
3. **匹配 Persona**：根据话题领域，读取 `references/personas/` 下对应文件作为思维框架：
   - 加密货币/区块链 → `Finance_Crypto.md`
   - 投资组合/资产配置 → `Finance_Portfolio.md`
   - 股票/技术分析 → `Finance_StockMarket.md`
   - 债务/财务规划 → `Finance_Debt.md`
   - 税务 → `Finance_Tax.md`
   - 软件架构 → `SE_Architect.md`
   - 代码质量/工程实践 → `SE_CodeBase.md`
   - 技术面试 → `SE_Interview.md`
   - 健康/医疗 → `Health_General.md` / `Health_Medication.md` / `Health_Nutrition.md`
   - 认知/决策 → `General_FirstPrinciples.md` / `General_Latticework.md` / `General_SecondOrderThinking.md`
   - 无匹配领域 → 跳过，使用通用研究视角
4. 确定输出结构：
   - 主研究笔记：`03-知识/<主题>/<主题>.md`（type: study）
   - 原子概念：`03-知识/<主题>/<概念>.md`（type: card）
   - 示例代码（如适用）：`03-知识/<主题>/` 下以独立 .md 存放

## Step 1.5: 确认研究方向（必须）

向用户展示研究计划，等确认后再执行：

```
## 研究计划

**主题:** [研究话题]
**领域:** [匹配的persona或"通用"]
**避免重复:** [已在03-知识/中存在的相关笔记]

### 输出结构
- 主笔记: `03-知识/<主题>/<主题>.md`
- 原子概念:
  - [[概念1]] — 简要说明
  - [[概念2]] — 简要说明

### 研究方向
1. [方向1]
2. [方向2]
3. [方向3]

确认后开始调研，或告诉我调整方向。
```

用户确认后再进入Step 2。如果用户要求调整，回到Step 1修改计划。

## Step 2: 调研

1. 带着 persona 的领域视角进行研究
2. 使用 web_search 搜索最新信息
3. 使用 web_fetch 阅读关键文档
4. 提取可复用的原子概念

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

## 边界条件

| 场景 | 处理方式 |
|------|---------|
| 话题太宽泛 | Step 1.5 中拆分为 2-3 个子话题，让用户选择聚焦哪个 |
| 搜索无结果 | 换关键词重试一次；仍无则告知用户，建议缩小范围 |
| web_fetch 失败 | 跳过该来源，用其他搜索结果补充；记录到笔记的「参考资源」中标注「访问失败」 |
| 已有相关研究 | Step 1 检测到 `03-知识/` 有同主题笔记时，询问用户：更新现有笔记 or 新建？ |
| persona 无匹配 | 跳过 persona 加载，使用通用研究视角，不影响流程 |
