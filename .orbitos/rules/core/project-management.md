---
title: Project Management Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-20
updated: 2026-06-20
tags:
  - orbitos
  - project
  - agent-rule
---

# Project Management Rule

本规则适用于 `03-项目/{project}/` 下的所有项目，只在任务进入具体项目时加载。

## 进入项目

1. 根据用户点名的项目、路径或对象定位目标项目，不扫描整个项目区。
2. 读取项目 `AGENTS.md` 了解目标、架构和特殊规则，再读取 `STATUS.md` 了解当前状态与任务。
3. 只有任务涉及长期路线或完成条件时才读取 `ROADMAP.md`；进入更深目录时继续读取路径上的 `AGENTS.md`。

## 任务进入与流转

用户只需自然提出任务，不需要说“更新 STATUS”“同步进度”或其他触发命令。Agent 自动判断：

1. 当场完成且不需要下次继续的小修改：直接执行，完成后写 event，不创建 STATUS 事项。
2. 需要跨会话继续的工作：写入 STATUS；已有 ROADMAP 归属时标注编号，没有长期路线含义时不强行创建编号。
3. 属于现有 ROADMAP 的目标：只有用户决定现在推进后，才拆成最多 3 项 STATUS 当前事项。
4. 形成新的长期能力或改变完成条件：先说明原因和影响，经用户确认后更新 REQUIREMENTS 与 ROADMAP；只有用户同时决定现在推进时才进入 STATUS。
5. 新事项会替换现有 STATUS 事项或改变当前优先级时，先请用户确认。

Agent 可以提出路线和优先级建议，但用户决定是否进入 ROADMAP、是否现在推进以及当前事项的替换顺序。

禁止自动流转：STATUS 事项不能自动提升为 ROADMAP 目标，ROADMAP 目标也不能自动进入 STATUS。

## 项目文件

- `03-项目/MAP.md` 只导航直属项目，每项一个用户入口和一句说明。
- 项目 `AGENTS.md` 只保存该项目的目标、稳定架构、特殊规则和下层路由，不重复本规则。
- `STATUS.md` 保存详细现状、判断依据、最多 3 项当前任务和 3 项待确认；属于长期路线时标注 ROADMAP 编号，否则标注“临时事项”，不得为满足格式强建路线目标。
- `ROADMAP.md` 保存目标、总体状态和完成条件清单，不展开当前执行任务。
- 完成条件按实现逻辑排列；已验证项使用 `[x]` 并标记 event 能证明的完成日期，未完成项使用 `[ ]`。不要把 STATUS 中的小任务复制成路线图流水账。
- 项目管理目录默认不创建 README；发布仓库或可独立使用模块可以有面向用户的 README。
- 新建 Markdown 先按 `document-semantics.md` 说明唯一职责、现有文件为何不能承载、位置和生命周期。

## 项目与仓库

- 项目根目录保存本地管理状态、私有信息和专项补充；`repo/` 保存实际产品或发布仓库。
- 修改前确认当前文件属于哪一层，并检查正确仓库的 Git 状态；不得把本地状态或私密内容提交到产品仓库。
- Git 跟踪、提交和发布继续遵守 `git-management.md` 与 `versioning.md`，本规则不重复其细节。

## 状态同步

- 实质性工作完成后自动执行 Progress Sync，不要求用户另行触发；用户说“同步进度”只是可选的显式请求。
- 当场完成的小修改只写 event；需要跨会话的状态变化才更新 STATUS。
- 满足完成条件并通过 validation 后，先更新 STATUS 的详细状态，再同步 ROADMAP 的清单与总体状态，并在同一次 Progress Sync 中写 event。
- STATUS 与 ROADMAP 必须在同一次 Progress Sync 中保持一致；今日只投影当天变化。
- 完成历史留在 event 或已发布 CHANGELOG，不堆入 STATUS 或 ROADMAP。
