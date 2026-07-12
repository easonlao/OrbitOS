---
title: Code Project Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-10
updated: 2026-07-10
tags:
  - orbitos
  - workflow
  - project
  - code
  - matt-pocock
---

# Code Project Workflow

## 目标

让带 `repo/` 的代码型项目以项目层为稳定入口，并通过 Matt Pocock Skills 获得明确的工程推进路径。

OrbitOS 不复制或改写这些 skills。它只确认项目结构、记录当前接入状态，并在用户明确启用 Engineering 模块后安装和配置所需的官方 skills。

## 触发条件

- 新项目经确认创建了 `repo/`。
- 进入已有项目，且项目根目录存在 `repo/`。
- 用户明确要求开始、继续或检查代码型项目。

## 前置条件

- 项目根存在 `AGENTS.md`、`STATUS.md` 与 `repo/`。
- 先读取项目 `AGENTS.md` 和 `STATUS.md`，再进入 `repo/`。
- 用户已确认本项目属于代码型项目。

## 工程接入

1. 先询问用户是否为本项目启用 Engineering 模块与 Matt Pocock Skills；仅发现 `repo/` 不构成安装授权。
2. 用户确认启用后，检查当前 Agent 环境是否已有所需 Matt Pocock Skills。
3. 缺失时，使用当前 Agent 环境支持的官方安装方式安装所需 skills；官方来源为 `https://github.com/mattpocock/skills`。
4. 安装完成后，运行 `/setup-matt-pocock-skills`，由该 skill 配置 issue tracker、triage 标签和工程文档位置。
5. 在 `STATUS.md` 写入 Engineering 已启用、安装/配置结果、当前工程阶段与下一步推荐 skill。
6. 如果用户明确不启用，记录为项目例外，继续保留项目层 `AGENTS.md`、`STATUS.md` 与 `repo/` 边界；不要伪造 skills 已安装或配置完成。
7. 配置完成后，继续按当前项目阶段推荐 skill；不要把 skill 的内部步骤复制进 OrbitOS workflow。

## 阶段推荐

| 项目阶段 | 推荐显式调用 |
|---|---|
| 需求、边界或领域语言尚未收敛 | `/grill-with-docs` |
| 已完成讨论，需要形成可实施规格 | `/to-spec` |
| 规格需要拆成可追踪工作项 | `/to-tickets` |
| 进入实现 | `/implement` |
| 功能或修复需要反馈闭环 | `/tdd` |
| 实现完成，准备提交前复核 | `/code-review` |
| 出现复杂故障或性能回归 | `/diagnosing-bugs` |
| 代码结构持续恶化，需要架构收敛 | `/improve-codebase-architecture` |

`/ask-matt` 可在用户不确定当前适用 skill 时作为路由入口。项目不应把“已安装 skill”伪装成“已完成该阶段”；每次完成仍需由项目事实、验证结果和 `STATUS.md` 更新共同证明。

## 状态记录

项目 `STATUS.md` 继续是唯一项目状态源。它至少要让人和 Agent 看见：

- 代码项目已建立，且 `repo/` 是产品仓库边界。
- Matt Pocock Skills 是否已完成 `/setup-matt-pocock-skills` 配置。
- 当前工程阶段、最近实际完成项与下一步推荐 skill。
- skills 未安装、用户暂缓接入或外部工具不可用时的明确阻塞说明。

具体 STATUS frontmatter 契约由项目状态 schema 落地时统一定义；本 workflow 不提前创建平行状态文件。

## 执行清单

### 进入检查

- [ ] 项目根存在 `AGENTS.md`、`STATUS.md` 和 `repo/`。
- [ ] 已先读取项目层入口和状态源，未直接从 `repo/` 开始。
- [ ] 已确认当前任务属于代码型项目工作。

### 执行检查

- [ ] 已先获得用户启用确认；仅在确认后安装缺失 skills 并运行 setup。
- [ ] 已按当前阶段推荐对应的官方 skill，未重写其内部流程。
- [ ] 项目状态变化时已先更新 `STATUS.md`。

### 退出检查

- [ ] 已运行与本次代码或文档变更相称的验证。
- [ ] 已通过 Progress Sync 记录实际完成项与待确认事项。
- [ ] 未把项目层状态、私有材料或运行时用户内容写入 `repo/`。

## 禁止

- 不得把 `repo/` 当成项目入口或项目状态源。
- 未经用户明确启用，不得安装或更新 Matt Pocock Skills。
- 不得把 OrbitOS workflow 包装成 Matt Pocock Skills 的替代实现。
- 不得因为 skills 未安装而伪造初始化已完成。