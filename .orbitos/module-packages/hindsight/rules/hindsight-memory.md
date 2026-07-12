---
title: Hindsight Memory Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-27
updated: 2026-07-05
tags:
  - orbitos
  - hindsight
  - memory
  - agent-rule
---

# Hindsight Memory Rule

本规则只回答三件事：

1. Agent 什么时候必须使用 Hindsight recall。
2. 什么内容才配被提炼成 Hindsight memory。
3. 直连 HTTP API 时，最小命令和最小格式是什么。

Hindsight 是记忆增强层，不是 OrbitOS 的事实底座，也不是项目状态源。

## 1. 默认接入方式

- 默认接入方式是 Hindsight HTTP API。
- 不额外依赖 MCP 或 hooks。
- 官方也支持 wrapper 自动模式与 skill / SDK 配套，但 OrbitOS 当前不把它们当默认接入前提。

发布默认地址模板：

```text
{hindsight_base_url}/v1/default/banks/{bank_id}
```

正式默认 bank 名称：

```text
orbit-os
```

## 2. 必须先 recall 的场景

命中以下情况时，Agent 必须先 recall，再用本地文件、event 或工具复核关键结论：

1. 用户询问 prior context、路径、IP、端口、部署或环境事实。
2. 用户询问长期偏好、稳定约束或既有决策。
3. Agent 准备修改可能受长期记忆影响的系统规则。
4. 多 Agent 协作需要确认既有共享边界，而这些边界已经具备跨会话复用价值。

如果本地权威主源已经足够，且 recall 不会改变决策，可以跳过 Hindsight。

Recall 结果默认只算候选线索，不自动等于本地事实。只有当它将被用于以下动作时，才必须回查本地主源：

1. 直接回答用户关于路径、环境、部署、偏好、约束或既有决策的事实问题。
2. 修改 OrbitOS 文件、系统规则、workflow、项目状态或其他正式文档。
3. 把某条 recalled 信息提升成 retain 输入、正式结论或升级给用户的确认性判断。

如果 recall 只是帮助 agent 找到下一份本地来源文件，而尚未把 recalled 内容本身当成结论，可以先不做额外复核。

## 3. Memory 触发门

只有同时满足以下四个问题，才把内容视为 Hindsight memory 候选：

1. 这条信息脱离当前任务后仍然成立。
2. 下次忘记它，会直接影响执行或判断。
3. 它能被压成一条最小稳定摘要，而不是保留长正文。
4. 它比单纯留在本地主源更值得被后续 recall 直接命中。

只要有一条不满足，就留在本地主源，不 retain。

社区反馈对应的 OrbitOS 默认判断：

- 不要为了“也许以后有用”而放宽 memory 门槛。
- 比起多写，当前更该优先减少误 retain 和误 recall。
- shared bank 的默认策略应先缩范围、再召回，而不是先宽召回再人工筛。
- 能先靠 tags 缩小 recall 范围时，不要依赖宽召回后再人工挑选。

## 4. 优先 retain 的内容

- 稳定环境事实
- 长期约束
- 已确认的系统边界
- 反复出现且有明确修法的坑
- 多 Agent 共享的稳定协作原则
- 用户明确要求“记住”的长期信息

## 5. 默认 skip 的内容

- 当前项目进度
- `STATUS.md` 中的滚动事项
- handoff 全文、接手动作、未完成项
- 待确认事项
- 临时草稿
- 未确认推测
- 当日 Dashboard 摘要
- 一次性命令输出
- 长对话摘录或原始日志

这些内容应继续留在 `STATUS.md`、handoff、`LESSONS-LEARNED.md`、`04-知识/` 或 event。

## 6. 最小只读命令

以下命令是发布侧默认示例，实际部署时由 `{hindsight_base_url}` 替换成具体服务地址。测试 bank 只用于验证或试点，不作为产品默认 bank。

### 6.1 stats

```bash
curl -sS {hindsight_base_url}/v1/default/banks/orbit-os/stats
```

### 6.2 tags

```bash
curl -sS {hindsight_base_url}/v1/default/banks/orbit-os/tags
```

### 6.3 recall

```bash
curl -sS -X POST {hindsight_base_url}/v1/default/banks/orbit-os/memories/recall \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Hermes runtime path for future recall\",\"tags\":[\"system:orbitos\",\"topic:runtime\"],\"tags_match\":\"all_strict\"}"
```

参数倾向：

- 默认先带 `system:orbitos` 和至少一个 `topic:*` tag。
- 只对某个 agent 成立的内容，再额外带 `agent:{agent_id}`。
- 多个 scope tag 并用时，默认采用 strict 匹配，避免未打 tag 的内容混入。
- 默认问题写具体，不写泛问题。
- 如果只是确认 bank 是否可用，先用 `stats / tags`，不要直接做大范围 recall。
- 裸 recall 或放宽过滤，只能作为第二步回退：先说明严格过滤未命中，再决定是否扩大范围。

## 7. 最小 retain 规则

如命中 retain：

- 正式默认 bank 是 `orbit-os`
- `orbitos-test` 只用于验证、试点或本地测试，不作为产品默认 bank
- 正式库优先从“已有本地主源、已多轮验证、会持续影响 Agent 行为”的协作原则或稳定环境事实开始
- 必须使用稳定 `document_id`
- 必须使用白名单 tags
- 必须把内容压成最小稳定摘要
- retain 后必须写 OrbitOS event

## 8. 一句话判断

Hindsight 只收“已经确认、以后还会反复改变 Agent 行为”的最小稳定摘要；凡是仍在推进、仍需协作或仍依赖当前项目上下文的内容，都不应被提炼成 memory。


