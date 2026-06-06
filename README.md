# OrbitOS

> 一个 **AI 驱动**的个人知识库操作系统。用自然语言和 AI 聊天管理一切。

## 安装

```bash
git clone https://github.com/easonlao/OrbitOS.git my-vault
```

用 Obsidian 打开 `my-vault` 即可。

## 设计理念

- **Agent-native**：所有知识库操作由 AI Agent 驱动
- **自描述**：`.orbit/workspace-index.yaml` 即代表"这里是知识库"
- **路径无关**：任意目录 clone 均可直接使用

## 目录结构

```
.orbit/                   ← vault 根锚点 + schema 规范
00-系统/
  Skills/                 ← Agent Skill 定义
  规范/                   ← Frontmatter、工作区、路由等规范文档
  运行时/                 ← hooks 脚本模板
01-收件箱/                ← 所有未分类内容入口
02-日记/                  ← 工作日志、反思、复盘
03-知识/                  ← 知识卡片、主题笔记
04-项目/                  ← Roadmap、项目文档
05-资源/                  ← 图片、附件
06-输出/                  ← 对外发布内容
99-归档/                  ← 已归档内容
.obsidian/plugins/        ← OrbitOS Dashboard 插件
```

## 许可

MIT
