# OrbitOS

> A Markdown-native workspace for coordinating humans, agents, memory, and Obsidian-readable artifacts.

[中文](README.zh-CN.md) | English

OrbitOS is a multi-agent collaboration workspace built around one simple idea: agents should not just answer in chat. They should enter a shared workspace, understand the current state, do scoped work, leave traceable events, and produce Markdown that remains readable in Obsidian.

This repository is both the working vault and the protocol surface for agents such as Codex, Hermes, HanaAgent, Claude Code, and future assistants.

## What OrbitOS Is

OrbitOS is not a traditional personal knowledge base. It is a coordination layer for:

- using Obsidian as the human-facing reading and review interface
- giving agents a single entry contract through [`AGENTS.md`](AGENTS.md)
- separating human-readable Markdown from machine/runtime state
- keeping agent work traceable through event logs
- turning raw input into reviewed projects, knowledge, resources, or outputs

## Core Concepts

| Concept | Meaning |
| --- | --- |
| `AGENTS.md` | The root usage contract every agent reads first. |
| Startup Sync | The required first step: read current state and report a short status summary. |
| Progress Sync | The required closeout/update step after meaningful work or when the user says "同步进度". |
| Event log | The fact base under `.orbitos/logs/events/`. |
| Human view | Obsidian-readable Markdown such as `今日.md`, `待确认.md`, or project `STATUS.md`. |
| Hindsight | Optional memory layer; useful, but not required for OrbitOS to operate. |

## Repository Layout

```text
AGENTS.md              # Agent usage entry
README.md              # GitHub-facing project guide
00-系统/               # Human-readable runtime rules and system docs
01-收件箱/             # Low-friction raw input
02-时间线/             # Current timeline views
03-项目/               # Project boundary layer
04-知识/               # Confirmed reusable knowledge
05-资源/               # Processed references and attachments
06-输出/               # Markdown outputs produced in Obsidian
99-归档/               # Archived inactive objects
.orbitos/              # Runtime layer: schemas, logs, queues, workflows, design docs
```

## Quick Start

### For Humans

Open the repository as an Obsidian vault and start from:

- [`02-时间线/今日.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E4%BB%8A%E6%97%A5.md) for today's state
- [`02-时间线/本周.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E6%9C%AC%E5%91%A8.md) for weekly insight
- [`02-时间线/待确认.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E5%BE%85%E7%A1%AE%E8%AE%A4.md) for decisions that need review
- [`02-时间线/下一步.md`](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E4%B8%8B%E4%B8%80%E6%AD%A5.md) for the next actionable entry points

Drop unprocessed material into:

- [`01-收件箱/粘贴.md`](01-%E6%94%B6%E4%BB%B6%E7%AE%B1/%E7%B2%98%E8%B4%B4.md)

### For Agents

Every agent should start with:

```text
Read AGENTS.md and run Startup Sync.
```

When work is complete, or when the user says "同步", "同步进度", or "更新进度", run Progress Sync:

```text
Write an event, refresh relevant timeline/project views, and record candidates that need review.
```

Agents modifying OrbitOS internals must also read:

- [`.orbitos/AGENTS.md`](.orbitos/AGENTS.md)

## Current Protocol

OrbitOS currently enforces a three-step agent lifecycle:

```text
Startup Sync -> Work Execution -> Progress Sync
```

The current fact base is:

```text
.orbitos/logs/events/
```

Human-facing Markdown is treated as a view, summary, or artifact. It should be readable, focused, and traceable back to events or source documents.

## Design Docs

Internal design records live under `.orbitos/docs/`:

- [Requirements](.orbitos/docs/REQUIREMENTS.md)
- [Architecture](.orbitos/docs/ARCHITECTURE.md)
- [Design](.orbitos/docs/DESIGN.md)

Runtime-facing system docs live under `00-系统/`:

- [System Map](00-%E7%B3%BB%E7%BB%9F/MAP.md)
- [Context](00-%E7%B3%BB%E7%BB%9F/CONTEXT.md)
- [Principles](00-%E7%B3%BB%E7%BB%9F/PRINCIPLES.md)
- [Data Lifecycle](00-%E7%B3%BB%E7%BB%9F/DATA-LIFECYCLE.md)
- [Obsidian Standard](00-%E7%B3%BB%E7%BB%9F/OBSIDIAN-STANDARD.md)
- [Changelog](00-%E7%B3%BB%E7%BB%9F/CHANGELOG.md)

## Roadmap

- Define event schema.
- Define Startup Sync and Progress Sync workflow files.
- Add agent profiles for the first real integrations.
- Add role cards and thinking mode libraries.
- Clarify Hindsight Bridge rules after the core workflow stabilizes.

## Status

OrbitOS is in early scaffold stage. The current repository already contains the initial workspace structure, runtime docs, timeline views, and event log convention. The next milestone is validating the protocol with real agents.

## License

MIT. See [LICENSE](LICENSE).
