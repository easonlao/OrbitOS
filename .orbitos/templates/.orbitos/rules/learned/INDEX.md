# Learned Rules Index

Learned rules are usable rules extracted from agent experience.

They are not core rules. Agents may use them, but effects and evidence should be tracked.

## Table

| id | rule | scope | source_agents | evidence | status | last_used | result | core_candidate | reason |
|---|---|---|---|---|---|---|---|---|---|
| _empty_ | _No learned rules yet._ | _n/a_ | _n/a_ | _n/a_ | _n/a_ | _n/a_ | _n/a_ | _n/a_ | _n/a_ |

## Status

- `active`: usable by agents.
- `watching`: usable with caution; evidence is still thin.
- `conflict`: conflicts with a rule, event, or observed result.
- `deprecated`: no longer recommended.
- `promoted_to_core`: already moved into `.orbitos/rules/core/`.

## Rule Boundary

Keep each rule atomic.

Long explanations, examples, and evidence should stay in:

- `00-系统/agents/{agent_id}.md`
- `.orbitos/logs/events/`
- related workflow, skill, or design document

## Update Loop

1. Agent experience is recorded in the agent profile first.
2. Only generalized, atomic, executable, and traceable rules enter this table.
3. Agents may use learned rules and update `last_used`, `result`, and `evidence`.
4. Core promotion requires discussion with the user and explicit confirmation.
