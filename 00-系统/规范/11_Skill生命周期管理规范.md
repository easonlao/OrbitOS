# Skill 生命周期管理规范

> 当你或任何 Agent 需要对 OrbitOS 的 skill 进行增删改时，必须遵循本规范。

---

## 1. 新增 Skill

### 1.1 创建 SKILL.md

在 `00-系统/Skills/<skill-name>/SKILL.md` 创建文件，Frontmatter 必须包含：

```yaml
---
name: <skill-name>           # 小写+连字符，与目录名一致
description: >-               # 一句话说明：做什么+什么时候用
  <功能描述>。当用户说"<触发词1>"、"<触发词2>"时触发。
triggers:                     # 触发词列表（中英文）
  - <触发词1>
  - <触发词2>
---
```

**注意：** triggers 不能与已有 skill 冲突。检查 `workspace-tools.yaml` 中已有的 triggers。

### 1.2 注册到 workspace-tools.yaml

编辑 `.orbit/schema/workspace-tools.yaml`，在对应工作区下添加：

```yaml
# 如果绑定到特定工作区
"<工作区>":
  domain:
    <skill-name>:
      skill: <skill-name>
      triggers: [<触发词列表>]

# 如果是全局skill（任意位置可触发）
global_skills:
  <skill-name>:
    skill: <skill-name>
    triggers: [<触发词列表>]
```

### 1.3 添加 references（可选）

如果 skill 需要参考材料（persona、模板、脚本等），放在 `references/` 子目录：

```
00-系统/Skills/<skill-name>/
  ├── SKILL.md
  └── references/
      ├── personas/          # 领域专家 persona
      └── templates/         # 输出模板
```

### 1.4 验证清单

- [ ] SKILL.md 有完整的 Frontmatter（name + description + triggers）
- [ ] triggers 不与已有 skill 冲突
- [ ] 已在 workspace-tools.yaml 中注册
- [ ] SKILL.md 中引用的路径都存在（03-知识/、04-项目/ 等）
- [ ] 旧 OrbitOS 路径（00_收件箱、10_日记等）已替换为 thirdspace 路径（01-收件箱、02-日记等）
- [ ] 用 git commit 记录变更

---

## 2. 修改 Skill

### 2.1 可以改的

- SKILL.md 的内容（工作流、规则、边界条件）
- triggers（增删触发词）
- references 目录下的文件

### 2.2 不能随便改的

- **不要改 skill 的核心功能和用途** — 只优化"怎么写"和"怎么执行"，不改"做什么"
- **不要改 directory name** — 改了会导致 workspace-tools.yaml 注册失效
- **不要删除其他 skill 依赖的 references**

### 2.3 修改后的验证

- [ ] workspace-tools.yaml 中的注册仍然匹配
- [ ] SKILL.md 中引用的其他 skill 路径仍然正确
- [ ] triggers 仍然不冲突
- [ ] git commit 记录变更

---

## 3. 删除 Skill

### 3.1 步骤

1. 从 `workspace-tools.yaml` 中移除注册
2. 检查是否有其他 skill 引用它（grep 搜索）
3. 删除 `00-系统/Skills/<skill-name>/` 目录
4. git commit

### 3.2 注意

- 如果其他 skill 在 SKILL.md 中引用了被删 skill，必须同步更新引用
- persona references 如果是共享的，确认没有其他 skill 依赖

---

## 4. Persona 管理

### 4.1 位置

Persona 文件放在使用它的 skill 的 `references/personas/` 下：

```
00-系统/Skills/research/references/personas/     ← research 用
00-系统/Skills/kickoff/references/personas/      ← kickoff 用
00-系统/Skills/prd/references/personas/          ← prd 用
```

### 4.2 共享原则

多个 skill 共用同一套 persona 时，各自维护自己的副本。不要用 symlink——避免一个 skill 的修改影响另一个。

### 4.3 新增 Persona

1. 在对应 skill 的 `references/personas/` 下创建 `<领域>_<子领域>.md`
2. 更新 SKILL.md 中的 persona 匹配表
3. git commit

### 4.4 命名规范

`<领域>_<子领域>.md`，如：
- `Finance_Crypto.md`
- `SE_Architect.md`
- `Health_General.md`

---

## 5. Schema 修改

### 5.1 可修改的文件

| 文件 | 什么时候改 |
|------|-----------|
| `taxonomy.yaml` | 新增 type 或 topic 枚举值 |
| `subsystems.yaml` | 新增工作区、修改工作区约束 |
| `workspace-tools.yaml` | 新增/删除 skill 注册 |
| `managed-paths.yaml` | 新增或修改高价值子目录的特殊规则 |
| `event-capture.yaml` | 修改工作日志事件采集规则 |
| `event-log.yaml` | 修改 `.orbit/events/*.ndjson` raw event 字段规则 |
| `frontmatter.yaml` | 修改必填字段或枚举值 |

### 5.2 修改规则

- 每次只改一个文件
- 改完后检查 AGENTS.md 和 CLAUDE.md 是否引用了被改的路径
- 改完后检查所有 SKILL.md 中是否有引用被改的 schema

### 5.3 AGENTS.md 和 CLAUDE.md

这两个文件是 Agent 入口。如果修改了 schema 文件名或路径，必须同步更新这两个文件中的引用。

---

## 6. 路径规范

### 6.1 工作区路径（已确定，不要改）

| 路径 | 用途 |
|------|------|
| `00-系统/` | 规范、Skills、运行时 |
| `01-收件箱/` | 临时内容入口 |
| `02-日记/` | 工作日志、反思、复盘 |
| `03-知识/` | 知识卡片、研究笔记 |
| `04-项目/` | 项目文档、PRD |
| `05-资源/` | 参考资料、附件 |
| `06-输出/` | 可发布内容 |
| `99-归档/` | 已归档内容 |

### 6.2 禁止使用的旧路径

以下路径来自旧 OrbitOS，已废弃：

```
❌ 00_收件箱    → ✅ 01-收件箱
❌ 10_日记      → ✅ 02-日记
❌ 20_项目      → ✅ 04-项目
❌ 30_研究      → ✅ 03-知识（合并）
❌ 40_知识库    → ✅ 03-知识（合并）
❌ 50_资源      → ✅ 05-资源
❌ 90_计划      → ✅ 99-归档
❌ 99_系统      → ✅ 00-系统
```

### 6.3 环境变量

- 正确：`ORBIT_VAULT`
- 兼容但不推荐：`orbit_VAULT`
- 错误：`OrbitOS_VAULT`

---

## 7. Agent 适配流程

当新 Agent（Claude Code / Gemini CLI / Hermes 等）接入 vault 时：

### 7.1 必须做的

1. 创建 Agent 入口文件（如 `AGENTS.md` 或 `CLAUDE.md`）
2. 入口文件引用 `.orbit/workspace-index.yaml` 作为 vault 根锚点
3. 入口文件引用 `.orbit/schema/` 下的 5 个 schema 文件
4. 确认 Agent 能读取 `00-系统/Skills/` 下的 SKILL.md 文件

### 7.2 不需要做的

- 不需要复制 skill 到 Agent 的 skills 目录（除了 Hermes 的 `orbit-vault` 入口）
- 不需要修改 vault 内的任何文件
- 不需要注册 schema（Agent 通过入口文件自动发现）

### 7.3 Hermes 特殊配置

Hermes 需要在 `~/.hermes/skills/productivity/orbit-vault` 创建 symlink：
```bash
ln -s ~/orbit/00-系统/Skills/orbit-vault ~/.hermes/skills/productivity/orbit-vault
```
并在 `~/.hermes/.env` 中设置：`ORBIT_VAULT=/home/lyx/orbit`

---

## 8. Git 规范

### 8.1 分支

- `main` — 稳定版本
- `auto-optimize/*` — 自动优化分支
- `feature/*` — 新功能分支

### 8.2 Commit Message

```
<type>: <简短描述>

type:
  feat     — 新增 skill 或功能
  fix      — 修复 bug
  optimize — 优化现有 skill
  docs     — 文档变更
  refactor — 重构（不改功能）
```

### 8.3 .gitignore

用户内容（01-收件箱、02-日记、03-知识、04-项目、05-资源、06-输出、99-归档）不提交。框架文件（00-系统、.orbit、AGENTS.md 等）提交。

---

## 9. 快速参考：常见操作

| 操作 | 步骤 |
|------|------|
| 新增 skill | 创建 SKILL.md → 注册 workspace-tools.yaml → git commit |
| 修改 skill | 改 SKILL.md → 验证注册仍有效 → git commit |
| 删除 skill | 移除 workspace-tools.yaml 注册 → 检查引用 → 删除目录 → git commit |
| 新增 persona | 放到 skill 的 references/personas/ → 更新 SKILL.md 匹配表 → git commit |
| 新增触发词 | 改 SKILL.md 的 triggers + workspace-tools.yaml 的 triggers |
| 新增工作区 | 改 subsystems.yaml + workspace-index.yaml + 创建 WORKSPACE.md |
| 新增 type 枚举 | 改 taxonomy.yaml |
| Agent 接入 | 创建入口文件 → 引用 .orbit/ → 确认可读 Skills |
