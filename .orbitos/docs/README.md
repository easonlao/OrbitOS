# OrbitOS 开发文档

这里保存 OrbitOS 产品设计，不保存 runtime 状态或当天任务。

## 文档职责

| 文件 | 回答的问题 |
|---|---|
| `REQUIREMENTS.md` | 为什么做、必须满足什么、当前不做什么 |
| `ARCHITECTURE.md` | 系统由哪些部分组成、事实和状态如何流动 |
| `DESIGN.md` | 目录、文件、对象和具体行为如何实现 |
| `RUNTIME.md` | agent 运行环境最低要求是什么 |

## 边界

- 确认后的产品需求、架构和设计写在这里。
- 尚未确认的问题写入本地项目 `OPEN-QUESTIONS.md`。
- 阶段路线写入本地项目 `ROADMAP.md`。
- 当前任务写入本地项目 `TASKS.md`。
- 当前进度写入本地项目 `STATUS.md`。
- 稳定执行规则进入 `.orbitos/rules/core/`。
- 可执行流程进入 `.orbitos/workflows/`。
- 用户需要理解的内容经过改写后进入 `00-系统/`。

不要把讨论流水、任务清单、当前进度或历史复盘写进本目录。

