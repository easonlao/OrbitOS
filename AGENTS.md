# OrbitOS Agent 入口

OrbitOS 是多 agent 协作工作台：Obsidian 是人读界面，`.orbitos/` 是机器与运行时层。

本文件是所有 agent 的唯一入口契约，只保留开始工作前必须知道的内容。具体步骤由对应 workflow 和 rule 定义。

## 1. 必做流程

1. 确认 `.orbitos/` 存在；缺失时停止并报告工作副本不完整。
2. 如果 `.orbitos/agents/registry.yaml` 或 `02-时间线/今日.md` 缺失，运行 `python .orbitos/scripts/init-runtime.py`；脚本不得覆盖已有内容。
3. 进入 `.orbitos/workflows/startup-sync.md`，只同步状态，不推进任务。
4. 按当前任务读取最小匹配的 workflow 和 rule，不全量扫描 vault。
5. 完成实质性工作后进入 `.orbitos/workflows/progress-sync.md`。

Startup Sync 默认只读取当前 agent 的轻量 profile；经验、踩坑和规则候选仅在任务命中、失败返工或排查历史问题时按入口读取。

当前 agent 不在 registry 中时立即停止，不写 registry、profile 或 event；先请用户确认 `agent_id`，再执行 onboarding。

## 2. Workflow 路由

### 必用 Workflow

- 启动同步：`.orbitos/workflows/startup-sync.md`
- 完成与进度同步：`.orbitos/workflows/progress-sync.md`
- 未注册 agent 经用户确认后接入：`.orbitos/workflows/agent-onboarding.md`
- 出现错误、返工、用户纠正或可复用经验：`.orbitos/workflows/experience-capture.md`

### 业务 Workflow

- 收件箱处理：`inbox-triage.md` → `inbox-ingest.md` → `knowledge-draft.md`；审计用 `vault-audit.md`
- 周回顾：`.orbitos/workflows/weekly-review.md`
- 提炼规则候选：`.orbitos/workflows/rule-evolution.md`
- Hindsight：`.orbitos/workflows/hindsight-bridge.md`

未写完整路径的 workflow 均位于 `.orbitos/workflows/`。

修改 OrbitOS 内核、schema、workflow、目录协议或系统规则时，不走业务路由，先读 `.orbitos/AGENTS.md`。

## 3. Rule 路由

### 写作 Rule

- 可见 Markdown / README：`markdown-writing.md` / `readme-writing.md`
- 从内部设计提升为用户说明：`doc-promotion.md`

### 维护 Rule

- Git 边界与 ignore：`git-management.md`
- 版本、commit 与 release：`versioning.md`
- workflow 编写：`workflow-writing.md`
- 架构决策记录：`adr-writing.md`
- 命名与 event：`naming.md`
- 任务范围：`task-boundary.md`
- 定时任务：`scheduled-task-boundary.md`

以上 rule 均位于 `.orbitos/rules/core/`，只在任务涉及时读取。

## 4. 必须暂停确认

- 创建未知 agent 的 profile 或注册信息。
- 移动、删除或归档用户内容。
- 改变 Git 跟踪边界。
- 把候选内容提升为 rule、ADR、知识卡片或其他正式产物。
- 关键 schema 字段缺失，或任务需要扩大到用户未指定的范围。
- 让无人值守定时任务写入 OrbitOS 文件。

## 5. 固定约束

- 具体项目只读其 `README.md`、`STATUS.md` 和任务明确相关的文件。
- 可见 Markdown 写入前读取对应规则；提及可打开的可见 Markdown 时使用 Obsidian 双链。
- 用户输入、资源、输出、归档、运行日志和本地工具状态默认不上传 Git。
- 临时内容不放根目录：待留存输入放 `01-收件箱/`，可丢弃文件放系统临时目录或 `.orbitos/tmp/`。
- `.orbitos/logs/events/` 是事实底座；人读页面只保留当前状态和必要摘要。
- Hindsight 是可选记忆层；使用时先 recall，retain 后必须在 event 中记录。
- 默认输出只说明：做了什么、改了哪里、验证结果、还剩什么。
