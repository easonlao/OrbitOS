# OrbitOS Agent 入口

OrbitOS：Obsidian 为人读界面、`.orbitos/` 为机器运行层的本地工作系统。本文件是唯一全局入口契约，只保留安全红线与按需路由；局部 `AGENTS.md` 只约束其目录树，可补充收紧，不得放宽安全边界。

## 启动（3 步）

1. 确认 `.orbitos/`、`.orbitos/agents/registry.yaml`、`02-时间线/今日.md` 存在；缺失时停止报告，不擅自初始化用户内容。
2. registry 中查本 agent：未注册→停止并请用户确认 `agent_id` 后走 onboarding；`offboarding` / `offboarded`→停止。
3. 读 `02-时间线/今日.md` 同步状态后直接开工。不做额外仪式；详细流程与异常处理见 `.orbitos/workflows/startup-sync.md`。

## 按需路由（任务命中才读，不默认加载）

- 收尾：完成实质性工作后按 `.orbitos/workflows/progress-sync.md` 跑 validation 并写 event。
- 任务范围与执行模式：`.orbitos/rules/core/task-boundary.md`。
- 知识流转与调用：`knowledge-flow.md` 与 `knowledge-use.md`；收件箱处理 `inbox-triage.md` → `inbox-ingest.md` → `knowledge-draft.md`；提炼门槛 `knowledge-refinement.md`；对话目的不明先 `chaos-capture.md`。
- 处理粘贴内容：先 `.orbitos/workflows/clipboard-flush.md`。
- 项目管理（项目判定、STATUS/ROADMAP 纪律、`repo/` 边界）：`.orbitos/rules/core/project-management.md`。
- 固定角色 Markdown 语义（MAP/README/AGENTS/STATUS 等）：`.orbitos/rules/core/document-semantics.md`。
- 思考：用户说"启动思考模式"或任务命中思考触发器时，读 `.orbitos/rules/core/thinking.md` 并展示思考模式启动选择；用户说"直接做"前不进入实质分析。
- 交出任务：用户显式 `$handoff`、说"交给另一位 Agent 继续"或"把任务交给 {agent_id}"时，进入 `.orbitos/modules/collaboration/workflows/handoff-adapter.md`；获取交接：说"获取交接工作"时进入 `.orbitos/modules/collaboration/workflows/handoff-pickup.md`。
- 可选模块：只有 `.orbitos/state/modules.json` 中 `ready` 的模块可进入其 workflow、rule 或可见域；其他状态先说明缺口，不擅自创建模块文件或目录。

## 安全红线（动手前必须经用户确认）

- 移动、删除或归档用户内容。
- 改变 Git 跟踪边界（init / clone / 推送远端 / 修改跟踪范围）。
- 把候选内容提升为 rule、ADR、知识卡片或其他正式产物。
- 关键 schema 字段缺失，或任务需要扩大到用户未指定的范围。
- 让无人值守定时任务写入 vault 文件。

## 行为约束

- 只读当前任务所需的最小上下文，不全量扫描 vault；目录或文件是否存在用 `ls` / `stat` 直接确认。
- 临时内容不入根目录：可丢弃放系统临时目录或 `.orbitos/tmp/`，待留存放 `01-收件箱/`；项目内容写 `03-项目/<项目>/` 并遵循该项目局部规则。
- 写可见 Markdown 前读 `.orbitos/rules/core/markdown-writing.md`。
- 在 `E:\SynologyDrive` 同步盘内新建 git 仓库后，必须运行 `.orbitos/scripts/add-git-exclusions.py`。
- 汇报只说做了什么、改了哪里、验证结果和剩余事项。
