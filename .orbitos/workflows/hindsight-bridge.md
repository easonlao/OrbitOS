---
title: Hindsight Bridge Workflow
area: internal
purpose: workflow
lifecycle: draft
created: 2026-06-15
updated: 2026-06-15
tags:
  - orbitos
  - workflow
  - hindsight
---

# Hindsight Bridge Workflow

本 workflow 约束 OrbitOS 如何使用 Hindsight 做跨会话记忆增强。

Hindsight 是可选增强层，不是 OrbitOS 的事实底座。OrbitOS 的事实底座仍是 `.orbitos/logs/events/`。

## 目标

- 降低 Hindsight 自动 retain 噪音。
- 只把稳定、可复用、经确认或验证的信息写入 Hindsight。
- 让 recall / retain / tags / document_id / event 审计有统一格式。
- 用测试 bank 验证规范，不污染现有 `eason` bank。

## 适用范围

适用于以下任务：

- 用户要求“记住”“写入 Hindsight”“以后注意”。
- agent 判断某条信息具备长期复用价值。
- 验证 Hindsight Bridge 试点。
- 需要用 Hindsight recall 查询历史环境、偏好、约束、部署和长期决策。

不适用于：

- 普通 Progress Sync。
- 今日状态更新。
- 项目短期进度。
- 未经确认的推测。
- 一次性命令输出、PR、commit 或临时提醒。

## Bank 策略

长期方向：

- OrbitOS 后期只使用一个正式主 bank。
- 正式主 bank 采用新建 bank，不继续把 `eason` 作为 OrbitOS 正式主 bank。
- `orbitos-test` 是过渡测试 bank，用于验证规则和接入路径，不代表长期多 bank 架构。
- `eason` 保留为历史 / 个人混合记忆 bank，不作为 OrbitOS 新规范的事实基线。
- 长期隔离优先依赖确定性 tags、retain 规则和 event 审计，而不是为每个 agent 拆 bank。

首个试点 bank 使用：

```text
orbitos-test
```

规则：

- `eason` 保留为历史 / 个人混合记忆 bank，首阶段只读 recall 为主。
- `orbitos-test` 只用于 Hindsight Bridge 试点。
- 不从 `eason` 批量导入旧数据。
- 不在 `orbitos-test` 开启 auto retain。
- 试点不为了凑数量批量写入；只在真实命中 retain 条件时写入高质量结构化记忆。
- 试点通过后，再确认正式主 bank 名称、迁移边界和旧数据治理方式。

## 接入路径

首版标准路径：

```text
Hindsight HTTP API + 显式 bank 路径
```

原因：

- 显式 bank 路径可以保证试点写入 `orbitos-test`，不污染 `eason`。
- HTTP API 不依赖单个 agent 的插件实现，适合 Hermes / Codex / Nova / HanaAgent 共享同一套语义规则。
- 当前 Hermes 默认 `hindsight_retain` 工具绑定配置 bank `eason`，不能作为 `orbitos-test` 试点写入路径。

首版禁止：

- 不用 Hermes 默认 `hindsight_retain` 写试点记忆。
- 不在无法显式指定 bank 的工具中执行 retain。

可选路径：

- MCP：只有在确认工具可显式指定 bank、tags、document_id 后才可用于试点。
- SDK：后续需要正式插件时再评估，不作为首版依赖。

## MCP 适配策略

MCP 是 Hindsight Bridge 的可选接入层，不是首版标准路径。

Hindsight MCP endpoint：

```text
http://10.10.10.35:8888/mcp/{bank_id}/
```

示例：

```text
http://10.10.10.35:8888/mcp/orbitos-test/
http://10.10.10.35:8888/mcp/eason/
```

### MCP 适用场景

- agent 原生支持 MCP，且可以配置 Hindsight MCP endpoint。
- 需要让 agent 用工具语义执行 recall / retain / reflect。
- 不方便直接写 HTTP API 调用，但能稳定配置 bank-scoped MCP server。

### MCP 模式

优先使用 single-bank endpoint：

```text
/mcp/{bank_id}/
```

原因：

- bank 从 URL 隐式确定，降低 agent 写错 bank 的概率。
- 测试期 `orbitos-test` 和 `eason` 可通过不同 MCP server 配置隔离。
- 长期如果只保留一个主 bank，则所有普通 agent 只配置该主 bank 的 single-bank endpoint。
- 工具调用不需要每次传 `bank_id`，更符合 agent 工具使用习惯。

multi-bank endpoint：

```text
/mcp/
```

只适合管理员或明确需要 bank 管理的场景。普通 agent 不应默认使用 multi-bank MCP，因为它暴露 `list_banks`、`create_bank` 等更大权限面。

### MCP 安全边界

当前 Hindsight API / MCP 暂不要求认证，前提是仅在可信局域网内使用，不暴露公网。

仍需遵守：

- 普通 agent 固定使用 single-bank endpoint。
- 不使用 multi-bank MCP 给普通 agent。
- 不让无人值守任务执行 MCP retain。
- 后续如果开放到非可信网络，再评估 API key tenant extension 或反向代理鉴权。
- 可按需要限制 `mcp_enabled_tools`，例如只开放 recall / list / retain，暂不开 delete / bank management。

### MCP retain 规则

如果 agent 通过 MCP retain，仍必须遵守本 workflow：

- 目标 endpoint 必须是 `orbitos-test` single-bank endpoint，除非用户明确确认写其他 bank。
- `content`、`context`、`document_id`、`tags` 必须符合 Retain 输入格式。
- tags 必须在白名单内。
- 不使用 `session:*` / `parent:*` / `conversation:*`。
- retain 后必须写 OrbitOS event。

如果 MCP 工具无法传入 `document_id` 或 tags，必须停止并报告，不得绕过本 workflow。

### MCP 验证清单

把 MCP 纳入 Hindsight Bridge 前，至少完成以下验证：

1. 连接 `http://10.10.10.35:8888/mcp/orbitos-test/`。
2. `tools/list` 中确认存在 recall / retain / list tags / operations 类工具。
3. 用 MCP recall 查询已存在的 `orbitos/runtime/hermes-ubuntu-orbitos-path`，确认命中。
4. 不执行 MCP retain，除非用户明确确认。
5. 确认 MCP 不会访问或写入 `eason`。
6. 如后续启用认证，再确认无 token 时失败、有 token 时成功。

## Recall 规则

必须先 recall 的场景：

- 用户询问 prior context、路径、IP、端口、部署、环境事实。
- 用户询问历史偏好、长期约束、过去决策。
- agent 准备修改可能受长期记忆影响的系统规则。

Recall 约束：

- 优先按主题和系统 tags 过滤。
- 不把 recall 结果直接当事实底座；关键事实仍需本地文件、event 或工具验证。
- recall 使用情况必须写入后续 event：query 摘要、是否命中、是否影响决策。

## Retain 触发条件

只有以下情况可以 retain：

1. 用户明确要求记住或写入 Hindsight。
2. 用户确认了长期规则、偏好、操作边界或系统设计。
3. 环境事实经过工具验证，并会影响后续 agent 行为。
4. 踩坑、根因和修复路径具备跨会话复用价值。
5. 多 agent 协作需要共享的稳定上下文。

以下情况禁止 retain：

- 普通任务流水。
- 未确认的 agent 推测。
- 今日 Dashboard 摘要。
- 项目短期进度。
- 临时命令输出。
- 完整 memory 正文、隐私原文或长对话摘录。
- `session:*`、`parent:*`、`conversation:*` 等高基数动态 tag。

## Retain 输入格式

每次 retain 必须先形成结构化输入：

```yaml
bank: orbitos-test
document_id: orbitos/{topic}/{stable-id}
context: "{一句话说明来源、确认状态和用途}"
tags:
  - user:eason
  - system:orbitos
  - agent:{agent_id}
  - type:{type}
  - topic:{topic}
content: |
  ## Context
  这条记忆来自哪里，是否经过用户确认或工具验证，未来用于什么场景。

  ## Key Facts
  - 可复用事实 1
  - 可复用事实 2

  ## Boundaries
  - 不适用范围
  - 不能误用的地方

  ## Evidence
  - OrbitOS event / 项目文档 / 工具验证来源
```

## 字段规则

### bank

试点阶段固定为 `orbitos-test`。

如果工具或插件无法指定 bank，必须停止并报告，不得退回写入 `eason`。

### document_id

格式：

```text
orbitos/{topic}/{stable-id}
```

示例：

```text
orbitos/hindsight/retain-format-v1
orbitos/runtime/hermes-ubuntu-path
orbitos/workflow/progress-sync-experience-check
```

规则：

- 使用稳定 ID，不使用 session id。
- 同一长期事实更新时复用同一个 document_id。
- 不用日期作为唯一标识，除非内容本身就是日期事件。

### context

必须说明：

- 来源：用户确认 / 工具验证 / 项目文档 / event。
- 状态：confirmed / verified / pilot。
- 用途：后续 agent 在什么场景 recall。

示例：

```text
OrbitOS Hindsight Bridge 试点中经用户确认的长期 retain 输入规范，用于约束多 agent 手动 retain。
```

禁止使用：

```text
聊天记录
记忆
总结
用户说的
```

### tags

试点阶段只允许以下 tags。

用户和系统：

```text
user:eason
system:orbitos
```

agent：

```text
agent:hermes
agent:codex
agent:nova
agent:hanaagent
```

type：

```text
type:decision
type:preference
type:config
type:environment
type:pitfall
type:workflow
type:constraint
```

topic：

```text
topic:orbitos
topic:hindsight
topic:agent-onboarding
topic:workflow
topic:runtime
topic:inbox
topic:knowledge
```

禁止 tags：

```text
session:*
parent:*
conversation:*
timestamp:*
random-id:*
自由发挥的长 tag
```

如果 Hindsight HTTP API 在当前部署中需要 `document_tags` 才能生效，agent 必须在报告中说明；不要静默把 `tags` 写成无效字段。

当前试点结论：

- Hindsight 0.8.2 HTTP retain 使用 item-level `tags` 生效。
- `document_tags` 仍可能兼容，但已 deprecated，不作为新 workflow 的推荐字段。

## 执行流程

1. 执行 Startup Sync。
2. 读取本 workflow。
3. 判断本次是 recall、retain、还是只读调查。
4. 如果是 recall：
   - 形成查询问题。
   - 选择最小 tags。
   - 执行 recall。
   - 用本地事实源验证关键结论。
5. 如果是 retain：
   - 检查是否命中 Retain 触发条件。
   - 确认目标 bank 是否为 `orbitos-test`。
   - 按 Retain 输入格式生成 draft。
   - 检查 tags 是否在白名单内。
   - 检查是否包含禁止内容。
   - 用户未明确授权时，先输出 draft 等确认。
   - 执行 retain 后写 OrbitOS event。
6. 如果是只读调查：
   - 只读取配置、stats、tags、operations。
   - 不读取 memory 正文，除非用户明确授权。
   - 不 retain。
7. 执行 Progress Sync。

## 执行清单

### 进入检查

- [ ] 已确认 `.orbitos/` 存在。
- [ ] 已执行 Startup Sync。
- [ ] 已确认当前 agent 已注册。
- [ ] 已确认本次任务类型：recall / retain / survey。
- [ ] 已确认 Hindsight 不是本次任务的唯一事实源。

### 执行检查

- [ ] 如 recall，已记录 query 摘要和使用的 tags。
- [ ] 如 recall，关键结论已用 OrbitOS 文件、event 或工具验证。
- [ ] 如 retain，已确认触发条件成立。
- [ ] 如 retain，bank 为 `orbitos-test`。
- [ ] 如 retain，document_id 稳定且不含 session id。
- [ ] 如 retain，context 说明来源、确认状态和用途。
- [ ] 如 retain，tags 全部在白名单内。
- [ ] 如 retain，content 使用指定 Markdown 结构。
- [ ] 如 retain，未包含 memory 正文、隐私原文或长对话摘录。
- [ ] 如 retain，已确认当前 API/工具的 tags 字段实际生效。

### 退出检查

- [ ] 已写入 event，或记录不需要写 event 的原因。
- [ ] event 已记录 Hindsight recall / retain / skipped / unavailable 状态。
- [ ] 如 retain，event 已记录 bank、document_id、tags、内容摘要和原因。
- [ ] 如 retain 失败，已记录失败命令或工具错误。
- [ ] 如修改 OrbitOS 文件，已运行 validation。
- [ ] 已记录跳过项和原因。

## 禁止

- 不在试点阶段写入 `eason`，除非用户明确确认。
- 不启用 auto retain。
- 不使用 `session:*` / `parent:*` / `conversation:*` 作为长期记忆 tags。
- 不把完整对话、原始日志或 memory 正文写入 Hindsight。
- 不把 Hindsight recall 当作最终事实源。
- 不在未写 event 的情况下执行 retain。
- 不把本 workflow 直接提升为 core rule；试点通过后再讨论提升。
