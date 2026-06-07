---
name: orbit-vault
description: >-
  激活词：知识库。任何时候用户说"知识库"、"存进知识库"、"记到知识库"、"查知识库"、"整理知识库"，
  或涉及 OrbitOS vault 的操作（创建笔记、归类文件、工作区路由、Frontmatter 规范、审计结构），
  立即加载本 Skill。从任意目录工作，无需用户手动指定路径。
  Activation: any mention of "知识库", "OrbitOS", "vault", or knowledge-base operations.
triggers:
  - "知识库"
  - "存进知识库"
  - "记到知识库"
  - "查知识库"
  - "整理知识库"
  - "知识库里"
  - "维护知识库"
  - "初始化知识库"
  - "当前工作区"
  - "OrbitOS"
  - "vault"
---

# OrbitOS Vault Root Skill

## Agent-native Contract

用户不需要手动执行命令。Agent 触发本 Skill 后，应该直接调用 `scripts/orbit-vault.mjs` 完成检测、初始化、创建文件、更新 Frontmatter 和审计。

## 渐进式加载

1. 用 `resolve-vault --cwd "$PWD"` 定位 vault。
2. 读取 `{VAULT}/.orbit/workspace-index.yaml`。
3. 读取 `{VAULT}/.orbit/schema/taxonomy.yaml`。
4. 读取 `{VAULT}/.orbit/schema/subsystems.yaml`。
5. 读取 `{VAULT}/.orbit/schema/event-capture.yaml`。
6. 读取 `{VAULT}/.orbit/schema/managed-paths.yaml`。
7. 读取 `{VAULT}/.orbit/schema/workspace-tools.yaml`。
8. 先用 `explain-route` 根据用户意图、当前路径和 managed path 解释有效落点；如果当前 `pwd` 在 vault 内，再用 `pwd` 校准。
9. 读取 `<workspace>/WORKSPACE.md`。
10. 加载 workspace 对应子 Skill。
11. 只有意图命中时加载领域 Skill，例如 `lifeos`、`worklog`、`article`。
12. 执行文件创建、更新、标签、Frontmatter、流转、审计、修复和高价值事件记录。

## Script Interface

```bash
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs resolve-vault --cwd "$PWD"
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs locate-workspace --vault {VAULT} --cwd "$PWD"
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs explain-route --vault {VAULT} --cwd "$PWD" --intent "写一篇开发文档"
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs init --vault /path/to/new-vault
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs init --vault /path/to/new-vault --install-machine-runtime
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs create-routed-note --cwd "$PWD" --intent "写一篇开发文档" --title "项目部署流程" --dry-run
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs create-routed-note --cwd "$PWD" --intent "写一篇开发文档" --title "项目部署流程"
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs migrate-flux-intake --vault {VAULT} --dry-run
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs create --vault {VAULT} --workspace 03-知识 --subdir AI工程 --title "Agent工作流" --topic ai --type note
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs ensure-daily-worklog
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs record-agent-work-event --cwd "$PWD" --summary "完成重要产出" --decision "采用当前方案" --reason "更符合知识库自治目标"
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs register-hooks --repo "$PWD"
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs sync-runtime-templates --vault {VAULT}
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs install-machine-runtime --vault {VAULT} --all
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs update-frontmatter --file /path/to/file.md --topic ai --type note
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs audit-system --vault {VAULT}
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs audit-projects --vault {VAULT} --write-report
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs audit-workspaces --vault {VAULT} --write-report
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs audit-subsystems --vault {VAULT} --write-report
node {SKILLS}/orbit-vault/scripts/orbit-vault.mjs audit-skill-locations --vault {VAULT} --write-report
```

## Create File Policy

- Agent 必须优先用 `create` 创建新 Markdown。
- 当前工作区可由 `locate-workspace` 推断；目标落点用 `explain-route` 校验；不确定时写入 `01-收件箱/待整理`。
- `create` 会自动生成 `YYYYMMDD_主题.md` 和标准 Frontmatter。
- 更新旧文件 Frontmatter 时用 `update-frontmatter`，保留正文。

## 默认行为

- 不确定放哪里时，先放入 `01-收件箱/待整理/`。
- 不直接删除历史文件。
- 不直接批量迁移；先生成 queue 或 manifest。
- Prompt 能力统一转成 Skill，不写入全局 prompts 目录。
- 结构异常、缺失目录和深层嵌套用 `audit-workspaces` 检查。
- 子系统契约漂移、Skill 缺失、Frontmatter 缺失用 `audit-subsystems` 检查，并写入 `subsystem-maintenance.yaml`。
- 任意目录写入知识库时先 `resolve-vault`，再 `explain-route`，最后 `create-routed-note`。
- Git Hook 只记录 commit 级事实；Agent Hook 只记录重大产出、关键决策和理由。
- CLI 不是用户入口；旧 CLI 能力必须被包装成 Skill。
- 所有 Skill scripts 的 canonical 根目录是 `00-系统/Skills`；不得再把可维护脚本散落到 Workbase、`.codex/skills` 或项目子目录的 Skill 中。
- Hook、crontab 和 Agent 自动化规格必须在 `00-系统/运行时` 留存；跨电脑迁移时由 Agent 调用 `install-machine-runtime --all` 自动注册。


## Project Classification Policy

- `04-项目` 的分类以项目意图为准，不以历史来源为准。
- 发现项目分类不准时，先运行 `audit-projects`，输出建议路径、置信度和理由。
- `audit-projects` 不移动文件；跨分类移动必须由后续明确任务执行，并写 trace。
- 低置信度项目必须人工确认。

## 工作区映射

| 路径 | Skill |
|---|---|
| `00-系统` | `workspace-system` |
| `01-收件箱` | `workspace-inbox` |
| `02-日记` | `workspace-journal` |
| `03-知识` | `workspace-knowledge` |
| `04-项目` | `workspace-projects` |
| `05-资源` | `workspace-resources` |
| `06-输出` | `workspace-outputs` |
| `99-归档` | `workspace-archive` |

## 初始化

用户触发"初始化"/"setup"/"install"时，加载子 Skill：
`00-系统/Skills/init-vault/SKILL.md`

## Frontmatter 规范（必填 9 字段）

```yaml
---
title: "标题"
type: note              # 见 .orbit/schema/taxonomy.yaml
topic: work             # ai|dev|reading|work|project|tools|writing|life|system
workspace: "01-收件箱"  # 当前工作区目录名
created: "2026-05-26 10:00:00"
modified: "2026-05-26 10:00:00"
tags: ["note", "draft"]
source: manual          # mcp|manual|obsidian-clipper|web|import
status: draft           # draft|active|processed|archived
---
```
