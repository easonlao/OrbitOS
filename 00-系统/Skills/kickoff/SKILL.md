---
name: kickoff
description: Converts an idea or an Inbox note into a structured Project Note
---

# OBJECTIVE

将收件箱中的想法转为结构化项目。遵循 OrbitOS 渐进式加载协议，读取工作区规范后执行。

## Step 0: 加载上下文

1. 读取 `.orbit/schema/subsystems.yaml`，确认 `04-项目` 工作区约束（allowed_types: roadmap/spec/board/note）
2. 读取 `04-项目/WORKSPACE.md`，确认项目分类规则
3. 加载 `workspace-projects` Skill

## Step 1: 确定输入

1. 如果用户提供了收件箱文件路径，读取内容
2. 如果用户提供了内联描述，直接使用
3. 如果无输入，列出 `01-收件箱/` 中 `status: draft` 的文件让用户选择

## Step 2: 分析并创建项目

1. **判断项目意图**，选择一级分类：内容创作/产品系统/运营增长/研究验证/实验原型
2. **确定规模**：单文件(note) / 小型目录(spec+board) / 完整项目(roadmap+spec+board)
3. **创建项目文件**：

**单文件项目**：`04-项目/<分类>/<ProjectName>.md`
**目录项目**：`04-项目/<分类>/YYYYMMDDHHMM_<ProjectName>/`
  - `README.md` — 项目概述和目标
  - `brief.md` — 需求简述（可选）
  - `plan.md` — 阶段/里程碑计划（可选）

4. **使用 9 字段 Frontmatter**：

```yaml
---
title: "项目名称"
type: roadmap          # roadmap|spec|board|note
topic: project
workspace: "04-项目"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["project", ...]
source: agent
status: active
project_type: research  # content|product|operations|research|experiment
project_category: "研究验证"
stage: planning         # planning|executing|reviewing|done
---
```

## Step 3: 清理收件箱

如果项目来自收件箱条目：
1. 更新原文件 frontmatter：`status: processed`
2. 移动到 `99-归档/收件箱/YYYY/MM/`

## Step 4: 记录到工作日志

在今日工作日志 `02-日记/工作日志/YYYYMMDD_工作日志_周X.md` 的 `## 重点记录` 中追加项目启动记录。

## 输出格式

```
## 项目创建完成

**项目:** [[ProjectName]] 位于 04-项目/<分类>/
**分类:** <分类名>
**类型:** <project_type>

**建议的下一步:**
- [ ] 填写 brief.md 细化需求
- [ ] 在 plan.md 中分解第一阶段任务
```
