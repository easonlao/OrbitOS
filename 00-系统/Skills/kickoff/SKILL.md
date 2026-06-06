---
name: kickoff
description: Converts an idea into a structured project, with built-in pressure-test to validate before building
---

# OBJECTIVE

将想法转为结构化项目。**先压力测试，通过后再立项**，避免在错误方向上浪费精力。

## Step 0: 加载上下文

1. 读取 `.orbit/schema/subsystems.yaml`，确认 `04-项目` 工作区约束
2. 读取 `04-项目/WORKSPACE.md`，确认项目分类规则
3. 加载 `workspace-projects` Skill

## Step 1: 确定输入

1. 用户提供收件箱文件路径 → 读取内容
2. 用户提供内联描述 → 直接使用
3. 无输入 → 列出 `01-收件箱/` 中 `status: draft` 的文件

如果缺少关键信息（项目是什么、目标用户/受众、期望结果），先追问再继续。

## Step 2: 压力测试

用以下框架检验想法。**直接、具体、不讨好**。

### 评分卡

| 维度 | 1-5 | 说明 |
|------|-----|------|
| 价值清晰度 | | 要解决什么问题？问题真实吗？ |
| 可行性 | | 现在能做吗？依赖什么前提？ |
| 紧迫性 | | 为什么是现在？两个月后做会怎样？ |
| 差异化 | | 和现有方案有什么本质不同？ |
| 验证速度 | | 多久能拿到反馈？最小验证成本？ |
| 匹配度 | | 你有独特优势吗？还是纯靠努力？ |

分数必须基于具体证据，不能凭空打。

### 核心假设

一句话：什么必须成立，这个项目才值得做？

### 致命缺陷

| 风险 | 严重度 | 为什么重要 | 快速验证方式 |
|------|--------|-----------|-------------|
| ... | 高/中 | ... | ... |

最多列 3 个。按严重度排序。

### 断言

- **通过** → 进 Step 3 创建项目
- **调整** → 指出需要修正的方向，让用户决定
- **放弃** → 直接说为什么，建议放入收件箱归档

### 规则

- 每个缺陷必须针对这个想法，不说"任何项目都有的问题"
- "没有竞争"永远不对——当前做法就是竞争
- 评分基于证据，不是感觉
- 不过度美化，也不过度打击

## Step 3: 创建项目（断言通过后）

1. **判断项目意图** → 一级分类：内容创作 / 产品系统 / 运营增长 / 研究验证 / 实验原型
2. **确定规模** → 单文件 / 目录项目
3. **创建文件**，使用 9 字段 Frontmatter：

```yaml
---
title: "项目名称"
type: roadmap
topic: project
workspace: "04-项目"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["project", ...]
source: agent
status: active
project_type: research    # content|product|operations|research|experiment
project_category: "研究验证"
stage: planning
---
```

4. 项目结构中包含压力测试结论（核心假设和关键风险）作为背景

## Step 4: 清理收件箱

如果来自收件箱条目：`status: processed` → 移到 `99-归档/收件箱/YYYY/MM/`

## Step 5: 记录工作日志

在 `02-日记/工作日志/YYYYMMDD_工作日志_周X.md` 的 `## 重点记录` 追加。

## 输出格式

```
## 项目创建完成

**项目:** [[ProjectName]] 位于 04-项目/<分类>/
**分类:** <分类名>
**压力测试结果:** 通过（评分 X/30）
**核心假设:** ...
**首要风险:** ...

**第一步:**
- [ ] ...
```
