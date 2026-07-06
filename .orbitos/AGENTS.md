# OrbitOS 内部开发入口

本文件只用于开发或扩展 OrbitOS 本身。

仅在修改以下内容时读取：

- 目录协议
- schema
- workflow
- 机器日志
- 生命周期规则
- 面向系统的 Markdown 规则
- 稳定的 agent 执行规则
- 根 README 的定位或编写规则
- 设计来源、`.orbitos/rules/` 与 `00-系统/` 之间的内容提升
- 版本、changelog、commit 或 release 规则
- Git ignore、仓库边界或已跟踪文件清理规则
- `.orbitos/` 内部内容

## 开发规则

1. 根 `AGENTS.md` 必须保持为唯一使用入口。
2. 面向用户的系统说明放在 `00-系统/`。
3. 稳定的 agent 执行规则放在 `.orbitos/rules/core/`。
4. 实现、schema、workflow 和设计文档放在 `.orbitos/`。
5. 已确认的当前版本系统变化记录在 `00-系统/07-系统变更.md`。
6. Architecture/Design 记录当前系统；项目级决策历史由各项目自己的工程文档约定处理，运行层不再提供独立 ADR 机制。
7. 未经用户明确确认，不得把讨论或脑暴直接提升为规则或其他正式产物。
8. 修改根 README 前，先读 `.orbitos/rules/core/readme-writing.md`。
9. 将设计内容提升到 `00-系统/` 前，先读 `.orbitos/rules/core/doc-promotion.md`。
10. 修改 OrbitOS 内核文件时，执行 `.orbitos/workflows/core-change.md`，并按 `.orbitos/schemas/core-change.schema.yaml` 校验。
11. 准备版本、changelog、commit 或 release 时，先读 `.orbitos/rules/core/versioning.md`。
12. 修改 Git 跟踪规则或创建新的生成内容区域时，先读 `.orbitos/rules/core/git-management.md`。
13. 内核变更在 commit/push 前必须通过 `python .orbitos/tests/test_runtime.py`。
14. 根 `AGENTS.md` 必须让新进入的 agent 可以直接行动：包含启动步骤、任务路由、停止条件和同步要求。
15. 根 `AGENTS.md` 不得变成长篇设计文档；详细行为放进链接到的 workflow 和 rule。

## 最小规则路由

- 不全量读取 `core/`；只加载当前变更命中的规则。
- 创建、修改或审查 MAP、README、AGENTS、STATUS、ROADMAP 等固定角色 Markdown 时，先读 `.orbitos/rules/core/document-semantics.md`。
- 写可见 Markdown 时再读 `markdown-writing.md`；修改根 README 时再读 `readme-writing.md`。
- 其他 Git、版本、workflow、命名和任务边界规则按下方索引与任务类型加载。

## 设计文档

OrbitOS 的人读设计文档由项目层入口管理，不属于 Product Repo 的固定内容。

需要设计上下文时：

1. 回到项目层 `03-项目/OrbitOS/AGENTS.md`。
2. 由项目层按需路由到本地 `docs/`。
3. Product Repo 只承载已经落地的规则、workflow、schema、脚本、测试和用户说明。

开发进度属于本地项目管理，不得混入产品设计文档：`ROADMAP.md` 管目标、完成条件和总体状态，`STATUS.md` 管详细现状、判断依据、最多 3 项当前任务和 3 项待确认决策；任务通过路线编号与 ROADMAP 对应。

## 核心规则

- `.orbitos/rules/core/README.md`：规则索引
- `.orbitos/rules/core/project-management.md`：项目目录、状态、路线与产品仓库公共规则
- `.orbitos/rules/core/document-semantics.md`：固定角色 Markdown 的全局职责边界
- `.orbitos/rules/core/markdown-writing.md`：可见 Markdown 编写规则
- `.orbitos/rules/core/readme-writing.md`：根 README 的受众、内容与链接规则
- `.orbitos/rules/core/doc-promotion.md`：内部设计如何转为用户系统说明
- `.orbitos/rules/core/git-management.md`：Git 边界、ignore 与跟踪文件清理
- `.orbitos/rules/core/versioning.md`：版本号、changelog 分层、commit 规则与 release 流程
- `.orbitos/rules/core/naming.md`：目录、文件、根目录顺序与 event 命名规则
- `.orbitos/rules/core/workflow-writing.md`：workflow 清单与审计规则
- `.orbitos/rules/core/task-boundary.md`：agent 默认任务范围与自检规则
- `.orbitos/rules/core/scheduled-task-boundary.md`：无人值守定时任务边界与投递规则

## 核心工作流

- `.orbitos/workflows/core-change.md`：修改 OrbitOS 内核文件时必须执行
- `.orbitos/workflows/startup-sync.md`：只读启动同步与未知 agent 拦截
- `.orbitos/workflows/agent-onboarding.md`：注册已确认新 agent
- `.orbitos/workflows/progress-sync.md`：把实质性工作编译成最小完成凭证并刷新必要视图
- `.orbitos/workflows/project-intake.md`：判断任务是否命中现有项目、是否应新建项目并建立最小项目入口
- `.orbitos/workflows/inbox-ingest.md`：将已确认收件箱输入移入已入库区
- `.orbitos/workflows/knowledge-draft.md`：将已入库输入转写为人读知识草稿
- `.orbitos/workflows/knowledge-conflict.md`：处理新证据与当前知识冲突时的候选草稿与确认流程
- `.orbitos/workflows/vault-audit.md`：审核收件箱入库内核
- `.orbitos/workflows/weekly-review.md`：以 event 为主源生成周回顾
- `.orbitos/workflows/agent-self-check.md`：整理单个 agent 的经验文件并收缩踩坑
- `.orbitos/workflows/learned-review.md`：低频巡检跨 agent 的公共经验层
- `.orbitos/workflows/experience-capture.md`：为 agent 自检提供经验分类逻辑
- `.orbitos/workflows/rule-evolution.md`：为 learned review 提供规则判断标准
- `.orbitos/workflows/hindsight-bridge.md`：Hindsight recall、retain、tag 与 event 审计试点

## 变更流程

1. 明确需求。
2. 检查现有设计文档和规则。
3. 进行范围受控的修改。
4. 使用 `.orbitos/scripts/write_event.py` 生成 event。
5. 按需更新人读视图。
6. 版本或 release 内容变化时，更新项目层 `03-项目/OrbitOS/CHANGELOG.md` 的完整版本历史。
7. `00-系统/07-系统变更.md` 只展示当前 release 摘要。
