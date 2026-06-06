# OrbitOS

> 一个 **AI 驱动**的个人知识库操作系统。用自然语言和 AI 聊天管理一切。

![Screenshot](05-资源/Screenshot.png)

## 安装

```bash
git clone https://github.com/easonlao/OrbitOS.git my-vault
```

用 Obsidian 打开 `my-vault`，在设置中启用 **OrbitOS Dashboard** 插件。

---

## 设计理念

- **Agent-native**：所有知识库操作由 AI Agent 驱动，无需手动维护
- **自描述**：`.orbit/workspace-index.yaml` 即代表"这里是知识库"，零外部配置
- **路径无关**：任意目录 clone 均可直接使用
- **渐进式加载**：Skill 按需加载，不浪费 token

## 目录结构

```
.orbit/                   ← vault 根锚点 + schema 规范
00-系统/
  Skills/                 ← Agent Skill 定义（26 个）
  规范/                   ← Frontmatter、工作区、路由等规范文档
  运行时/                 ← hooks 脚本模板
01-收件箱/                ← 所有未分类内容入口
02-日记/                  ← 工作日志、反思、复盘、人际事件
03-知识/                  ← 知识卡片、主题笔记、长期沉淀
04-项目/                  ← Roadmap、项目文档、任务看板
05-资源/                  ← 图片、附件、参考资料
06-输出/                  ← 对外发布内容
99-归档/                  ← 已归档内容
.obsidian/plugins/        ← OrbitOS Dashboard 插件
```

---

## 核心特性

### AI 驱动的工作流

| 命令 | 用途 |
| :--- | :--- |
| `/start-my-day` | 回顾昨日进展，扫描项目状态，生成今日待办 |
| `/kickoff` | 把收件箱里的想法变成结构化项目 |
| `/research` | 深度调研，整理成结构化笔记，提取核心概念 |
| `/ask` | 快问快答，不生成笔记 |
| `/brainstorm` | 互动式头脑风暴 |
| `/help` | 显示所有可用命令 |

### 内容筛选

| 命令 | 用途 |
| :--- | :--- |
| `/ai-newsletters` | 筛选 AI 领域通讯 (TLDR AI, The Rundown AI 等) |
| `/ai-products` | 发现 Product Hunt、HN、GitHub 上的 AI 新产品 |

### Obsidian 专属

| 技能 | 用途 |
| :--- | :--- |
| `obsidian-markdown` | 双向链接、Callout 块、嵌入等 Obsidian 特有语法 |
| `obsidian-bases` | 过滤器和公式创建类数据库视图 (.base 文件) |
| `json-canvas` | 可视化思维导图和流程图 (.canvas 文件) |

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
