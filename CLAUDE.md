# OrbitOS Claude Code 入口

当 Claude Code 在 vault 根目录（含 .orbit/workspace-index.yaml 的目录）打开时，按顺序读取：

1. `./00-系统/Skills/orbit-vault/SKILL.md`（核心路由 Skill）
2. .orbit/workspace-index.yaml（工作区索引）
3. .orbit/schema/taxonomy.yaml（type/topic 枚举）
4. .orbit/schema/subsystems.yaml（工作区契约）
5. .orbit/schema/managed-paths.yaml（高价值子目录规则）
6. .orbit/schema/event-capture.yaml（Agent 事件采集规格）
7. .orbit/schema/event-log.yaml（raw event log 字段规则）
8. .orbit/schema/workspace-tools.yaml（工作区→Skill 绑定）
9. 当前工作区 WORKSPACE.md
10. 仅在意图命中时加载领域 Skill

## 渐进式加载

日常操作不预载所有 Skill。需要操作某个工作区时，先读取对应 workspace-* Skill，再按意图加载领域 Skill。

## 生命周期管理

**新增、修改、删除 Skill 或 Schema 时，必须先读取 `00-系统/规范/11_Skill生命周期管理规范.md`，按规范操作。**

## 初始化（新机器）

告诉 Agent：帮我初始化这个知识库

Agent 读取 init-vault Skill 后自动完成：
1. 结构验证（.orbit/schema/ 完整性）
2. Git Hook 安装（可选）
3. 定时任务注册（可选）
4. Skill 全局注册（~/.claude/skills/orbit-vault 软链）
5. Obsidian 插件启用提示
