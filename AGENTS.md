# OrbitOS Agent 入口

## 读取顺序

0. 如果当前目录不在知识库内，向上遍历父目录直到找到 `.orbit/workspace-index.yaml`，该目录即为 vault 根。
1. 读取 `.orbit/workspace-index.yaml`，先根据用户意图判断目标工作区；如果当前 `pwd` 在 vault 内，再把 `pwd` 作为辅助信号校准。
2. 读取 `.orbit/schema/taxonomy.yaml`，确认当前工作区允许的 type/topic 枚举。
3. 读取 `.orbit/schema/subsystems.yaml`，确认当前工作区的自治子系统契约。
4. 读取 `.orbit/schema/event-capture.yaml`，确认全局路由和 Hook 事件采集规则。
5. 读取 `.orbit/schema/event-log.yaml`，确认 raw event log 字段规则。
6. 读取 `.orbit/schema/managed-paths.yaml`，确认高价值子目录的特殊规则。
7. 读取 `.orbit/schema/workspace-tools.yaml`，确认当前工作区可用工具 Skill 和领域 Skill。
8. 读取当前工作区的 `WORKSPACE.md`。
9. 按 `workspace-index.yaml` 中的 `skill` 加载对应子 Skill。
10. 仅在意图命中时加载领域 Skill。
11. 创建、更新或整理文件前，检查 `.orbit/schema/`，并用 `explain-route` 确认有效 workspace、managed path、type、topic、status 和目标目录。

## 全局规则

- 新 Markdown 文件默认使用 `YYYYMMDD_主题.md`。
- 每个 Markdown 文件必须有 Frontmatter（9 字段：title, type, topic, workspace, created, modified, tags, source, status）。
- `workspace` 字段必须等于当前工作区目录名。
- 不确定归属时，写入 `01-收件箱/待整理/`。
- 不直接批量删除历史内容。
- 大规模迁移先写入 `.orbit/manifests/`。
- 每个工作区都是自治子系统，必须遵守输入、输出、状态、审计和修复边界。
- 任意目录触发知识库操作时，先 resolve vault，再用 `explain-route` 校验落点，最后按意图 `create-routed-note`。
- 写入文件前必须同时确认 workspace 与 managed path；不命中 managed path 时继承当前 `WORKSPACE.md`。

## 生命周期管理

**新增、修改、删除 Skill 或 Schema 时，必须先读取 `00-系统/规范/11_Skill生命周期管理规范.md`，按规范操作。** 该规范定义了：
- Skill 的创建、注册、修改、删除流程
- Persona 的管理和命名规范
- Schema 文件的修改规则
- 路径规范（禁止使用的旧路径）
- Agent 接入流程
- Git 提交规范

## 工作区切换

当前目录只在位于 vault 内时辅助决定工作状态；外部目录触发知识库操作时，以用户意图和工作区规范为准：

- `00-系统`：规范、Schema、Skills、Agent、审计。
- `01-收件箱`：接收、粗分、生成整理队列。
- `02-日记`：记录、反思、复盘。
- `03-知识`：沉淀知识卡片和主题笔记。
- `04-项目`：推进项目，项目内可有局部 `AGENTS.md` 或 `CLAUDE.md`。
- `05-资源`：保存长期参考资料和附件。
- `06-输出`：维护可发布成品。
- `99-归档`：保存迁移记录、废弃系统、废弃工具、完结项目和非活跃内容。
