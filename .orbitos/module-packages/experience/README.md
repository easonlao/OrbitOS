---
title: Experience Module
area: internal
purpose: guide
lifecycle: active
created: 2026-08-09
updated: 2026-08-09
tags:
  - orbitos
  - experience
  - module
---

# Experience Module

Experience 模块承载每个 OrbitOS Agent 的**个体学习沉淀**：做完实质工作后，把验证过的做法、踩过的坑、返工教训写进自己的 `00-系统/agents/{agent_id}-experience.md`，供自己和后续会话查阅。

## 与相邻概念的边界（为什么它独立存在）

- **与 learned-rule 无关**：本模块只做沉淀与查阅。经验**不会自动升级为规则**。一条经验要进入规则池，必须走显式路径：用户确认 → 写入 `core rules` 或产品文档。历史背景见 ADR-0008（experience 机制 2026-06-12 构建 → 7-13 因归类偏差被误删 → 本模块化接回）。
- **与工程技能互补而非替代**：Matt Pocock skill 体系（to-issues / triage / code-review，见 `engineering/workflows/code-project.md`）解决的是**项目管理维度**——拆 issue、交付、验收。Experience 解决的是**个体学习维度**——做完事记住什么。两者零重叠。
- **与 Hindsight 的区分**：Hindsight 做跨会话记忆召回/保留（`modules/hindsight/`）；Experience 是 agent 自己管理的人读 markdown 记录，不依赖任何记忆服务。

## 何时使用

- 完成会改变文件或长期状态的实质性工作后（配合 `progress-sync.md` 的自检步骤）。
- 踩坑、返工、用户纠正后——这些是最有价值的经验来源。
- 新会话开始需要回顾自己积累时，读取本 agent 的 `*-experience.md`。

## 模块内容

- `workflows/experience-capture.md`：写入触发、条目格式、追加流程。
- `rules/experience-record.md`：记录边界（什么该记/不该记）、隐私、显式升级路径。
- `templates/experience-entry.md`：条目模板。

## 存量数据

现有 agent 的 `00-系统/agents/*-experience.md`（codex / hermes / mimo / nova / workbuddy）是模块的存量数据，直接保留，不迁移。
