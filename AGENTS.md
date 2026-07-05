# OrbitOS Agent 入口

OrbitOS 是多 agent 协作工作台：Obsidian 是人读界面，`.orbitos/` 是机器与运行时层。

本文件是所有 agent 的唯一全局入口契约。具体工作区域可以用自己的 `AGENTS.md` 补充局部路由和约束。

## 1. 必做流程

1. 确认 `.orbitos/` 存在；缺失时停止并报告工作副本不完整。
2. 如果 `.orbitos/agents/registry.yaml` 或 `02-时间线/今日.md` 缺失，运行 `python .orbitos/scripts/init-runtime.py`；脚本不得覆盖已有内容。
3. 进入 `.orbitos/workflows/startup-sync.md`，只同步状态，不推进任务。
4. 根据任务中的项目名、路径和对象定位目标工作区域；沿 OrbitOS 根目录到目标目录依次读取路径上存在的 `AGENTS.md`。
5. 再按当前任务读取最小匹配的 workflow 和 rule。
6. 在开始执行前，必须先判定本轮 `execution_mode`：`direct / delegated / confirm_first`；判定标准与复杂任务约束见 `.orbitos/rules/core/task-boundary.md`。
7. 如果任务命中 `delegated`，必须进入 `.orbitos/workflows/agent-handoff.md` 或其命中的局部协作流程。
8. 如果任务涉及当前用户的协作方式、输出风格或默认配合习惯，且 `00-系统/08-本地协作偏好.md` 存在，再读取该文件；它只代表当前 Runtime 的本地偏好，不自动视为系统通用规则。若文件仍带有 `TODO_UPDATE_LOCAL_COLLAB_PREFS`，先提醒用户更新模板，再决定是否参考其中内容。
9. 完成实质性工作后进入 `.orbitos/workflows/progress-sync.md`。

Startup Sync 默认只读取当前 agent 的轻量 profile；经验和历史问题仅在任务命中、失败返工或排查历史问题时按入口读取。

当前 agent 不在 registry 中时立即停止，不写 registry、profile 或 event；先请用户确认 `agent_id`，再执行 onboarding。

局部 `AGENTS.md` 只约束其目录树，可以补充或收紧本契约，不得放宽全局安全与确认边界。

## 2. Workflow 路由

### 生命周期 Workflow

- 启动同步：`.orbitos/workflows/startup-sync.md`
- 完成与进度同步：`.orbitos/workflows/progress-sync.md`

### 条件触发 Workflow

- 未注册 agent 经用户确认后接入：`.orbitos/workflows/agent-onboarding.md`
- 出现错误、返工、用户纠正或可复用经验：`.orbitos/workflows/experience-capture.md`
- 当前工作需要跨 Agent / 跨会话继续，出现接手异议、局部驳回，或任务命中 `execution_mode=delegated`：`.orbitos/workflows/agent-handoff.md`

### 业务 Workflow

- 收件箱处理：`inbox-triage.md` → `inbox-ingest.md` → `knowledge-draft.md`；知识冲突处理用 `knowledge-conflict.md`；审计用 `vault-audit.md`
- 周回顾：`.orbitos/workflows/weekly-review.md`
- 规则演化：`.orbitos/workflows/rule-evolution.md`
- Hindsight：`.orbitos/workflows/hindsight-bridge.md`

未写完整路径的 workflow 均位于 `.orbitos/workflows/`。

修改 OrbitOS 内核、schema、workflow、目录协议或系统规则时，不走业务路由，先读 `.orbitos/AGENTS.md`。

## 3. Rule 路由

### 写作 Rule

- 固定角色 Markdown 语义：`document-semantics.md`
- 可见 Markdown / README：`markdown-writing.md` / `readme-writing.md`
- 从内部设计提升为用户说明：`doc-promotion.md`
- 思考模块：`03-项目/OrbitOS/docs/DESIGN.md` 中的 思考模块；默认采用自动推荐、显式可见、用户可覆盖的调用方式；它不是额外 workflow

### 维护 Rule

- 处理 `03-项目/{project}/`：`project-management.md`
- Hindsight memory 与直连 API：`hindsight-memory.md`
- Git 边界与 ignore：`git-management.md`
- 版本、commit 与 release：`versioning.md`
- workflow 编写：`workflow-writing.md`
- 命名与 event：`naming.md`
- 任务范围：`task-boundary.md`
- 定时任务：`scheduled-task-boundary.md`

以上 rule 均位于 `.orbitos/rules/core/`，只在任务涉及时读取。创建、修改或审查 MAP、README、AGENTS、STATUS 等固定角色 Markdown 时，先读 `document-semantics.md`。

## 4. 必须暂停确认

- 移动、删除或归档用户内容。
- 改变 Git 跟踪边界。
- 把候选内容提升为 rule、ADR、知识卡片或其他正式产物。
- 关键 schema 字段缺失，或任务需要扩大到用户未指定的范围。
- 让无人值守定时任务写入 OrbitOS 文件。

## 5. 固定约束

### 上下文

- 只读取当前任务和目标工作区域必需的最小上下文；任务切换区域时重新执行语义路由。
- 不全量扫描或重写 vault，不把短确认扩展成未点名的批量工作。
- 目录或文件是否存在，先用 `ls` / `Get-ChildItem` / `stat` / `Test-Path` 做直接确认；`glob` / `find` 只用于枚举或模式匹配，空结果不能直接推断“对象不存在”。
- 需要确认项目是否存在时，先看上一级目录列表，再决定是否继续用模式搜索。

### 文件与数据

- 写可见 Markdown 前读取对应 rule；提及用户可打开的现有 Markdown 时使用 Obsidian 双链。
- Runtime 用户内容与运行状态默认不进入 Git；Product Repo 的发布内容按项目 Git 规则处理。
- 放在 `00-系统/` 下的本地协作偏好仍属于 Runtime 用户内容；只有经用户再次确认并证明已通用化后，才能提升为可进入 Product Repo 的系统说明或 core rule。
- 临时内容不放根目录：待留存输入放 `01-收件箱/`，可丢弃文件放系统临时目录或 `.orbitos/tmp/`。

### 状态与记忆

- Event 记录操作事实；项目 `STATUS.md` 记录项目现状；时间线只做必要投影，不互相替代。
- Hindsight 不是 OrbitOS 运行依赖；命中历史上下文、环境事实、长期偏好或既有决策时先 recall，再用本地文件、event 或工具复核关键结论。
- Hindsight 默认直接走 HTTP API；memory 触发门、retain / skip 边界与 API 格式见 `.orbitos/rules/core/hindsight-memory.md`。
- retain 后必须在 event 中记录；未满足 highlight 条件的内容留在本地主源，不伪装成长期记忆。

### 输出

- 默认只说明做了什么、改了哪里、验证结果和剩余事项；不输出长推理、完整 event 或内部日志。
