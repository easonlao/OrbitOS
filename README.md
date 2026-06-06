# OrbitOS

> 一个 **Agent-native** 的个人知识库操作系统。基于 ThirdSpace Vault 架构，为 HanaAgent 深度定制。

![Screenshot](05-资源/Screenshot.png)

## 安装

```bash
git clone https://github.com/easonlao/OrbitOS.git my-vault
```

用 Obsidian 打开 `my-vault`，在设置 → 第三方插件中启用 **OrbitOS Dashboard**。

---

## 设计理念

- **Agent-native**：所有知识库操作由 AI Agent 驱动，Skills 内置在 vault 内，零外部依赖
- **自描述**：`.orbit/workspace-index.yaml` 即代表"这里是知识库"，向上遍历自动定位
- **路径无关**：任何人 clone 到任意目录均可直接使用，零硬编码绝对路径
- **渐进式加载**：Skill 按场景按需加载，日常操作不浪费 token
- **结构化约束**：`.orbit/schema/` 定义 type 枚举、状态机、工作区流转规则，Agent 行为可校验

## 目录结构

```
.orbit/                   ← vault 根锚点 + schema 规范
00-系统/
  Skills/                 ← 全部 26 个 Skill 的 canonical 位置
  规范/                   ← 命名、Frontmatter、路由、审计规范
  运行时/                 ← hooks、crontab、自动化模板
01-收件箱/                ← 所有未分类内容的入口
02-日记/                  ← 工作日志、反思、复盘、人际事件
03-知识/                  ← 知识卡片、主题笔记、长期沉淀
04-项目/                  ← 项目文件，按意图分类（研究验证/产品系统/…）
05-资源/                  ← 图片、附件、参考资料
06-输出/                  ← 对外发布内容（文章、口播稿、脚本）
99-归档/                  ← 已归档内容
.obsidian/plugins/        ← OrbitOS Dashboard 插件
```

---

## Skill 体系

### 工作区 Skills（按场景自动加载）

| Skill | 工作区 | 职责 |
|-------|--------|------|
| `workspace-inbox` | 01-收件箱 | 网页剪藏、临时想法、待整理队列 |
| `workspace-journal` | 02-日记 | 工作日志、反思、复盘、人际事件 |
| `workspace-knowledge` | 03-知识 | 知识卡片、主题笔记、长期沉淀 |
| `workspace-projects` | 04-项目 | 项目分类、Roadmap、任务看板 |
| `workspace-resources` | 05-资源 | 参考资料、附件、素材管理 |
| `workspace-outputs` | 06-输出 | 文章、口播稿、脚本创作 |
| `workspace-archive` | 99-归档 | 归档管理、迁移 trace |
| `workspace-system` | 00-系统 | 规范、Schema、审计 |

### 领域 Skills（意图触发）

| Skill | 触发词 | 功能 |
|-------|--------|------|
| `start-my-day` | 开始一天、今日规划 | 扫描项目状态、收件箱，生成每日待办 |
| `kickoff` | 启动项目、kickoff | 收件箱想法 → 结构化项目 |
| `research` | 调研、深入研究 | 深度调研，提取原子概念到知识库 |
| `daotrace` | 道痕、道痕六层 | 六层自我反思（事实→第一反应→贪婪→恐惧→自洽→主石头） |
| `reflect` | 反思、复盘思考 | Mirror-Deepen-Bridge 三层反馈反思 |
| `worklog` | 工作日志、补充日志 | 创建/更新工作日志 |
| `review` | 周报、月报、复盘 | 扫描 vault 生成结构化周/月报告 |
| `knowledge` | 知识卡片、整理成知识 | 网页/视频内容 → 知识卡片 |
| `lifeos` | 人际事件、人物档案 | 人际互动记录和分析 |
| `brainstorm` | 头脑风暴 | 互动式想法打磨 |
| `ask` | 快问快答 | 直接回答，不生成笔记 |

### 内容筛选

| Skill | 功能 |
|-------|------|
| `ai-newsletters` | 筛选 AI 领域通讯 (TLDR AI, The Rundown AI 等) |
| `ai-products` | 发现 Product Hunt、HN、GitHub 上的 AI 新产品 |

### Obsidian 专属

| Skill | 功能 |
|-------|------|
| `obsidian-markdown` | 双向链接、Callout 块、嵌入等语法 |
| `obsidian-bases` | 过滤器和公式创建类数据库视图 |
| `json-canvas` | 可视化思维导图和流程图 |

### 系统

| Skill | 功能 |
|-------|------|
| `orbit-vault` | 核心路由 Skill，vault 解析、工作区路由 |
| `init-vault` | 新机器初始化：结构验证、Hook 安装、Skill 注册 |
| `help` | 显示所有可用命令 |

---

## 核心特性

### 结构化 Schema 约束

`.orbit/schema/` 下 5 个 YAML 文件定义了全部前端约束：

- `frontmatter.yaml` — 9 个必填字段和合法枚举值
- `taxonomy.yaml` — type/topic 可取值范围
- `subsystems.yaml` — 每个工作区的输入输出、类型约束、状态机
- `event-capture.yaml` — Agent 事件采集规则和 Hook 触发条件
- `workspace-tools.yaml` — 工作区到 Skill 的绑定映射

### OrbitOS Dashboard

Obsidian 侧边栏插件，提供工作区文件统计、活动热力图、Todos 管理、快捷操作面板。

### Git Hook

每次 `git commit` 自动记录到今日工作日志，保留完整的代码变更时间线。

---

## 设计哲学

1. **AI 是伙伴**：AI 不只是工具，而是理解你的系统、帮你维护它的协作者
2. **先记下来，再整理**：收件箱让你永不丢失灵感；准备好了再让 AI 处理
3. **连接比分类重要**：双向链接构建灵活可查的知识图谱
4. **每日节奏**：工作日志锚定一切，为工作和思考建立时间线
5. **渐进式结构化**：想法从粗糙开始，在 AI 辅助下逐步变得清晰有序

---

## 开源协议

MIT License
