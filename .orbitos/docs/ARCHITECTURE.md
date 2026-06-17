# OrbitOS 架构

## 1. 系统边界

OrbitOS 由一个 Git 管理的系统层和一个本地 runtime 数据层组成。

- 系统层：入口、规则、workflow、schema、脚本、eval、用户说明。
- Runtime 数据层：收件箱内容、时间线、项目、知识、Agent Profile、registry、event、queue、state。

Runtime 根目录本身是普通 Git clone。系统文件通过 `git pull` 更新，runtime mutable files 通过 `.gitignore` 保持本地。

## 2. 四个平面

### 2.1 证据平面

回答“依据是什么”和“实际发生了什么”。

- `01-收件箱/已入库/`：处理后保留的原始输入。
- `.orbitos/ingest/batches/`：原件处理状态与定位索引。
- `.orbitos/logs/events/`：操作事实账本。

原件是内容证据；event 是操作证据。两者不能互相替代。

### 2.2 认知平面

回答“当前最可信、已经确认的理解是什么”。

- `04-知识/00-草稿箱/`：agent 根据证据形成的待确认综合。
- `04-知识/{主题}/`：用户确认后的当前知识。

Active knowledge 只表示当前已经确认的版本。任何语义修改都必须先把文件移回 `04-知识/00-草稿箱/`，将 lifecycle 改为 `draft`，完成修改后重新等待用户确认；确认后才能回到正式主题目录并恢复 `active`。错字、格式和明确失效链接等不改变语义的维护可以直接处理。

知识不是原文副本，也不是 event 汇总。

### 2.3 控制平面

回答“agent 必须如何行动”。

- 根 `AGENTS.md`：唯一入口和路由。
- `.orbitos/rules/`：稳定约束。
- `.orbitos/workflows/`：执行步骤和异常分支。
- `.orbitos/schemas/`：机器写入对象结构。
- `.orbitos/scripts/` 与 `.orbitos/evals/`：自动检查。

当前 OrbitOS 不存在专属 Skills 层。未来 Skills 架构必须单独设计，不能从旧 Skills 继承隐含规则。

### 2.4 记忆平面

回答“哪些稳定信息需要跨会话快速召回”。

- Hindsight 是可选实现。
- 适合保存稳定环境事实、长期偏好、确认决策和复用型踩坑。
- 不保存全部 Markdown、普通进度或原始对话。
- recall 结果需要用证据平面或当前状态源复核。

## 3. 人读界面

Obsidian 是四个平面的用户界面，不是另一套事实源。

- `00-系统/`：用户需要理解的系统说明。
- `02-时间线/`：当前状态与时间视图。
- `03-项目/`：正在推进的对象及其状态源。
- `04-知识/`：当前确认理解。
- `05-资源/`：已识别、可引用的资料。
- `06-输出/`：Obsidian 内形成的正式 Markdown 产物。
- `99-归档/`：退出当前工作视野的完整对象。

时间线是聚合视图，不是操作事实账本；项目 STATUS 是项目当前状态源，不是历史日志。

## 4. 双通道编译

OrbitOS 不要求用户与 agent 的自然对话本身结构化。结构只在结果需要持久化时出现。

### 4.1 普通工作通道

```text
自然对话 -> 直接工作 -> 最小完成凭证 -> Validation -> 必要的人读投影
```

- agent 可以使用适合当前任务的方法工作。
- 实质性工作结束时，脚本把少量结果字段编译成 event。
- Validation 检查持久化结果，不审查或保存完整思考过程。

### 4.2 内容编译通道

```text
原始输入
  -> 01-收件箱
  -> triage：盘点、聚类、提出方向
  -> 用户确认处理
  -> 01-收件箱/已入库 + ingest batch
  -> knowledge draft：基于证据转写
  -> 04-知识/00-草稿箱
  -> 用户确认
  -> active knowledge
  -> 需要语义修改时回到知识草稿
```

整个过程中：

- 实质动作追加 event。
- 待确认事项投影到时间线。
- 项目变化先更新项目 STATUS，再投影到今日。
- 满足长期记忆条件时，可以选择性 retain 到 Hindsight。

## 5. Agent 生命周期

```text
Startup Sync -> Natural Work -> Result Compilation -> Validation
```

- Startup Sync 只读取状态，不推进任务。
- Natural Work 不要求固定话术或完整状态机。
- Result Compilation 通过 Progress Sync 把结果编译成最小 event，并刷新必要的人读视图。
- Validation 是完成门，只检查文件、对象和边界是否稳定。

Experience Capture、Rule Evolution 和 Hindsight Bridge 都是条件触发扩展，不是每次任务必须完整执行的串行管线。

## 6. 事实与状态优先级

| 问题 | 优先来源 |
|---|---|
| 原始内容是什么 | 已入库原件 |
| 某次操作发生了什么 | event |
| 项目现在做到哪里 | 项目 `STATUS.md` |
| 当前确认理解是什么 | active knowledge |
| 今天需要看什么 | `02-时间线/今日.md` |
| 跨会话稳定背景是什么 | Hindsight recall，随后复核本地来源 |

“事实底座”不能再被笼统理解为单一文件夹。不同问题有不同权威来源。

## 7. 核心与扩展

### 当前核心

- 普通 clone/runtime 更新边界。
- Agent 统一入口与同步闭环。
- 收件箱盘点、入库和审核。
- 知识草稿、确认和来源追溯。
- Event、Dashboard、项目 STATUS 的主从关系。

### 扩展路线

- 多 agent 并发与冲突处理。
- Hindsight 正式主 bank。
- Role Card。
- Thinking Mode Library。
- Skills 架构。
- 大范围知识 lint、矛盾检测和增量 Wiki 编译。
