# OrbitOS

> A Markdown-native workspace for coordinating humans, agents, memory, and Obsidian-readable artifacts.

[中文](README.zh-CN.md) | English

OrbitOS is an Obsidian-first collaboration workspace for working with agents.

The core idea is simple: you read and review Markdown in Obsidian; agents help maintain state, organize raw input, record traceable work, and turn confirmed material into projects, knowledge, resources, or outputs.

## What OrbitOS Is

OrbitOS is not a traditional personal knowledge base, and it is not only an agent framework. It is a workspace that connects:

- Obsidian as the human-facing dashboard and reading surface
- `AGENTS.md` as the shared entry contract for agents
- `00-系统/` as the user-facing system manual
- `.orbitos/` as the internal runtime layer for schemas, logs, queues, workflows, rules, and design records

## Fastest Start

1. Download or clone this repository:

```powershell
git clone https://github.com/easonlao/OrbitOS.git
```

2. Open the cloned `OrbitOS` folder as a vault in Obsidian.
3. Put anything you want OrbitOS to handle into `01-收件箱/`.
4. Ask an agent to start from the workspace entry:

```text
Read AGENTS.md, run Startup Sync, and tell me the current OrbitOS state.
```

Your main daily view is:

- [Today Dashboard](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E4%BB%8A%E6%97%A5.md)

If something needs your decision, it appears in:

- [Pending Review](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E5%BE%85%E7%A1%AE%E8%AE%A4.md)

If you want to continue from the current state, use:

- [Next Steps](02-%E6%97%B6%E9%97%B4%E7%BA%BF/%E4%B8%8B%E4%B8%80%E6%AD%A5.md)

## How It Feels To Use

OrbitOS keeps the user-facing path short:

```text
drop material into 01-收件箱/
  -> talk with an agent
  -> review 今日.md / 待确认.md
  -> confirmed material becomes project, knowledge, resource, or output
```

Raw input stays low-friction. Agents can triage, summarize, and propose routes, but confirmed long-term knowledge or formal artifacts still require user review.

## Repository Layout

```text
AGENTS.md              # Agent usage entry
README.md              # GitHub-facing project guide
README.zh-CN.md        # Chinese project guide
00-系统/               # Human-readable runtime rules and system docs
01-收件箱/             # Low-friction raw input
02-时间线/             # Human dashboard and expanded status views
03-项目/               # Project boundary layer
04-知识/               # Confirmed reusable knowledge
05-资源/               # Processed references and attachments
06-输出/               # Markdown outputs produced in Obsidian
99-归档/               # Archived inactive objects
.orbitos/              # Runtime layer: schemas, logs, queues, workflows, rules, design docs
```

## User Manual

The `00-系统/` folder is the user-facing manual for OrbitOS:

- [System Map](00-%E7%B3%BB%E7%BB%9F/MAP.md): where things live
- [Context](00-%E7%B3%BB%E7%BB%9F/CONTEXT.md): key terms
- [Principles](00-%E7%B3%BB%E7%BB%9F/PRINCIPLES.md): operating principles
- [Data Lifecycle](00-%E7%B3%BB%E7%BB%9F/DATA-LIFECYCLE.md): how data moves through the system
- [Changelog](00-%E7%B3%BB%E7%BB%9F/CHANGELOG.md): system updates

## For Agents

Every agent should start with:

```text
Read AGENTS.md and run Startup Sync.
```

When connecting a new agent for the first time, use this fuller prompt:

```text
You are now connecting to OrbitOS. Read AGENTS.md first and run Startup Sync.
If you are not registered yet, do not write any files. Tell me which agent_id, deployment location, LAN IP, access method, and OrbitOS path I need to confirm.
After I confirm them, register through the agent-onboarding workflow.
```

The important boundary is: a new agent starts read-only; if it is not registered, it stops and asks for identity and deployment details; only after user confirmation may it write the registry and Agent Profile.

When work is complete, or when the user says "同步", "同步进度", or "更新进度", run Progress Sync:

```text
Create a valid event, run Validate Sync, refresh relevant timeline/project views, and record candidates that need review.
```

Agents modifying OrbitOS internals must also read:

- [`.orbitos/AGENTS.md`](.orbitos/AGENTS.md)

## For Developers

Internal implementation records are in `.orbitos/`.

Start here only if you are modifying OrbitOS itself:

- `.orbitos/AGENTS.md`
- `.orbitos/docs/REQUIREMENTS.md`
- `.orbitos/docs/ARCHITECTURE.md`
- `.orbitos/docs/DESIGN.md`
- `.orbitos/workflows/agent-onboarding.md`
- `.orbitos/rules/core/git-management.md`
- `.orbitos/rules/core/markdown-writing.md`

Design records live in `.orbitos/docs/`. Stable execution rules live in `.orbitos/rules/core/`.

The current runtime baseline includes strict schemas, workflows, event logs, queues, lifecycle state, and validation evals.

Run the validation eval set with:

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

If an agent sandbox cannot start PowerShell, use the Node.js fallback:

```powershell
node .orbitos/scripts/run-validation.mjs
```

## Roadmap

- Run one `01-收件箱/` inbox triage dry run with Nova and validate its knowledge-manager role and the inbox loop.
- Trigger Experience Capture with one real pitfall and validate the profile -> Rule Evolution input loop.
- Add role cards and thinking mode libraries after the logging and lifecycle loop is proven.
- Clarify Hindsight Bridge rules after OrbitOS core workflow stabilizes.

## Status

OrbitOS is in early scaffold stage with a working system baseline. The repository contains the workspace structure, user manual, timeline dashboard, Agent Profile baseline, strict schemas, validation workflow, inbox triage workflow, event log convention, and a minimal validation eval set.

The next milestone is connecting one real agent end to end, then testing the loop on real inbox content.

## License

MIT. See [LICENSE](LICENSE).
