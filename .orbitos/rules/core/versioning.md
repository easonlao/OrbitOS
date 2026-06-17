# Versioning, Commit, and Release Rule

This rule defines OrbitOS versioning, commit, changelog, and release behavior.

## Version Format

OrbitOS uses three-part versions:

```text
vMAJOR.MINOR.PATCH
```

Example:

```text
v0.1.0
```

## Version Levels

### MAJOR

Increment MAJOR when OrbitOS changes in a way that breaks existing usage or agent behavior.

Examples:

- root `AGENTS.md` entry contract changes incompatibly
- directory responsibilities are redefined
- lifecycle states are renamed or removed
- event/schema contracts break existing logs or workflows
- user-visible operating model changes substantially

### MINOR

Increment MINOR when OrbitOS gains a meaningful new capability while remaining compatible.

Examples:

- new schema or workflow
- new agent integration pattern
- new Dashboard projection
- new validation/eval coverage
- new documented system rule that extends behavior

### PATCH

Increment PATCH for compatible fixes and clarifications.

Examples:

- typo or wording fixes
- README clarification
- small workflow correction
- eval/script bugfix that does not change the protocol
- changelog or documentation cleanup

## Current Version

Current release:

```text
v0.1.0
```

Meaning:

OrbitOS has a working system baseline: workspace skeleton, user README, Dashboard semantics, strict schemas, validation workflow, inbox triage workflow, core-change workflow, eval script, and documentation promotion rules.

## Changelog Layers

OrbitOS keeps two changelog layers.

### Full Internal Changelog

Path:

```text
.orbitos/CHANGELOG.md
```

Purpose:

- full release history
- detailed change groups
- implementation and protocol changes
- migration notes
- validation notes
- prior releases

This is the source of truth for release history.

### User-Facing Current Release Changelog

Path:

```text
00-系统/07-系统变更.md
```

Purpose:

- show only the current release summary
- keep Obsidian reading lightweight
- point to `.orbitos/CHANGELOG.md` for full history

Do not copy all historical release notes into `00-系统/07-系统变更.md`.

## Commit Rules

Use concise commit messages with a type prefix:

```text
type(scope): summary
```

Recommended types:

- `feat`: new capability
- `fix`: bug fix
- `docs`: documentation-only change
- `schema`: schema change
- `workflow`: workflow change
- `eval`: validation/eval change
- `refactor`: internal restructuring without behavior change
- `release`: version/changelog/tag preparation

Examples:

```text
schema(core): add core-change validation contract
docs(readme): rewrite README as user onboarding entry
release: prepare v0.1.0
```

## Release Flow

When preparing a release:

1. Run Startup Sync.
2. Read `.orbitos/AGENTS.md`.
3. Read this rule.
4. Review changed files and event logs since the previous release.
5. Decide version bump: MAJOR, MINOR, or PATCH.
6. Run validation:

```powershell
pwsh -ExecutionPolicy Bypass -File .orbitos/scripts/run-validation.ps1
```

7. Run the Runtime integration test:

```bash
python .orbitos/tests/test_runtime.py
```

Validation and the Runtime integration test must both pass before commit or push.

8. Update `.orbitos/CHANGELOG.md` with full release notes.
9. Update `00-系统/07-系统变更.md` with only the current release summary.
10. Write a release event under `.orbitos/logs/events/`.
11. Commit with a release commit message.
12. Create a git tag:

```bash
git tag vX.Y.Z
```

13. Push commit and tag:

```bash
git push
git push origin vX.Y.Z
```

## Release Notes Structure

Use this structure in `.orbitos/CHANGELOG.md`:

```markdown
## vX.Y.Z - YYYY-MM-DD

### Summary

### Added

### Changed

### Fixed

### Validation

### Migration Notes
```

`00-系统/07-系统变更.md` should use a shorter structure:

```markdown
# 系统变更记录

## 当前版本：vX.Y.Z

### 你需要知道的变化

### 下一步

### 完整历史
```

## Agent Requirements

Agents preparing version or release changes must:

- follow `.orbitos/workflows/core-change.md`
- validate core changes against `.orbitos/schemas/core-change.schema.yaml`
- update `.orbitos/CHANGELOG.md`
- update `00-系统/07-系统变更.md`
- write an event log
- run `.orbitos/tests/test_runtime.py` and stop if it fails
- not create git commits or tags unless the user explicitly asks

