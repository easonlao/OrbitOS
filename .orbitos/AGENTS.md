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
- `.orbitos/docs/`、`.orbitos/rules/` 与 `00-系统/` 之间的内容提升
- 版本、changelog、commit 或 release 规则
- Git ignore、仓库边界或已跟踪文件清理规则
- `.orbitos/` 内部内容

## 开发规则

1. 根 `AGENTS.md` 必须保持为唯一使用入口。
2. 面向用户的系统说明放在 `00-系统/`。
3. 稳定的 agent 执行规则放在 `.orbitos/rules/core/`。
4. 实现、schema、workflow 和设计文档放在 `.orbitos/`。
5. 已确认的当前版本系统变化记录在 `00-系统/07-系统变更.md`。
6. 只有重大且难以回退的架构决策才使用 ADR。
7. 未经用户明确确认，不得把讨论或脑暴直接提升为规则。
8. 修改根 README 前，先读 `.orbitos/rules/core/readme-writing.md`。
9. 将设计内容提升到 `00-系统/` 前，先读 `.orbitos/rules/core/doc-promotion.md`。
10. 修改 OrbitOS 内核文件时，执行 `.orbitos/workflows/core-change.md`，并按 `.orbitos/schemas/core-change.schema.yaml` 校验。
11. 准备版本、changelog、commit 或 release 时，先读 `.orbitos/rules/core/versioning.md`。
12. 修改 Git 跟踪规则或创建新的生成内容区域时，先读 `.orbitos/rules/core/git-management.md`。
13. 内核变更在 commit/push 前必须通过 `python .orbitos/tests/test_runtime.py`。
14. 根 `AGENTS.md` 必须让新进入的 agent 可以直接行动：包含启动步骤、任务路由、停止条件和同步要求。
15. 根 `AGENTS.md` 不得变成长篇设计文档；详细行为放进链接到的 workflow 和 rule。

## 设计文档

- `.orbitos/docs/README.md`：开发文档边界
- `.orbitos/docs/REQUIREMENTS.md`：已确认需求与约束
- `.orbitos/docs/ARCHITECTURE.md`：系统分层与对象模型
- `.orbitos/docs/DESIGN.md`：具体目录与文档设计
- `.orbitos/docs/RUNTIME.md`：agent 最小运行环境约定

开发进度属于本地项目管理，不得混入产品设计文档：`ROADMAP.md` 管里程碑，`TASKS.md` 管当前可执行任务，`STATUS.md` 管当前进度，`OPEN-QUESTIONS.md` 管未确认决策。

## 核心规则

- `.orbitos/rules/core/README.md`：规则索引
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
- `.orbitos/workflows/inbox-ingest.md`：将已确认收件箱输入移入已入库区
- `.orbitos/workflows/knowledge-draft.md`：将已入库输入转写为人读知识草稿
- `.orbitos/workflows/vault-audit.md`：审核收件箱入库内核
- `.orbitos/workflows/weekly-review.md`：以 event 为主源生成周回顾
- `.orbitos/workflows/experience-capture.md`：在规则演进前记录 agent 经验与踩坑
- `.orbitos/workflows/rule-evolution.md`：把 agent 经验提炼为 learned/core 规则
- `.orbitos/workflows/hindsight-bridge.md`：Hindsight recall、retain、tag 与 event 审计试点

## 变更流程

1. 明确需求。
2. 检查现有设计文档和规则。
3. 进行范围受控的修改。
4. 使用 `.orbitos/scripts/write_event.py` 生成 event。
5. 按需更新人读视图。
6. 版本或 release 内容变化时，更新 `.orbitos/CHANGELOG.md` 的完整版本历史。
7. `00-系统/07-系统变更.md` 只展示当前 release 摘要。
