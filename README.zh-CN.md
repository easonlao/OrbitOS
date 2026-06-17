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
- `.orbitos/`：schema、日志、队列、workflow、rules、设计文档等内部运行层

## 最快开始

1. 下载或克隆这个仓库：

```powershell
git clone https://github.com/easonlao/OrbitOS.git
```

2. 在 Obsidian 里把克隆下来的 `OrbitOS` 文件夹打开为一个 vault。
3. 把你想丢进系统的东西复制到 `01-收件箱/`。
4. 如果要让 agent 接入，让它从 `AGENTS.md` 开始；具体执行规则都在 `AGENTS.md`，不是 README。

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

`01-收件箱/` 是临时入口：你可以先随手放文字、链接、截图说明或旧资料。agent 可以帮你盘点、摘要、分组，并建议放到哪里；但不能未经你确认就把这些内容变成正式知识卡片、项目产物或发布内容。

## 仓库结构

```text
AGENTS.md              # agent 进入系统时必须读取的规则入口
README.md              # 英文上手说明
README.zh-CN.md        # 中文上手说明
00-系统/               # 给用户看的系统说明书
01-收件箱/             # 临时入口，先放原始材料
02-时间线/             # 今天、本周、待确认和下一步
03-项目/               # 每个项目自己的资料和状态
04-知识/               # 已确认、值得长期保留的知识
05-资源/               # 参考资料、附件和原始材料副本
06-输出/               # 写好的文章、报告或其他 Markdown 成品
99-归档/               # 暂时不用但不想删除的内容
.orbitos/              # agent 和脚本使用的内部文件，普通使用时不用打开
```

## 系统说明书

`00-系统/` 是 OrbitOS 用户需要理解的系统说明书：

- [[00-系统/MAP|系统地图]]：当前有哪些系统文档和入口
- [[00-系统/CONTEXT|术语表]]：OrbitOS 的关键概念
- [[00-系统/PRINCIPLES|运行原则]]：agent 和系统协作时遵守什么
- [[00-系统/DATA-LIFECYCLE|数据生命周期]]：内容从进入系统到确认、处理、归档如何流转
- [[00-系统/CHANGELOG|系统变更记录]]：系统最近更新了什么

## Agent 协作

README 只说明你作为用户怎么使用 OrbitOS。agent 的唯一执行入口是 `AGENTS.md`。

你只需要知道三件事：

- 新 agent 第一次接入时，应该先读 `AGENTS.md`。
- 未注册的 agent 需要先向你确认身份和部署信息，不能直接写入系统。
- 工作完成后，你可以说“同步”“同步进度”或“更新进度”，让 agent 按 `AGENTS.md` 刷新时间线和状态。

## 修改 OrbitOS 本身

日常使用不需要打开 `.orbitos/`。

只有当你要修改 OrbitOS 的规则、workflow、schema、目录协议或发布流程时，才需要进入内部开发层。入口是：

- [`.orbitos/AGENTS.md`](.orbitos/AGENTS.md)

运行最小验证集：

```bash
python .orbitos/scripts/run-validation.py
```

如果 Python 不可用，可使用 Node.js fallback：

```bash
node .orbitos/scripts/run-validation.mjs
```

## 许可证

MIT。见 [LICENSE](LICENSE)。
