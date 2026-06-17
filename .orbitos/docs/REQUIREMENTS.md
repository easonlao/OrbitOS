# OrbitOS 需求

## 1. 产品定位

OrbitOS 是一个以 Obsidian 为人读界面、支持多个 agent 协作的 Markdown 工作台。

它解决的不是“如何保存更多笔记”，而是：不同 agent 如何在同一套边界内工作、留下可追溯记录、把原始输入逐步编译成用户确认的知识与产物，并在后续会话中顺畅衔接。

## 2. 核心用户问题

- 与不同 agent 做过的工作容易散落，下一次接入时无法连续。
- 原始资料、过程状态、当前结论和长期知识混在一起，容易重复处理或产生幻觉。
- agent 如果没有统一入口、工作流和审核边界，会自行创建目录、改写内容或错误沉淀。
- 人需要在 Obsidian 中快速看懂今天发生了什么、需要确认什么、下一步是什么。
- 系统规则、项目状态、知识内容和机器日志需要各自有唯一职责。

## 3. 核心目标

### 3.1 协作连续性

- 所有 agent 从根 `AGENTS.md` 进入。
- agent 开始工作前执行 Startup Sync，完成实质工作后执行 Progress Sync。
- agent 能读取自己的部署信息、经验和踩坑，但不能读取或修改无关 agent 的档案。

### 3.2 内容编译闭环

OrbitOS 必须支持以下最小闭环：

```text
原始输入 -> 收件箱盘点 -> 已入库原件 -> 知识草稿 -> 用户确认 -> 当前知识
```

- 收件箱只是临时入口，不是永久原始资料库。
- 已入库原件保留原始内容，不因知识转写而被覆盖。
- 新知识卡片和核心结论变化必须经过用户确认。
- Active knowledge 发生语义修改前必须移回 `04-知识/00-草稿箱/`，重新进入 draft -> confirmation -> active 流程。
- 错字、格式和失效链接等非语义维护可以自动处理，但必须保持可追溯。

### 3.3 状态可见

- `02-时间线/今日.md` 是用户每日入口。
- 项目 `STATUS.md` 是项目当前状态源，今日只投影当天变化。
- 用户不需要阅读 `.orbitos/` 才能知道当前状态。

### 3.4 可追溯性

- `.orbitos/logs/events/` 记录操作事实：谁、何时、因为什么、做了什么、结果是什么。
- ingest batch 记录原件是否已处理及其状态。
- 知识正文保留来源链接，使当前结论可以回到原始证据。

### 3.5 普通 clone 使用

- OrbitOS runtime 本身必须像普通用户 clone 一样通过 Git 更新。
- 系统文件由 Git 跟踪；用户数据和 mutable runtime files 不进入 Git。
- `git pull` 不应覆盖收件箱、时间线、项目、知识、Agent Profile、registry、event、queue 或 state。

## 4. 人读要求

- Obsidian 是阅读、确认和回看的主要界面。
- 可见 Markdown 必须单一职责、简洁、可跳转。
- 用户需要打开的现有可见文件使用 Obsidian 双链。
- 内部 `.orbitos/` 路径使用普通代码路径，避免误建空白笔记。
- 知识宁少不多，不能把普通对话、任务流水或未经确认的推测直接变成知识卡片。

## 5. Agent 执行要求

- 根 `AGENTS.md` 不超过 200 行，并采用渐进式披露。
- 只有任务涉及时才加载对应 rule 或 workflow。
- 关键字段缺失、需要移动用户内容、改变 Git 边界或创建正式产物时必须停止并请求确认。
- 写入型 workflow 必须通过 validation；失败时不得刷新人读视图。

## 6. Hindsight 要求

- Hindsight 是可选的跨会话长期记忆增强，不是 OrbitOS 的事实底座。
- 不使用 Hindsight 时，OrbitOS 的核心流程仍必须完整运行。
- Hindsight 只接收稳定、可复用、经确认或工具验证的信息。
- 普通任务流水、Dashboard 摘要、临时命令输出和完整对话不得自动 retain。
- OrbitOS 不要求把所有 Markdown 知识复制到 Hindsight。

## 7. 当前非目标

以下能力属于整体路线，但不是当前最小内核任务：

- Role Card。
- Thinking Mode Library。
- OrbitOS 专属 Skills 架构。
- 自动把知识转成 rule 或 skill。
- 自动重写大量知识页面的全库 Wiki 编译器。
- 将数据库、向量索引或 Hindsight 设为必需依赖。

## 8. 验收标准

- 新用户 clone 后可以初始化 runtime，并通过 validation。
- 新 agent 只读 `AGENTS.md` 和被路由的最小文档即可进入正确状态。
- 原始输入不会被知识转写覆盖，已处理状态可检查。
- 未经用户确认不能产生 active knowledge 或正式产物。
- 用户打开今日、待确认和项目 STATUS 能理解当前状态。
- agent 能区分内容证据、操作事实、当前知识、人读视图和长期记忆。
