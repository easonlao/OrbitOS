---
title: Git Management Rule
area: internal
purpose: rule
lifecycle: active
created: 2026-06-12
updated: 2026-06-13
tags:
  - orbitos
  - git
  - agent-rule
---

# Git Management Rule

This rule defines how agents keep the public Git repository separate from local OrbitOS user data.

## Repository Boundary

The public repository should contain:

- OrbitOS system skeleton
- root `AGENTS.md`
- root README files
- `00-系统/` user manual
- `02-时间线/` dashboard templates and current visible status
- `.orbitos/AGENTS.md`
- `.orbitos/docs/`
- `.orbitos/rules/core/`
- `.orbitos/schemas/`
- `.orbitos/workflows/`
- `.orbitos/scripts/`
- `.orbitos/evals/`
- directory `.gitkeep` files

The public repository should not contain:

- raw inbox content
- personal notes
- processed resource files
- Obsidian output drafts
- archived local vault snapshots
- OH-Works runtime output
- `.obsidian/`, `.claude/`, `.codex/`
- `.orbitos/cache/`
- `.orbitos/logs/` runtime files
- `.orbitos/queues/` runtime files
- `.orbitos/state/` runtime files

## Before Creating Files

Before an agent creates a new top-level directory or a new category of generated files, it must decide:

1. Is this public system material?
2. Is this local user data?
3. Is this runtime state?
4. Should the directory be represented in Git only by `.gitkeep`?

If the answer is local user data or runtime state, update `.gitignore` before creating or staging those files.

## Runtime-Only Content

When a file or directory exists in the Runtime working copy but is not part of the Product Repo definition, treat it as a local-only candidate by default.

Examples:

- agent private working directories such as `.codex/`, `.mimocode/`, `.claude/`
- local app state such as `.obsidian/`
- caches, session files, indexes, logs, temporary outputs

This is a default boundary signal, not an automatic rule.

Agents must still ask:

1. Is this clearly runtime-only state?
2. Or is this new product/system content created for the current task?

Use the result:

- if it is clearly runtime-only state, add it to `.gitignore`
- if it is intentional new product/system content, do not ignore it; stage it into the Product Repo instead

Do not use broad patterns like `.*` to ignore all hidden files or directories. OrbitOS system content includes required dot-paths such as `.orbitos/` and `.gitignore`, so hidden-path handling must stay explicit.

## Common Placement

- User input goes under `01-收件箱/` and is ignored by Git except `.gitkeep`.
- Project implementation content goes under `03-项目/` and is ignored by Git except `03-项目/MAP.md`.
- Confirmed knowledge may live under `04-知识/`, but the default Git rule still ignores the area except `04-知识/MAP.md`.
- Processed references go under `05-资源/` and are ignored by Git except `.gitkeep` files.
- Obsidian outputs go under `06-输出/` and are ignored by Git except `.gitkeep`.
- Archives go under `99-归档/` and are ignored by Git except `.gitkeep`.
- Runtime facts go under `.orbitos/logs/` and are ignored by Git except directory placeholders.

## When Untracking Existing Files

If private files are already tracked, `.gitignore` is not enough.

Use:

```powershell
git rm -r --cached -- <path>
```

This removes files from the Git index while keeping local files on disk.

After that, add back required placeholders:

```powershell
git add -f -- <path>/.gitkeep
```

## Commit Review

Before committing, run:

```powershell
git status --short
git ls-files -- 01-收件箱 05-资源 06-输出 99-归档 OH-Works .orbitos/logs/events
git check-ignore -v <sample-private-file>
```

Expected result:

- private content paths are not listed by `git ls-files`
- only `.gitkeep` remains tracked in ignored content directories
- sample private files are matched by `.gitignore`

## History Warning

Removing files from the Git index prevents future commits from carrying them.

It does not remove files from existing Git history. If sensitive content has already been pushed, use a separate history rewrite procedure such as `git filter-repo` or BFG, then force-push with explicit approval.

