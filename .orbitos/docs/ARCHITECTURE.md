# OrbitOS Architecture

## Positioning

OrbitOS has two main layers:

- Human layer: Obsidian-readable Markdown.
- Runtime layer: `.orbitos/` schemas, logs, queues, state, workflows, and design docs.

## Top-Level Structure

```text
AGENTS.md
00-系统/
01-收件箱/
02-时间线/
03-项目/
04-知识/
05-资源/
06-输出/
99-归档/
.orbitos/
```

## First-Class Objects

- Agent Profile: runtime agent capabilities and limits.
- Role Card: loadable expert identity, not bound to one agent.
- Thinking Mode: reusable reasoning method.
- Workflow: staged procedure.
- Machine Log: event/session/run facts.
- Obsidian Artifact: human-readable Markdown output.
- Hindsight Bridge: optional memory integration.

## Agent Lifecycle

```text
Startup Sync -> Work Execution -> Progress Sync
```

## Fact Base

`.orbitos/logs/events/` is the fact base. Human Markdown files are views, summaries, or artifacts derived from facts and confirmed context.

## Hindsight Boundary

Hindsight can help recall or retain memory, but OrbitOS must operate without it.
