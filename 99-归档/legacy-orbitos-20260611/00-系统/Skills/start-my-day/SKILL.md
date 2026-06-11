---
name: start-my-day
description: >-
  每日规划工作流。当用户说"开始一天"、"今日规划"、"早上好"、"start-my-day"时触发。
  回顾昨日进展，创建今日工作日志，连接活跃项目。
triggers:
  - 开始一天
  - 今日规划
  - 早上好
  - start-my-day
  - 今日安排
---

# OBJECTIVE

按 OrbitOS 渐进式加载协议执行每日规划：回顾昨日进展，创建今日工作日志，连接活跃项目。

# WORKFLOW

## Step 0: 加载上下文（Silent）

1. 读取 `.orbit/schema/subsystems.yaml`，确认 `02-日记` 工作区的约束
2. 读取 `02-日记/WORKSPACE.md`
3. 加载 `workspace-journal` Skill
4. 仅在需要时加载 `worklog` 领域 Skill

## Step 1: Gather Context (Silent)

1. **Get Today's Date**
   - Determine current date (YYYYMMDD format) and weekday

2. **Read Yesterday's Worklog**
   - If exists, read `02-日记/工作日志/[yesterday]_工作日志_周X.md`
   - Extract unfinished Todo items
   - Note yesterday's key records and decisions

3. **Find Active Projects**
   - Search `04-项目/` for notes with `status: active`
   - For each active project:
     - Current stage and status
     - Pending tasks
     - Last update date (flag if 3+ days stale)
     - Any time-sensitive items

4. **Check Inbox**
   - List files in `01-收件箱/` with `status: draft`
   - Count items waiting to be processed

5. **Fetch AI Content** (run in parallel if possible)
   - Run `ai-newsletters` workflow
   - Run `ai-products` workflow
   - Store top 3-5 items from each for the summary

6. **Analyze & Prioritize**
   - Time-sensitive items first
   - Stale projects (3+ days) flagged
   - Logical next steps per project

## Step 2: Ask User Input (Interactive)

Gather user input:

**Q1:** "今天的主要目标是什么?"
- Options based on active projects + "其他"

**Q2:** "有什么新想法或任务吗?"
- Free text, captured to inbox

**Q3:** "有什么阻碍或顾虑吗?"
- Free text

## Step 3: Create Today's Worklog

1. **Check if today's worklog exists** at `02-日记/工作日志/YYYYMMDD_工作日志_周X.md`
   - If exists: read and update (preserve existing content)
   - If not: create using ThirdSpace worklog template

2. **Populate sections:**
   - **今日重点**: User's main goals from Q1
   - **今日Todo**: Carryover from yesterday + user's focus + project next actions
   - **Git 提交**: (leave empty, Git Hook auto-populates)
   - **重点记录**: (leave empty, user fills throughout day)
   - **关键决策**: User's concerns from Q3 (if any)
   - **问题与风险**: User's blockers from Q3 (if any)
   - **明日计划**: (leave empty, fill at end of day)

3. **Add AI 摘要 section** (below 明日计划):
   - Top 3-5 AI newsletter content opportunities with `[标题](原文链接)`
   - Top 3-5 AI product launches with `[产品](原文链接)`
   - Links to full digests: `[[05-资源/Newsletters/YYYY-MM-DD-Digest]]` and `[[05-资源/产品发布/YYYY-MM-DD-Digest]]`

4. **Add 相关项目 section**:
   - List active projects with current status and last update date
   - Flag stale projects

## Step 4: Process New Ideas (from Q2)

For each new idea mentioned in Q2:
1. Check if it already exists in `04-项目/` or `01-收件箱/`
2. If new, create `01-收件箱/[Brief-Title].md` with 9-field frontmatter:
   ```yaml
   ---
   title: "[Brief Title]"
   type: note
   topic: work
   workspace: "01-收件箱"
   created: "YYYY-MM-DD HH:MM:SS"
   modified: "YYYY-MM-DD HH:MM:SS"
   tags: ["inbox"]
   source: manual
   status: draft
   ---
   [User's description]
   ```

## Step 5: Present Summary

Output in Chinese:

```
## 早安！今日规划已就绪

**今日笔记:** [[02-日记/工作日志/YYYYMMDD_工作日志_周X|YYYY-MM-DD 周X]]

**今日重点:**
- 重点1
- 重点2

**今日Todo:**
- [ ] Todo1
- [ ] Todo2

**活跃项目 ([N]):**
- [[Project1]] — 阶段/状态（上次更新: date）
- [[Project2]] — 阶段/状态（上次更新: date）⚠ 3天未更新

**已记录新想法 ([N]):**
- [[Idea1]]
- [[Idea2]]

**收件箱:** [N] 条待处理

---

**AI 摘要:**

*内容机会:*
- [标题](链接) — [角度]
- [标题](链接) — [角度]

*产品发布:*
- [产品](链接) — [角度]
→ 完整摘要: [[05-资源/Newsletters/...]] | [[05-资源/产品发布/...]]

---

快捷操作:
- `kickoff` — 将收件箱条目转为项目
- `research <话题>` — 深度调研并整理到 03-知识/
- `道痕` — 道痕六层自我反思
```

# IMPORTANT RULES

- **Follow progressive loading** — read schema and WORKSPACE.md before operating
- **Always read yesterday's worklog** — don't assume empty
- **Be specific** — "完善 PYTA 流动性理论笔记" not "处理项目"
- **Time-sensitive items first** — deadlines and events get top priority
- **Flag stale projects** — 3+ days untouched, mark with ⚠
- **Carryover incomplete Todo** — unchecked items from yesterday
- **Don't overwrite** — merge with existing today's worklog
- **Link everything** — use `[[wikilinks]]`
- **Use 9-field frontmatter** — for all new files
- **Keep it fast** — minimize back-and-forth

# EDGE CASES

- **No active projects:** Suggest processing inbox or starting new
- **No yesterday's worklog:** Skip carryover, start fresh
- **Weekend/Monday:** Note the gap, suggest weekly review if needed
- **Empty inbox:** Focus on project execution
- **Today's worklog already exists:** Read, merge, don't duplicate

# TEMPLATE

Worklog format follows ThirdSpace `worklog` Skill template (`00-系统/Skills/worklog/`).

```yaml
---
title: "YYYY-MM-DD 周X 工作日志"
type: "worklog"
topic: "work"
workspace: "02-日记"
created: "YYYY-MM-DD HH:MM:SS"
modified: "YYYY-MM-DD HH:MM:SS"
tags: ["worklog", "work"]
source: "agent"
status: "active"
---
# YYYY-MM-DD 周X 工作日志

## 今日重点

## 今日Todo

## Git 提交

## 重点记录

## 关键决策

## 问题与风险

## 明日计划
```
