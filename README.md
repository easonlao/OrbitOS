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
3. Initialize local runtime files:

```bash
python .orbitos/scripts/init-runtime.py
```

This command only creates missing local files. It does not overwrite existing content.

4. Put anything you want OrbitOS to handle into `01-收件箱/`.
5. If you want an agent to connect, have it start from `AGENTS.md`; the execution rules live there, not in README.

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

`01-收件箱/` is the temporary intake area: you can drop text, links, image notes, or old material there first. Agents may triage, summarize, group, and suggest where the material should go; they must not turn it into confirmed knowledge cards, project artifacts, or publishable outputs without your confirmation.

## Repository Layout

```text
AGENTS.md              # Rules an agent must read before using OrbitOS
README.md              # English getting-started guide
README.zh-CN.md        # Chinese getting-started guide
00-系统/               # User-facing system manual
01-收件箱/             # Temporary intake for raw material
02-时间线/             # Today, this week, pending confirmations, and next steps
03-项目/               # Project folders, notes, and status
04-知识/               # Confirmed knowledge worth keeping long term
05-资源/               # References, attachments, and source material copies
06-输出/               # Finished Markdown outputs such as articles or reports
99-归档/               # Inactive material you want to keep
.orbitos/              # Internal files for agents and scripts; usually not opened by users
```

## User Manual

The `00-系统/` folder is the user-facing manual for OrbitOS:

- [System Map](00-%E7%B3%BB%E7%BB%9F/MAP.md): where things live
- [Context](00-%E7%B3%BB%E7%BB%9F/CONTEXT.md): key terms
- [Principles](00-%E7%B3%BB%E7%BB%9F/PRINCIPLES.md): operating principles
- [Data Lifecycle](00-%E7%B3%BB%E7%BB%9F/DATA-LIFECYCLE.md): how data moves through the system
- [Changelog](00-%E7%B3%BB%E7%BB%9F/CHANGELOG.md): system updates

## Working With Agents

README only explains how you use OrbitOS as a user. The only execution entry for agents is `AGENTS.md`.

You only need to know three things:

- A new agent should read `AGENTS.md` first.
- An unregistered agent must ask you to confirm its identity and deployment details before writing to the system.
- After work is done, you can say "同步", "同步进度", or "更新进度" to have the agent refresh the timeline and status according to `AGENTS.md`.

## Changing OrbitOS Itself

Daily use does not require opening `.orbitos/`.

Only enter the internal development layer when changing OrbitOS rules, workflows, schemas, directory protocol, or release process. Start here:

- [`.orbitos/AGENTS.md`](.orbitos/AGENTS.md)

Run the validation eval set with:

```bash
python .orbitos/scripts/run-validation.py
```

If Python is not available, use the Node.js fallback:

```bash
node .orbitos/scripts/run-validation.mjs
```

## License

MIT. See [LICENSE](LICENSE).
