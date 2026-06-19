#!/usr/bin/env python3
"""OrbitOS document consistency checker.

Scans visible Markdown files for:
1. Broken wikilinks (target file does not exist)
2. Legacy system paths (.orbit/, old filenames)

Usage:
    python run-doc-consistency.py [root_dir]
    python run-doc-consistency.py --help

Exit code: 0 if no issues, 1 if issues found.
"""

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Issue(NamedTuple):
    file: str
    line: int
    category: str
    detail: str


WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")

VISIBLE_MARKDOWN_DIRS = ["00-系统", "02-时间线"]
VISIBLE_MARKDOWN_FILES = ["AGENTS.md", "README.md", "README.zh-CN.md"]

LEGACY_PATTERNS = [
    (re.compile(r"(?<!\w)\.orbit/"), "legacy .orbit/ path"),
]

EXCLUDE_DIRS = {".orbitos", ".git", ".obsidian", ".mimocode", "node_modules"}
EXCLUDE_PATTERNS = ["00-系统/agents/*.md", "AGENTS.md"]


def find_visible_markdown(root: Path) -> list[Path]:
    files = []
    for name in VISIBLE_MARKDOWN_FILES:
        p = root / name
        if p.is_file():
            files.append(p)
    for dirname in VISIBLE_MARKDOWN_DIRS:
        dirpath = root / dirname
        if dirpath.is_dir():
            for md in sorted(dirpath.rglob("*.md")):
                if not any(part in EXCLUDE_DIRS for part in md.parts):
                    files.append(md)
    return files


def resolve_wikilink_target(source_file: Path, link_target: str, root: Path) -> Path | None:
    target = link_target.strip()
    if target.startswith("/"):
        return root / target.lstrip("/")

    source_dir = source_file.parent
    candidate = source_dir / target
    if candidate.is_file():
        return candidate
    if candidate.with_suffix(".md").is_file():
        return candidate.with_suffix(".md")

    candidate = root / target
    if candidate.is_file():
        return candidate
    if candidate.with_suffix(".md").is_file():
        return candidate.with_suffix(".md")

    return None


def check_broken_wikilinks(files: list[Path], root: Path) -> list[Issue]:
    issues = []
    for filepath in files:
        if is_excluded(filepath, root):
            continue
        rel = filepath.relative_to(root)
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue
        in_code_block = False
        for line_num, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            for match in WIKILINK_PATTERN.finditer(line):
                link_target = match.group(1)
                if link_target.startswith(".orbitos/") or link_target.startswith(".orbit/"):
                    continue
                resolved = resolve_wikilink_target(filepath, link_target, root)
                if resolved is None:
                    issues.append(Issue(
                        file=str(rel),
                        line=line_num,
                        category="broken-wikilink",
                        detail=f"target '{link_target}' not found",
                    ))
    return issues


def is_excluded(filepath: Path, root: Path) -> bool:
    rel = filepath.relative_to(root)
    rel_str = str(rel).replace("\\", "/")
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(rel_str, pat):
            return True
    return False


def check_legacy_paths(files: list[Path], root: Path) -> list[Issue]:
    issues = []
    for filepath in files:
        if is_excluded(filepath, root):
            continue
        rel = filepath.relative_to(root)
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue
        in_code_block = False
        for line_num, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            for pattern, desc in LEGACY_PATTERNS:
                if pattern.search(line):
                    issues.append(Issue(
                        file=str(rel),
                        line=line_num,
                        category="legacy-path",
                        detail=desc,
                    ))
    return issues


def main():
    parser = argparse.ArgumentParser(description="OrbitOS document consistency checker")
    parser.add_argument("root_dir", nargs="?", default=".", help="OrbitOS root directory")
    args = parser.parse_args()

    root = Path(args.root_dir).resolve()
    if not (root / ".orbitos").is_dir():
        print(f"Error: {root} does not look like an OrbitOS root (no .orbitos/ dir)")
        sys.exit(2)

    files = find_visible_markdown(root)
    print(f"Scanning {len(files)} visible Markdown files in {root}")

    issues = []
    issues.extend(check_broken_wikilinks(files, root))
    issues.extend(check_legacy_paths(files, root))

    if not issues:
        print("PASS: No document consistency issues found.")
        sys.exit(0)

    print(f"\nFAIL: {len(issues)} issue(s) found:\n")
    by_category = {}
    for issue in issues:
        by_category.setdefault(issue.category, []).append(issue)

    for category, cat_issues in sorted(by_category.items()):
        print(f"## {category} ({len(cat_issues)})")
        for issue in cat_issues:
            print(f"  {issue.file}:{issue.line} — {issue.detail}")
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
