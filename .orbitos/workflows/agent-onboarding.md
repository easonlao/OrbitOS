---
title: Agent Onboarding Workflow
area: internal
purpose: workflow
lifecycle: active
created: 2026-06-13
updated: 2026-06-13
tags:
  - orbitos
  - workflow
  - agent-onboarding
---

# Agent Onboarding Workflow

Agent Onboarding 用于把一个真实 agent 接入 OrbitOS。

它不是 Startup Sync，也不是知识库初始化。它只在用户确认 agent 身份后，登记部署信息、创建 Agent Profile，并验证新 agent 以后能通过 Startup Sync 进入系统。

## 目标

- 确认稳定 `agent_id`。
- 记录 agent 的部署位置、局域网 IP、接入方式和 OrbitOS 路径。
- 更新机器可读 registry。
- 创建人读 Agent Profile。
- 让后续 Startup Sync 能识别该 agent。

## 触发条件

- 用户明确说“接入新 agent”“注册 agent”“初始化 Hermes/HanaAgent/Claude Code”等。
- Startup Sync 发现当前 agent 不在 `.orbitos/agents/registry.yaml`，并且用户已经确认 `agent_id`。

## 前置确认

开始写入前，必须确认：

- `agent_id`：稳定小写 ID，例如 `hermes`、`hanaagent`、`claude-code`。
- `display_name`：人读显示名。
- `deployment.location`：部署位置，例如某台电脑、NAS、服务名或本地会话。
- `deployment.lan_ip`：局域网 IP；不知道时填 `unknown`，并投影到待确认。
- `deployment.access`：接入方式，例如 local filesystem、SSH、SynologyDrive、Git clone、MCP、API。
- `deployment.orbitos_path`：该 agent 看到的 OrbitOS 路径。

## 执行流程

1. 读取 `.orbitos/AGENTS.md`。
2. 读取 `.orbitos/schemas/agent-registry.schema.yaml`。
3. 读取 `.orbitos/agents/registry.yaml`，确认 `agent_id` 未重复。
4. 更新 `.orbitos/agents/registry.yaml`。
5. 创建 `00-系统/agents/{agent_id}.md`。
6. 在 Agent Profile 中保留以下区块：
   - 基本信息
   - 部署信息
   - 最近工作
   - 待确认来源
   - 经验记录
   - 踩坑
   - 规则候选
   - Learned Rule 使用记录
7. 运行 validation eval：
   - 优先：`pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1`
   - fallback：`node .orbitos/scripts/run-validation.mjs`
   - 两者都不可用时，才允许手动校验，并在 event checklist 中标记 `skipped`。
8. 执行 Progress Sync，写入 event，并刷新 `今日.md` 的 Agents 状态。

## 用户提示词

把下面这段发给一个新 agent，即可开始接入：

```text
你现在接入 OrbitOS。请先阅读 AGENTS.md，执行 Startup Sync。
如果你还没有注册，不要写入任何文件；请先告诉我需要确认的 agent_id、部署位置、局域网 IP、接入方式和 OrbitOS 路径。
我确认后，再按 .orbitos/workflows/agent-onboarding.md 注册。
```

## 执行清单

### 进入检查

- [ ] 已确认当前 workflow 是新 agent 接入，而不是普通 Startup Sync。
- [ ] 已确认用户明确给出或确认 `agent_id`。
- [ ] 已读取 `.orbitos/AGENTS.md` 和 agent registry schema。

### 执行检查

- [ ] 已收集最小部署信息。
- [ ] 已确认 `agent_id` 未重复。
- [ ] 已更新 registry。
- [ ] 已创建 Agent Profile。
- [ ] 已把未知 IP、未知路径或接入限制写入待确认来源。

### 退出检查

- [ ] 已运行 validation eval；如 sandbox 阻止脚本执行，已尝试 Node fallback 或记录手动校验范围。
- [ ] 已执行 Progress Sync 并写入 event。
- [ ] 已刷新 `今日.md` 的 Agents 状态。
- [ ] 已给用户一段可复用的新 agent 接入提示词。

## 禁止

- 未经用户确认自动注册未知 agent。
- 用显示名替代 `agent_id`。
- 缺少部署位置时标记注册完成。
- 把角色卡、思考模型或任务偏好写进 registry。
- 把 Hindsight 作为接入 OrbitOS 的必需条件。
- 只因 `pwsh` 无法运行就跳过 validation，而不尝试 fallback 或记录手动校验边界。
