# README Writing Rule

This rule defines how OrbitOS root README files should be written.

It applies to:

- `README.md`
- `README.zh-CN.md`

## Positioning

The root README is a user onboarding page.

It should help a first-time reader understand:

- what OrbitOS is
- how to start using it
- how to download or clone it
- how to open it in Obsidian
- where the user should look every day
- where the system manual lives
- where agent and developer entry points are

It should not be the main place for internal protocol details, schema definitions, workflow internals, or implementation history.

Agents are not expected to read README as execution context. README may point users to `AGENTS.md`, but all Agent routing and constraints must live in `AGENTS.md`, rules, or workflows.

## Audience Order

Write for these readers in this order:

1. The user opening OrbitOS in Obsidian.
2. A person evaluating the GitHub repository.
3. A developer extending OrbitOS internals.

Internal implementation details belong in `.orbitos/`.

User-facing system explanations belong in `00-系统/`.

## Required Content

The README should include:

- a short explanation of OrbitOS
- the fastest start path:
  - download or clone the repository
  - open the repository folder as an Obsidian vault
  - put raw material into `01-收件箱/`
  - ask an agent to read `AGENTS.md` and run Startup Sync
- the main daily view:
  - `02-时间线/今日.md`
- the system manual entry:
  - `00-系统/00-开始使用.md`
  - `00-系统/01-目录说明.md`
  - `00-系统/02-日常协作.md`
  - `00-系统/03-内容生命周期.md`
  - `00-系统/04-Agent协作.md`
  - `00-系统/05-安全与边界.md`
  - `00-系统/06-术语表.md`
  - `00-系统/07-系统变更.md`
- a brief repository layout
- agent entry:
  - `AGENTS.md`
- developer entry:
  - `.orbitos/AGENTS.md`
  - `.orbitos/docs/`
  - `.orbitos/rules/`
- current status and next milestone
- license

## What To Avoid

Do not make the README a full system manual.

Avoid front-loading:

- schema field lists
- workflow step-by-step internals
- eval case details
- event log examples
- implementation changelog details
- long terminology tables

Point to `00-系统/` for user concepts.

Point to `.orbitos/` for internal implementation.

## Link Rules

`README.md` should use GitHub-friendly Markdown links.

`README.zh-CN.md` may use Obsidian wikilinks, but only for existing, human-readable Markdown files that the user should open in Obsidian.

Allowed wikilink targets include existing files under:

- `00-系统/`
- `02-时间线/`
- other visible user-facing Markdown areas when the target file already exists

Do not use wikilinks for:

- `.orbitos/`
- `.obsidian/`
- machine logs
- queues
- schemas
- scripts
- files that do not exist

Use plain code paths for internal files, for example:

```text
.orbitos/AGENTS.md
.orbitos/docs/ARCHITECTURE.md
.orbitos/rules/core/git-management.md
.orbitos/scripts/run-validation.ps1
```

This prevents Obsidian from creating blank files when a user clicks a link.

## Tone

The README should be practical and concise.

Prefer:

- "put material into `01-收件箱/`"
- "open `02-时间线/今日.md`"
- "ask the agent to run Startup Sync"

Avoid:

- over-explaining internal mechanics
- repeating the same entry points in multiple sections
- presenting OrbitOS as only a developer framework

## Maintenance Rule

When changing root README files, update this rule only if the expected README role or audience changes.

Routine content updates do not require changing this document.

