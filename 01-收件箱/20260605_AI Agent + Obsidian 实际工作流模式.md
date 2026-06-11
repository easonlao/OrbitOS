---

title: "AI Agent + Obsidian 实际工作流模式"
type: card
topic: ai
workspace: "03-知识"
created: "2026-06-05"
modified: "2026-06-06 21:06:03"
tags: ["AI", "Obsidian", "workflow", "automation", "agent", "PKM"]
source: manual
status: active
---


# AI Agent + Obsidian 实际工作流模式

## 1. 内存衰减模型（Maksym Prokopov）

用原子化事实替代长篇笔记，每个事实附带元数据驱动记忆优先级：

```json
{
  "fact": "用户偏好燕麦奶美式",
  "learnedAt": "2026-01-15",
  "lastAccessed": "2026-02-08",
  "source": "daily-note"
}
```

**衰减规则：**
- **Hot**（<7天）：出现在每日摘要，高优先级
- **Warm**（8-30天）：在摘要中但权重降低
- **Cold**（30+天）：仅可搜索，不在工作上下文中

AI 每周运行一次任务：重算热度、重新生成摘要。保持上下文新鲜，无需人工策展。

**关键洞察：** 在已有习惯上构建新工作流。用户每天刷 Telegram 几十次，那就把 Telegram 当输入端，而不是强迫自己打开 Obsidian。

## 2. Vault Agent 技能体系（obsidian-vault-agent）

### 核心处理管道

```
inbox → processing → processed → evergreen
```

### 三种关键认知技能

| 技能 | 机制 | 原理 |
|------|------|------|
| `/process` | 先问检索问题，再展示内容 | 生成效应（generation effect）：从记忆写比抄写更有效 |
| `/recall` | 跨领域交错检索 | 间隔交错（interleaving）：ML + 心理学 + 金融混在一起问 |
| `/synthesize` | 耗尽 vault 知识，暴露矛盾 | 强迫抽象化，用自己证据锚定不舒服的问题 |

### 笔记类型体系

`(Term)`, `(Paper)`, `(Post)`, `(Book)`, `(Thought)`, `(Course)` 等，每种有专用模板和处理流程。

## 3. 多 Agent 区域治理（Multi-Agent Vault）

### 问题：多个 Agent 共享一个 Vault 时的五大挑战
1. Agent 盲视彼此
2. 写入冲突
3. 索引漂移
4. 无新鲜度信号
5. 无协调机制

### 解决方案：分区写入 + 协调层

```
BotVault/
├── 01_knowledge/notes/    ← 主 Agent 写入（系统知识、偏好）
├── 07_shared/notes/       ← 协调区（主 Agent 创建，其他追加）
├── 08_work/notes/         ← 工作 Agent 写入（技术笔记）
└── 06_system/scripts/     ← 自动化脚本
```

**所有 Agent 可读整个 Vault，写入严格分区。**

### 新鲜度元数据

```yaml
last-reviewed: 2026-02-19
confidence: high|medium|low
```

### 知识晋升管道

技术发现在工作区经过 14 天 `confidence: high` 后，被标记为晋升候选。主 Agent 审查后决定：晋升到知识区（全员需要）、晋升到协调区（有协调价值）、或留在工作区。

**核心原则：知识靠自身价值赢得位置。**

### 自动化脚本

| 脚本 | 功能 |
|------|------|
| `generate-vault-index.sh` | 自动生成索引，永远不手动编辑 |
| `stale-notes-report.sh` | 标记 30+ 天未审查的笔记 |
| `validate-vault-index.sh` | 验证索引与实际文件一致 |
| `session-briefing.sh` | 为每个 Agent 生成个性化阅读清单 |

## 对 OrbitOS 的参考价值

| 模式 | OrbitOS 可借鉴 |
|------|----------------|
| 内存衰减 | 知识库条目可用 frontmatter 的 `last-reviewed` + `confidence` 跟踪新鲜度 |
| 处理管道 | 收件箱 → 处理中 → 已处理 → 常青笔记，与现有收件箱流程对齐 |
| 区域治理 | Nova-activity（Nova 独立活动）、共享知识库、项目区的写入权限可以明确 |
| 晋升管道 | 已验证的知识从项目笔记晋升到知识库 |
| 检索先行 | `/process` 的"先回忆再看"模式可用于学习类技能 |
