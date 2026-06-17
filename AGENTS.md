# OrbitOS Agent 入口

OrbitOS 是一个多 agent 协作工作台。Obsidian 是人读界面，`.orbitos/` 是机器与运行时层。

本文件是所有 agent 使用 OrbitOS 的唯一入口契约，必须保持在 200 行以内。

## 1. 启动顺序

你进入 OrbitOS 后，只做三件事：

0. 先确认 `.orbitos/` 存在；如果缺失，立即停止并报告“工作副本不完整或未同步”，不要退回旧 `.orbit/`。
   如果 `.orbitos/agents/registry.yaml` 或 `02-时间线/今日.md` 缺失，先运行 `python .orbitos/scripts/init-runtime.py` 创建缺失的本地运行文件；该脚本不得覆盖已有内容。
1. 执行 Startup Sync。
2. 按任务选择一个工作流或规则。
3. 完成实质性工作后执行 Progress Sync。

如果你不确定该读什么，先读 `00-系统/00-开始使用.md`，再按本文件路由选择，不要全量扫描 vault。

## 2. 工作流入口

工作流负责“做事的过程”。收到任务后按最小匹配读取：

- 进入系统、同步当前状态：`.orbitos/workflows/startup-sync.md`
- 接入新 agent、登记部署信息：`.orbitos/workflows/agent-onboarding.md`
- 完成工作、同步进度、刷新状态：`.orbitos/workflows/progress-sync.md`
- 处理收件箱：`.orbitos/workflows/inbox-triage.md`
- 入库已确认的收件箱原始输入：`.orbitos/workflows/inbox-ingest.md`
- 将已入库原始输入转写为知识草稿：`.orbitos/workflows/knowledge-draft.md`
- 自检收件箱入库闭环：`.orbitos/workflows/vault-audit.md`
- 做本周回顾或周总结：`.orbitos/workflows/weekly-review.md`
- 记录对话内经验、踩坑、纠正或返工：`.orbitos/workflows/experience-capture.md`
- 提炼 agent 经验或规则候选：`.orbitos/workflows/rule-evolution.md`
- 使用 Hindsight recall / retain：`.orbitos/workflows/hindsight-bridge.md`
- 修改 OrbitOS 内核、schema、workflow、目录协议或系统规则：先读 `.orbitos/AGENTS.md`

## 3. 规则入口

规则负责“必须遵守的约束”。只有任务涉及时才读取：

- 写入可见 Markdown：`.orbitos/rules/core/markdown-writing.md`
- 修改 README：`.orbitos/rules/core/readme-writing.md`
- 修改 Git 边界、`.gitignore` 或清理跟踪文件：`.orbitos/rules/core/git-management.md`
- 准备版本、changelog、commit 或 release：`.orbitos/rules/core/versioning.md`
- 从内部设计提升到用户说明：`.orbitos/rules/core/doc-promotion.md`
- 编写或修改 workflow：`.orbitos/rules/core/workflow-writing.md`
- 创建或重命名目录、文件、event：`.orbitos/rules/core/naming.md`
- 判断任务范围、避免越界执行：`.orbitos/rules/core/task-boundary.md`
- 创建或审查定时任务：`.orbitos/rules/core/scheduled-task-boundary.md`

Hindsight 不是 OrbitOS 运行必需项。若使用 Hindsight，先 recall；如果 retain，必须在 event 中记录。

## 4. Startup Sync

开始任何工作前，先执行 Startup Sync：

0. 确认 `.orbitos/agents/registry.yaml` 存在；如果不存在，先运行 `python .orbitos/scripts/init-runtime.py`；仍不存在时停止并报告路径缺失，不读取其他 agent 的 profile。
1. 读取 `00-系统/00-开始使用.md`、`00-系统/06-术语表.md`、`00-系统/05-安全与边界.md`。
2. 读取 `.orbitos/agents/registry.yaml`，只读确认自己的 `agent_id` 和部署上下文；如果当前 agent 不在 registry 中，立即停止并请求用户确认注册信息。
3. 已注册时才读取自己的 `profile_ref`，查看经验记录、踩坑、待确认来源和 Learned Rule 使用记录。
4. 读取 `02-时间线/今日.md`、`02-时间线/待确认.md`、`02-时间线/下一步.md`。
5. 如果任务涉及具体项目，再读取目标项目的 `README.md` 和 `STATUS.md`。
6. 输出 5-8 行短状态摘要：当前状态、历史注意事项、待确认事项、下一步入口。

Startup Sync 只同步状态，不推进任务，不做决策。

如果当前 agent 不在 registry 中，立即停止；不要写 registry、不要创建 Agent Profile、不要写 event。先向用户确认 `agent_id`，再按单独注册流程处理。

新 agent 第一次接入时，建议用户这样描述：

```text
你现在接入 OrbitOS。请先阅读 AGENTS.md，执行 Startup Sync。
如果你还没有注册，不要写入任何文件；请先告诉我需要确认的 agent_id、部署位置、局域网 IP、接入方式和 OrbitOS 路径。
我确认后，再按 agent-onboarding workflow 注册。
```

如果读完 Startup Sync 仍不清楚下一步，只向用户输出当前状态、待确认、可继续入口，不要自行扩大任务范围。

## 5. 执行边界

只加载当前任务必需的最小上下文，使用渐进式披露：

- 写入可见 Markdown 前，先读取对应规则。
- 只有处理具体项目时，才读取项目文件。
- 只有修改 OrbitOS 内核时，才读取 `.orbitos/AGENTS.md`。
- 没有明确需要时，不全量扫描或重写整个 vault。
- 用户请求简短或模糊时，默认执行最小可逆动作；不要把短确认扩展成批量整理。
- 临时文件、外部仓库 clone、下载物和实验性输出不得创建在根目录；需要临时留存时放入 `01-收件箱/`，可丢弃的过程文件放在系统临时目录或 `.orbitos/tmp/`。

执行过程中如果遇到以下情况，先停下来问用户：

- 需要创建未知 agent 的 Agent Profile。
- 需要把候选内容提升为规则、ADR、知识卡片或正式产物。
- 需要移动、删除、归档用户内容。
- 需要改变 Git 跟踪边界。
- 关键必填字段缺失，无法通过 schema。
- 需要扩大到用户没有点名的目录、项目或内容类型。
- 需要让无人值守定时任务写入 OrbitOS 文件。

处理具体项目时，只读该项目的 `README.md`、`STATUS.md` 和明确相关文件。

行动前必须把当前 agent profile 中与本任务相关的经验、踩坑和待确认来源纳入执行约束。

## 6. Experience Capture

如果本次对话出现错误、返工、用户纠正、规则误读、validation 失败、明显有效做法，或用户说“记录经验/记录踩坑/这个以后注意”，先写入当前 agent profile。

经验捕获只记录可复用事实，不写长推理；是否进入 learned/core 规则池按 Rule Evolution 处理。

## 7. Progress Sync

完成实质性工作后，或用户说“同步”“同步进度”“更新进度”时，执行 Progress Sync。

Progress Sync 必须：

1. 至少在 `.orbitos/logs/events/` 写入一条 event。
2. 刷新相关人读视图，例如 `02-时间线/今日.md`、`待确认.md`、`下一步.md`。
3. 如果项目状态发生变化，更新项目 `STATUS.md`。
4. 对长期影响候选事项做记录，不静默提升为正式规则。
5. 在 event checklist 中记录任务边界自检：是否只改了目标范围、是否移动用户内容、是否创建正式产物、validation 是否通过。

Progress Sync 不会自动写 ADR，不会自动提升规则，不会自动创建知识卡片。

## 8. 固定规则

`.orbitos/logs/events/` 是事实底座。

可见 Markdown 是人读视图或产物，必须可读、聚焦、可追踪。

可见 Markdown 提到用户可能需要打开的现有可见 Markdown 文件时，必须使用 Obsidian 双链；内部 `.orbitos/` 文件仍用普通代码路径。

创建新目录或大量内容前，先判断它是公开系统材料、用户数据还是运行时状态。用户输入、资源、输出、归档、运行日志和本地工具状态默认不上传 Git。

可见 Markdown 默认需要 frontmatter；例外：`01-收件箱/00-粘贴.md` 是自由输入入口，不要求 frontmatter。

以下事项必须由用户确认：

- rule candidate
- ADR candidate
- formal artifact candidate，包括知识卡片

## 9. 输出风格

默认输出简短状态和结果：

- 做了什么
- 改了哪里
- 验证结果
- 还剩什么

不要把长推理、完整 event YAML、内部日志列表塞进人读 Markdown。

## 10. 开发边界

如果要修改 OrbitOS 内核、schema、workflow、目录协议或系统规则，先读取：

`.orbitos/AGENTS.md`
