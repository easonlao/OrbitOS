---
title: Project Intake Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-07-06
updated: 2026-07-06
tags:
  - orbitos
  - workflow
  - project
  - intake
---

# Project Intake Workflow

Project Intake 用于在普通项目推进前，先判断一项任务是否已经属于某个现有项目、是否应新建项目，以及如何建立最小项目入口。代码型项目建立最小入口后，只有 Engineering 模块为 `ready` 才继续进入 `.orbitos/modules/engineering/workflows/code-project.md`。

它不是项目推进本身，也不是 repo 初始化流程。它只负责把“项目还不存在时怎么办”这一段前置链路收口。

## 触发条件

- 用户带来一项需要长期推进的新任务，但没有点名现有项目。
- Agent 识别到任务看起来与项目相关，但当前没有合适的 `03-项目/{project}/` 可直接落位。
- 用户明确说“新建一个项目”“这个需要单独立项”“先看看要不要建项目”。

## 前置确认

开始写入前，至少先确认：

- 现有项目里是否已有合适归属。
- 这项任务是否真的需要跨会话持续推进，而不是一次性处理。
- 是否需要独立的项目状态源。
- 是否需要 `repo/`；只有代码型项目才创建。

如果结论是“需要新建项目”，属于扩大范围动作，必须先向用户说明理由并得到确认。

## 输入

- 用户任务、自然语言要求或收件箱线索。
- `03-项目/` 现有项目目录列表。
- 根 `AGENTS.md`。
- `.orbitos/rules/core/project-management.md`。
- 如任务已明显命中某个项目，再读取该项目 `AGENTS.md` 与 `STATUS.md`。

## 输出

- 挂接到现有项目，或
- 新建最小项目入口：
  - `03-项目/{project}/AGENTS.md`
  - `03-项目/{project}/STATUS.md`
  - `03-项目/{project}/docs/`
  - `03-项目/{project}/repo/`（仅代码型项目）
- `.orbitos/logs/events/*.yaml`
- 必要时同步 `02-时间线/今日.md`

## 执行流程

1. 先读取 `.orbitos/rules/core/project-management.md`。
2. 列出 `03-项目/` 的直属项目目录，不做全量深扫。
3. 判断任务属于以下哪一类：
   - 已有项目可承接
   - 暂时不应项目化
   - 需要新建项目
4. 如果命中已有项目：
   - 进入该项目 `AGENTS.md` 和 `STATUS.md`
   - 如果项目根下存在 `repo/` 且 Engineering 模块为 `ready`，进入 `.orbitos/modules/engineering/workflows/code-project.md`；否则保留项目层入口并报告工程模块未就绪
5. 如果暂时不应项目化：
   - 保持在当前区域处理
   - 不创建项目目录或项目状态
6. 如果需要新建项目：
   - 先向用户说明为什么现有项目都不合适
   - 说明是否需要 `repo/`
   - 用户确认后再创建最小项目入口
7. 创建最小入口时：
   - `AGENTS.md` 优先复用 `.orbitos/templates/03-项目/AGENTS-TEMPLATE.md`
   - `STATUS.md` 优先复用 `.orbitos/templates/03-项目/STATUS-TEMPLATE.md`
   - 创建后必须替换 `{PROJECT_NAME}`、`{DATE}` 和 `待补充` 等占位内容，再把文件作为项目入口。
   - `docs/` 先只建立目录，不自动填充平级设计稿
   - `repo/` 仅在代码型项目时创建
8. 初始化完成后，再进入普通项目流；不得跳过项目入口直接进入 `repo/`。
9. 执行 `validate-sync.md`。
10. 通过后写 event，并在需要时把“新项目已建立”或“项目已挂接”投影到今日。

## 最小入口模板

新建项目时优先复用以下模板：

```text
.orbitos/templates/03-项目/AGENTS-TEMPLATE.md
.orbitos/templates/03-项目/STATUS-TEMPLATE.md
```

模板只负责建立薄入口与最小状态源，不替代后续项目自己的设计文档。

## 执行清单

### 进入检查

- [ ] 已确认这次问题属于“项目接入”而不是普通项目推进。
- [ ] 已先列出 `03-项目/` 的直属项目，再判断是否命中现有项目。
- [ ] 已读取 `project-management.md`。

### 执行检查

- [ ] 已区分“已有项目 / 不应项目化 / 新建项目”三种情况。
- [ ] 若需新建项目，已先得到用户确认。
- [ ] 已按模板建立最小入口。
- [ ] 仅在代码型项目场景创建 `repo/`。
- [ ] 代码型项目在 Engineering 模块为 `ready` 时已进入 `.orbitos/modules/engineering/workflows/code-project.md`，未直接跳进仓库执行开发任务。

### 退出检查

- [ ] 已运行 validation。
- [ ] 已写 event。
- [ ] 若建立了新项目，已给出从哪个入口继续。

## 禁止

- 不得因为任务看起来重要就自动立项。
- 不得跳过项目层入口直接创建 `repo/` 并开始工作。
- 不得为非代码型项目默认创建 `repo/`。
- 不得在未确认前批量扫描整个项目区深层目录。
- 不得在初始化阶段自动生成大量设计稿、README 或路线文档。
