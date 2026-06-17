---
title: Startup Sync Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-12
updated: 2026-06-13
tags:
  - orbitos
  - workflow
  - startup-sync
---

# Startup Sync Workflow

Startup Sync 在任何 agent 开始工作前执行。

## 目标

- 读取当前 OrbitOS 状态。
- 确认 agent 身份和部署上下文。
- 检查当前 runtime 是否满足 OrbitOS 最小运行环境。
- 读取当前 agent 自己的经验、踩坑和待确认来源。
- 输出短状态摘要。
- 防止未知 agent 自主注册或静默写入系统文件。
- 给新 agent 一个明确的下一步路由，而不是让 agent 自行猜测系统规则。
- 在 `.orbitos/` 缺失或工作副本不完整时立即停止。

## 只读原则

Startup Sync 是只读流程。

允许读取：

- `00-系统/00-开始使用.md`
- `00-系统/06-术语表.md`
- `00-系统/05-安全与边界.md`
- `.orbitos/agents/registry.yaml`
- 当前 agent 的 `profile_ref`
- `.orbitos/state/env/{agent_id}.json`，如果存在
- `02-时间线/今日.md`
- `02-时间线/待确认.md`
- `02-时间线/下一步.md`
- 当前任务明确涉及的项目 `README.md` 和 `STATUS.md`

## 工作副本完整性检查

Startup Sync 开始前必须确认：

- `.orbitos/` 存在。
- `.orbitos/agents/registry.yaml` 存在。
- `.orbitos/workflows/startup-sync.md` 存在。

如果任一缺失：

1. 立即停止。
2. 报告当前路径和缺失项。
3. 不退回旧 `.orbit/`。
4. 不读取其他 agent 的 profile。
5. 不执行写入型 workflow。

这通常表示当前 agent 使用的是过期同步副本、映射路径不完整，或仓库没有更新到当前 OrbitOS。

禁止写入：

- `.orbitos/agents/registry.yaml`
- `00-系统/agents/`
- `.orbitos/logs/events/`
- 任何项目、知识、资源、输出文件

## Agent 身份确认

agent 必须先声明或推断自己的 `agent_id`。

然后读取 `.orbitos/agents/registry.yaml`：

1. 如果 `agent_id` 存在：
   - 读取对应 `deployment`。
   - 读取对应 `profile_ref`。
   - 读取 `profile_ref` 中的 `经验记录`、`踩坑`、`待确认来源`、`Learned Rule 使用记录`。
   - 运行或读取 runtime 环境检查：
     - 优先运行 `python .orbitos/scripts/env-check.py --agent-id {agent_id}`。
     - 如果当前任务是只读且已有当日 `.orbitos/state/env/{agent_id}.json`，可以读取已有报告。
     - 如果 Python 不可用，标记 runtime `blocked`，不要执行写入型 workflow。
   - 在状态摘要中说明 agent_id、局域网 IP、接入方式和 OrbitOS 路径。
2. 如果 `agent_id` 不存在：
   - 立即停止 Startup Sync。
   - 不创建 registry。
   - 不创建 Agent Profile。
   - 不写 event。
   - 向用户询问：`当前 agent_id 应该是什么？确认后我再创建 Agent Profile。`

## 未知 Agent 注册流程

未知 agent 只有在用户明确确认 `agent_id` 后，才能进入注册流程。

注册流程不是 Startup Sync 的一部分，必须作为单独的系统变更执行：

1. 读取 `.orbitos/AGENTS.md`。
2. 读取 `.orbitos/schemas/agent-registry.schema.yaml`。
3. 收集最小部署信息：
   - `agent_id`
   - `deployment.location`
   - `deployment.lan_ip`
   - `deployment.access`
   - `deployment.orbitos_path`
4. 更新 `.orbitos/agents/registry.yaml`。
5. 创建 `00-系统/agents/{agent_id}.md`。
6. 运行 validation eval。
7. 执行 Progress Sync 写入 event。

## 输出格式

正常完成时，输出 5-8 行短状态摘要：

```text
Startup Sync 完成
- agent_id:
- 部署位置:
- 局域网 IP:
- 当前状态:
- 历史注意事项:
- 待确认:
- 下一步:
```

如果无法判断下一步，输出：

```text
Startup Sync 完成，但下一步不明确
- 我已确认的状态:
- 当前待确认:
- 可选入口:
- 需要用户确认的问题:
```

未知 agent 时，只输出确认问题，不继续摘要。

## 执行清单

### 进入检查

- [ ] 已确认当前任务处于进入 OrbitOS 的启动阶段。
- [ ] 已确认 `.orbitos/`、registry 和 startup-sync workflow 存在。
- [ ] 已确认 Startup Sync 只读，不推进任务。
- [ ] 已准备读取系统地图、术语、原则、registry 和时间线状态。
- [ ] 已准备读取当前 agent profile 的经验、踩坑和待确认来源。
- [ ] 已准备运行或读取 runtime 环境检查。

### 执行检查

- [ ] 已读取 `00-系统/00-开始使用.md`、`00-系统/06-术语表.md`、`00-系统/05-安全与边界.md`。
- [ ] 已读取 `.orbitos/agents/registry.yaml` 并确认当前 `agent_id`。
- [ ] 已读取当前 agent 的 `profile_ref`，并提取与本任务相关的经验、踩坑、待确认来源和 Learned Rule 使用记录。
- [ ] 已运行或读取 `.orbitos/state/env/{agent_id}.json`，并确认 runtime 未 blocked。
- [ ] 已读取 `02-时间线/今日.md`、`待确认.md`、`下一步.md`。
- [ ] 如涉及项目，已读取目标项目 `README.md` 和 `STATUS.md`。
- [ ] 如果 agent 未注册，已停止并询问用户确认 `agent_id`。

### 退出检查

- [ ] 已输出 5-8 行状态摘要，或未知 agent 确认问题。
- [ ] 已确认未写 registry、Agent Profile、event 或用户内容。
- [ ] 已记录所有不适用项和原因。

## 禁止

- 未经用户确认自动创建 agent_id。
- 在 Startup Sync 中写入 registry 或 Agent Profile。
- 用显示名替代 agent_id。
- 缺少 `deployment.lan_ip` 时标记为已完成。
- 把 Startup Sync 当作任务执行或决策流程。
- 不读 Task Router 就直接修改文件。
- 已注册 agent 不读取自己的 Agent Profile 就开始行动。
- runtime 为 `blocked` 时执行写入型 workflow。
- `.orbitos/` 缺失时退回旧 `.orbit/`。
- 无法读取 registry 时读取其他 agent profile。
