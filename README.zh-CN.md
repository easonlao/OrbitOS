# OrbitOS

> 一个 Markdown 原生的人机协作工作台，用来协调人、agents、记忆系统和 Obsidian 可读产物。

中文 | [English](README.md)

OrbitOS 是一个多 agent 协作工作台。它的核心想法很简单：agent 不应该只在聊天窗口里回答问题，而应该进入一个共享工作区，理解当前状态，执行有边界的工作，留下可追踪的事件记录，并产出能长期在 Obsidian 中阅读和维护的 Markdown。

这个仓库既是实际使用的 Obsidian vault，也是 Codex、Hermes、HanaAgent、Claude Code 等 agents 的协作协议入口。

## OrbitOS 是什么

OrbitOS 不是传统个人知识库，而是一个协作层，用来：

- 把 Obsidian 作为人类阅读和审查界面
- 通过 [`AGENTS.md`](AGENTS.md) 给所有 agent 一个统一入口
- 分离人读 Markdown 和机器/运行时状态
- 通过 event log 追踪 agent 工作
- 把原始输入整理为项目、知识、资源或输出

## 核心概念

| 概念 | 含义 |
| --- | --- |
| `AGENTS.md` | 所有 agent 首先读取的根入口契约。 |
| Startup Sync | agent 进入后先读取当前状态并输出短摘要。 |
| Progress Sync | 完成实质性工作后，或用户说“同步进度”时执行的收尾/更新流程。 |
| Event log | `.orbitos/logs/events/` 下的事实底座。 |
| 人读视图 | Obsidian 可读的 Markdown，例如 `今日.md`、`待确认.md`、项目 `STATUS.md`。 |
| Hindsight | 可选记忆层；有帮助，但不是 OrbitOS 运行必需项。 |

## 仓库结构

```text
AGENTS.md              # agent 使用入口
README.md              # GitHub 英文项目说明
README.zh-CN.md        # GitHub 中文项目说明
00-系统/               # 人读的运行规则和系统说明
01-收件箱/             # 低摩擦原始输入
02-时间线/             # 当前时间视图
03-项目/               # 项目边界层
04-知识/               # 已确认、可复用的知识
05-资源/               # 已处理的参考资料和附件
06-输出/               # Obsidian 内产出的 Markdown 成品
99-归档/               # 退出当前使用的对象
.orbitos/              # 运行时层：schema、日志、队列、workflow、设计文档
```

## 快速开始

### 给人使用

用 Obsidian 打开这个仓库，从这些入口开始：

- [`02-时间线/今日.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E4%BB%8A%E6%97%A5.md)：今天状态
- [`02-时间线/本周.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E6%9C%AC%E5%91%A8.md)：本周洞察
- [`02-时间线/待确认.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E5%BE%85%E7%A1%AE%E8%AE%A4.md)：需要判断的事项
- [`02-时间线/下一步.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E4%B8%8B%E4%B8%80%E6%AD%A5.md)：下一步行动入口

把未处理材料丢进：

- [`01-收件箱/粘贴.md`](01-%E6%94%B6%E4%BB%B6%E7%AE%B1/%E7%B2%98%E8%B4%B4.md)

### 给 agent 使用

每个 agent 都应该从这句话开始：

```text
读取 AGENTS.md 并执行 Startup Sync。
```

当工作完成，或用户说“同步”“同步进度”“更新进度”时，执行 Progress Sync：

```text
写入 event，刷新相关时间线/项目视图，并记录需要 review 的候选事项。
```

如果 agent 要修改 OrbitOS 内核，还必须读取：

- [`.orbitos/AGENTS.md`](.orbitos/AGENTS.md)

## 当前协议

OrbitOS 当前采用三段式 agent 生命周期：

```text
Startup Sync -> Work Execution -> Progress Sync
```

当前事实底座是：

```text
.orbitos/logs/events/
```

人读 Markdown 被视为视图、摘要或产物。它必须可读、聚焦，并能追溯到 event 或来源文档。

## 设计文档

内部设计记录在 `.orbitos/docs/`：

- [Requirements](.orbitos/docs/REQUIREMENTS.md)
- [Architecture](.orbitos/docs/ARCHITECTURE.md)
- [Design](.orbitos/docs/DESIGN.md)

运行时系统文档在 `00-系统/`：

- [系统地图](00-%E7%B3%BB%E7%BB%9F/MAP.md)
- [术语表](00-%E7%B3%BB%E7%BB%9F/CONTEXT.md)
- [运行原则](00-%E7%B3%BB%E7%BB%9F/PRINCIPLES.md)
- [数据生命周期](00-%E7%B3%BB%E7%BB%9F/DATA-LIFECYCLE.md)
- [Obsidian 写作规范](00-%E7%B3%BB%E7%BB%9F/OBSIDIAN-STANDARD.md)
- [系统变更记录](00-%E7%B3%BB%E7%BB%9F/CHANGELOG.md)

## 路线图

- 定义 event schema。
- 定义 Startup Sync 和 Progress Sync workflow 文件。
- 为首批真实 agent 接入添加 agent profile。
- 添加 role card 和 thinking mode library。
- 在核心 workflow 稳定后，再细化 Hindsight Bridge 规则。

## 状态

OrbitOS 处于早期骨架阶段。当前仓库已经包含初始工作区结构、运行时文档、时间线视图和 event log 约定。下一阶段目标是用真实 agents 验证协议。

## 许可证

MIT。见 [LICENSE](LICENSE)。
