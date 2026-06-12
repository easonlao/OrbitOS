# OrbitOS

> 一个 Markdown 原生的人机协作工作台，用来协调人、agents、记忆系统和 Obsidian 可读产物。

中文 | [English](README.md)

OrbitOS 是一个 Obsidian-first 的人机协作工作台。

它的核心想法很简单：你在 Obsidian 里阅读和确认，agent 负责维护状态、整理原始输入、记录可追踪的工作痕迹，并把确认后的内容推进到项目、知识、资源或输出。

## OrbitOS 是什么

OrbitOS 不是传统个人知识库，也不只是 agent 框架说明书。它连接的是：

- Obsidian：人的阅读、确认和回看界面
- `AGENTS.md`：所有 agent 进入 OrbitOS 的统一入口
- `00-系统/`：用户需要理解的系统说明书
- `.orbitos/`：schema、日志、队列、workflow、设计文档等内部运行层

## 最快开始

1. 下载或克隆这个仓库：

```powershell
git clone https://github.com/easonlao/OrbitOS.git
```

2. 在 Obsidian 里把克隆下来的 `OrbitOS` 文件夹打开为一个 vault。
3. 把你想丢进系统的东西复制到 `01-收件箱/`。
4. 和 agent 聊天，让它从入口开始：

```text
请读取 AGENTS.md，执行 Startup Sync，然后告诉我当前 OrbitOS 状态。
```

你每天主要看：

- [[02-时间线/今日|今日 Dashboard]]

需要你判断的事情看：

- [[02-时间线/待确认|待确认]]

想继续推进什么看：

- [[02-时间线/下一步|下一步]]

## 日常怎么用

OrbitOS 的用户路径应该尽量短：

```text
把材料丢进 01-收件箱/
  -> 和 agent 聊天
  -> 看 今日.md / 待确认.md
  -> 确认后的内容进入项目、知识、资源或输出
```

收件箱保持低摩擦。agent 可以盘点、摘要、提出去向建议，但长期知识和正式产物必须经过确认。

## 仓库结构

```text
AGENTS.md              # agent 使用入口
README.md              # GitHub 英文项目说明
README.zh-CN.md        # GitHub 中文项目说明
00-系统/               # 人读的运行规则和系统说明
01-收件箱/             # 低摩擦原始输入
02-时间线/             # 用户 Dashboard 和展开状态视图
03-项目/               # 项目边界层
04-知识/               # 已确认、可复用的知识
05-资源/               # 已处理的参考资料和附件
06-输出/               # Obsidian 内产出的 Markdown 成品
99-归档/               # 退出当前使用的对象
.orbitos/              # 运行时层：schema、日志、队列、workflow、设计文档
```

## 系统说明书

`00-系统/` 是 OrbitOS 用户需要理解的系统说明书：

- [[00-系统/MAP|系统地图]]：当前有哪些系统文档和入口
- [[00-系统/CONTEXT|术语表]]：OrbitOS 的关键概念
- [[00-系统/PRINCIPLES|运行原则]]：agent 和系统协作时遵守什么
- [[00-系统/DATA-LIFECYCLE|数据生命周期]]：内容从进入系统到确认、处理、归档如何流转
- [[00-系统/CHANGELOG|系统变更记录]]：系统最近更新了什么

## 给 agent 使用

每个 agent 都应该从这句话开始：

```text
读取 AGENTS.md 并执行 Startup Sync。
```

当工作完成，或用户说“同步”“同步进度”“更新进度”时，执行 Progress Sync：

```text
生成合法 event，执行 Validate Sync，刷新相关时间线/项目视图，并记录需要 review 的候选事项。
```

如果 agent 要修改 OrbitOS 内核，还必须读取：

- [`.orbitos/AGENTS.md`](.orbitos/AGENTS.md)

## 二次开发

`.orbitos/` 是内部实现层。只有在你要修改 OrbitOS 内核、schema、workflow、日志、队列或设计文档时，才需要看这里。

二次开发入口：

- `.orbitos/AGENTS.md`
- `.orbitos/docs/REQUIREMENTS.md`
- `.orbitos/docs/ARCHITECTURE.md`
- `.orbitos/docs/DESIGN.md`
- `.orbitos/docs/GIT-MANAGEMENT.md`
- `.orbitos/docs/OBSIDIAN-STANDARD.md`

当前内部基线包括 strict schema、workflow、event log、queue、lifecycle state 和 validation eval。

运行最小验证集：

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

## 路线图

- 用 `01-收件箱/` 的真实旧内容执行一次 inbox triage dry run。
- 起草与根 `AGENTS.md` 对齐的 `startup-sync.md`。
- 用一个真实 agent 跑通完整协议。
- 单 agent 流程稳定后，再添加 agent profile。
- 日志和生命周期闭环跑通后，再添加 role card 和 thinking mode library。
- 在 OrbitOS 核心 workflow 稳定后，再细化 Hindsight Bridge 规则。

## 状态

OrbitOS 处于早期骨架阶段，但已经有可运行的系统基线。当前仓库包含工作区结构、系统说明书、时间线 Dashboard、严格 schema、校验 workflow、收件箱盘点 workflow、event log 约定和最小 eval。

下一阶段目标是用真实收件箱内容测试闭环，再接入一个真实 agent 跑通端到端流程。

## 许可证

MIT。见 [LICENSE](LICENSE)。
