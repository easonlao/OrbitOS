# OrbitOS Requirements

## Core Need

OrbitOS is a multi-agent collaboration brain. It is not a traditional personal knowledge base.

The user wants different agents to collaborate through one workspace, leave traceable work, and produce Obsidian-readable artifacts.

## Confirmed Requirements

- Obsidian is the human reading and review interface.
- Agents may include Hermes, HanaAgent, Codex, Claude Code, and others.
- Root `AGENTS.md` is the single usage entry.
- `AGENTS.md` must stay under 200 lines.
- Use progressive disclosure: agents load only necessary context.
- Agent work must be traceable through event logs.
- Startup Sync runs when an agent enters OrbitOS.
- Progress Sync runs after substantial work or when the user asks to sync progress.
- Human-facing Markdown and machine logs are separate.
- Knowledge cards must be confirmed/reviewed and should remain few but high quality.
- Hindsight is optional and not the OrbitOS fact base.

## Human Reading Requirements

- Top-level vault structure should serve Obsidian reading habits.
- Visible Markdown should be focused, linked, and not bloated.
- Wikilinks should connect small documents rather than creating monolithic manuals.

## Deferred

- Detailed Hindsight Bridge protocol
- Role card schema
- Thinking mode library
- Workflow schema details
