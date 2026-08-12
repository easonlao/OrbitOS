---
title: Agent 接入与状态
area: system
purpose: status
lifecycle: active
created: 2026-06-12
updated: 2026-08-12
tags:
  - orbitos
  - agents
---

# Agent 接入与状态

这里是已接入 Agent 的看板入口。执行规则不放在本页，而由根 `AGENTS.md` 和对应 workflow 管理。

第一次使用时，让 Agent 先执行 Startup Sync；如果它不在 registry 中，先确认 `agent_id`、部署位置、局域网 IP、接入方式和 OrbitOS 路径，再按 agent-onboarding workflow 注册。

## 当前 Agents

- [[codex|Codex]]：本地工作区实现与整合 Agent。
- [[nova|Nova]]：知识整理与结构化 Agent。
- [[hermes|Hermes]]：Ubuntu 映射运行时上的审阅与协同 Agent。
- [[mimo|MiMo]]：通过 WSL 接入本地 OrbitOS 的执行 Agent。
- [[workbuddy|WorkBuddy]]：本地开发与协作 Agent，支持多角色切换。

## 当前运行状态

- `.orbitos/agents/registry.yaml` 已登记 `codex / nova / hermes / mimo / workbuddy`。
- 后续新 Agent 注册后，在这里追加入口，并链接到 `[[{agent_id}|对应 Agent 档案]]`。

## 交接入口

- `BOARD.md`：Agent 之间需要继续交接的索引。
- `handoff/`：每次交接的实例区与归档位置。
- `.orbitos/templates/00-系统/agents/handoff/TEMPLATE.md`：handoff 模板源。
- `.orbitos/templates/00-系统/agents/PROFILE-TEMPLATE.md`：新 Agent 档案模板源。
- `.orbitos/scripts/prepare_agent_onboarding.py`：registry + profile 的 onboarding 预演/写入脚本。
- `.orbitos/scripts/generate_agent_profile.py`：新 Agent 档案生成脚本。

## 接入后会发生什么

- 新 Agent 先确认身份和部署信息，再完成注册。
- 已注册 Agent 使用轻量档案保存定位和部署信息，完整经验按需展开。
- 运行环境差异记录在本地，不预置到发布模板。
- 跨 Agent 可复用的经验只有经过确认后才会提升为公共规则。

## 注销 Agent

Agent 不再使用时，通过注销流程下线，而不是手工删除 registry 条目。注销有统一的入口和固定步骤，支持中途恢复和重复执行。

### 什么时候用哪种注销

| 场景 | 适用情况 | 说明 |
|---|---|---|
| 主动注销 | Agent 正常退役、被替代、不再使用 | 资源可预期释放，流程完整走完 |
| 异常注销 | Agent 失联、账号/平台身份废弃、沙箱失效 | 部分清理可能失败或跳过；需要二次确认 |

### 注销会发生什么

- registry 中该 Agent 的状态变为已注销，并记录注销时间、原因和是否异常注销。
- 该 Agent 的档案、经验和环境报告归档到 `99-归档/agents-{id}-{日期}/`，不直接删除。
- 该 Agent 名下未完成的任务、会话和交接会解除绑定（标记给人工处理，不自动转交给别人）。
- 注销动作会写入事件记录；注销后该 Agent 不再被 Startup Sync 认领，也不再收到新任务分发。

### 使用方式

先查看状态，再执行注销：

```text
python .orbitos/scripts/offboard-agent.py status --agent-id <agent_id>
python .orbitos/scripts/offboard-agent.py offboard --agent-id <agent_id> --reason "注销原因" --confirm
```

异常注销额外要求二次确认：

```text
python .orbitos/scripts/offboard-agent.py offboard --agent-id <agent_id> --reason "原因" --exception --confirm --confirm-exception
```

### 注意事项

- 注销**不可逆**：状态不会自动回退；档案虽归档可查，但重新启用需要你明确决定并重新走接入流程。
- 注销前请确认该 Agent 名下没有需要收尾的工作；未完成的交接会转为待人工处理。
- 注销中途中断可以重新执行，会从断点继续；对已注销的 Agent 重复执行不会报错或重复归档。
- 历史事件和归档目录会长期保留，供追溯。

## 机器来源

- `.orbitos/agents/registry.yaml`
- `.orbitos/state/env/`
- `.orbitos/logs/events/`
