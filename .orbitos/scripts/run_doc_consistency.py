#!/usr/bin/env python3
"""OrbitOS document consistency checker.

Scans visible Markdown files for:
1. Broken wikilinks (target file does not exist)
2. Legacy system paths and directory numbers
3. Statements that contradict stable document boundaries

Usage:
    python run_doc_consistency.py [root_dir]
    python run_doc_consistency.py --help

Exit code: 0 if no issues, 1 if issues found.
"""

import argparse
import fnmatch
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
    (re.compile(r"(?<!\w)\.orbit[\\/]"), "legacy .orbit/ path"),
    (re.compile(r"(?<![\w-])02-日记[\\/]"), "legacy 02-日记/ directory"),
    (re.compile(r"(?<![\w-])03-知识[\\/]"), "legacy 03-知识/ directory"),
    (re.compile(r"(?<![\w-])04-项目[\\/]"), "legacy 04-项目/ directory"),
]

FORBIDDEN_STATEMENTS = [
    (
        re.compile(r"Hindsight\s+是\s+OrbitOS(?:\s*的)?(?:\s*运行)?\s*(?:必需项|必需依赖|事实底座)", re.IGNORECASE),
        "Hindsight is optional and must not be described as an OrbitOS dependency or fact base",
    ),
    (
        re.compile(r"(?:`?02-时间线/今日\.md`?|`?今日\.md`?)\s*是\s*项目(?:的)?(?:唯一)?状态源", re.IGNORECASE),
        "project STATUS.md, not 今日.md, is the project state source",
    ),
    (
        re.compile(r"(?:`?\.orbitos/logs/events/`?|Event)\s+是\s+(?:OrbitOS(?:\s*的)?\s*)?唯一事实底座", re.IGNORECASE),
        "events are operation evidence, not the only fact base",
    ),
    (
        re.compile(r"Active knowledge\s*(?:可以|可)\s*直接(?:进行)?语义修改", re.IGNORECASE),
        "active knowledge must return to draft before semantic changes",
    ),
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


def iter_prose_lines(filepath: Path):
    """Yield non-fenced Markdown lines with one-based line numbers."""
    content = filepath.read_text(encoding="utf-8")
    in_code_block = False
    for line_num, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            yield line_num, line


def check_legacy_paths(files: list[Path], root: Path) -> list[Issue]:
    issues = []
    for filepath in files:
        if is_excluded(filepath, root):
            continue
        rel = filepath.relative_to(root)
        try:
            lines = iter_prose_lines(filepath)
            for line_num, line in lines:
                for pattern, desc in LEGACY_PATTERNS:
                    if pattern.search(line):
                        issues.append(Issue(
                            file=str(rel),
                            line=line_num,
                            category="legacy-path",
                            detail=desc,
                        ))
        except (OSError, UnicodeError):
            continue
    return issues


def check_forbidden_statements(files: list[Path], root: Path) -> list[Issue]:
    issues = []
    for filepath in files:
        if is_excluded(filepath, root):
            continue
        rel = filepath.relative_to(root)
        try:
            for line_num, line in iter_prose_lines(filepath):
                for pattern, desc in FORBIDDEN_STATEMENTS:
                    if pattern.search(line):
                        issues.append(Issue(
                            file=str(rel),
                            line=line_num,
                            category="boundary-conflict",
                            detail=desc,
                        ))
        except (OSError, UnicodeError):
            continue
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
    issues.extend(check_forbidden_statements(files, root))

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
