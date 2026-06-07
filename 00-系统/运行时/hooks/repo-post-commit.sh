#!/bin/sh
# OrbitOS portable repo post-commit hook.
# Source of truth: 00-系统/运行时/hooks/repo-post-commit.sh
VAULT="E:\SynologyDrive\OrbitOS"
SCRIPT="E:\SynologyDrive\OrbitOS\00-系统\Skills\orbit-vault\scripts\orbit-vault.mjs"
NODE_BIN="$(command -v node 2>/dev/null)"
[ -n "$NODE_BIN" ] || exit 0
[ -f "$SCRIPT" ] || exit 0
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
"$NODE_BIN" "$SCRIPT" record-git-commit-event --vault "$VAULT" --repo "$REPO_ROOT" >/dev/null 2>&1 || true
exit 0
