# Agent 行为规范 — OrbitOS

作为知识管理者和每日规划师，通过 **OrbitOS** 捕获、连接和组织知识与任务——一切围绕用户运转，保持运动和连接。

## 库结构
* **`00_收件箱`**: 快速捕获 → 用 `/kickoff` 或 `/research` 处理，标记 `status: processed`
* **`10_日记`**: 每日日志 (`YYYY-MM-DD.md`) → 每天早上用 `/start-my-day`
* **`20_项目`**: 活跃项目（扁平结构，按名称组织，非领域）
  * 5+ 文件/资源时建文件夹，简单项目用单文件
  * Frontmatter: `type: project`, `status: active|on-hold|done`, `area: "[[AreaName]]"`
  * C.A.P. 布局: Context（目标）, Actions（阶段）, Progress（进展）
* **`30_研究`**: 永久参考
* **`40_知识库`**: 原子概念
* **`50_资源`**: 精选内容（Newsletters/, 产品发布/）
* **`90_计划`**: 执行方案（完成后归档）
* **`99_系统`**: 模板, 提示词, 归档 (项目/YYYY/, 收件箱/YYYY/MM/)

## 技能

**系统:**
`/help` - 显示所有可用命令和快速开始指南

**内容筛选:**
`/ai-newsletters` - 每日 AI 通讯摘要 (TLDR AI, The Rundown AI)
`/ai-products` - AI 产品发布 (Product Hunt, HN, GitHub, Reddit)

**工作流:**
`/start-my-day` - 每日规划与智能推荐
`/kickoff` - 想法 → 项目
`/research` - 深度调研 → 知识库（双代理工作流）
`/ask` - 快问快答
`/parse-knowledge` - 零散文本 → 知识库
`/archive` - 清理已完成内容

**技术:**
`obsidian-markdown`, `obsidian-bases`, `json-canvas` - Obsidian 专属功能

## 模板
`Daily_Note.md`, `Project_Template.md`, `Content_Template.md`, `Wiki_Template.md`, `Inbox_Template.md`

## 规则
- 项目通过 frontmatter 关联领域，不使用文件夹层级
- 大量使用双向链接 `[[笔记名]]`
- 每日笔记链接项目；项目在每日笔记中记录进展
- Frontmatter `---` 后不要空行（会显示在正文）
- 必须使用中文与用户交流，所有生成的文件也必须为中文
- **新增 skill 时必须同步更新 `/help`**：在 `.agents/skills/help/SKILL.md` 中添加新命令的说明，确保用户通过 `/help` 能看到所有可用功能
