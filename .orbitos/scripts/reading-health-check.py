#!/usr/bin/env python3
"""Read-only structural checks for the OrbitOS Reading Domain."""

import json
import re
import sys
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
READING = ROOT / "05-阅读"
BOOKS = READING / "books"
INSIGHT = READING / "insight"
DIMENSIONS = ("概念", "延伸", "你的故事", "闪回", "共振", "悬题")
INDEX_LINK = re.compile(r"\[\[([^\]|#]+)")


def remove_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    end = content.find("\n---\n", 4)
    return content[end + 5 :] if end >= 0 else content


def digest(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def add_issue(issues: list[dict], path: Path, message: str) -> None:
    issues.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "message": message})


def main() -> None:
    issues: list[dict] = []
    if not BOOKS.is_dir():
        add_issue(issues, READING, "books directory is missing")
    else:
        for book in sorted(path for path in BOOKS.iterdir() if path.is_dir()):
            progress = book / "progress.md"
            sidecar = book / ".orbitos-source.json"
            if not progress.is_file():
                add_issue(issues, book, "progress.md is missing")
            if not sidecar.is_file():
                add_issue(issues, book, ".orbitos-source.json is missing")
                continue
            try:
                source = json.loads(sidecar.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                add_issue(issues, sidecar, "source sidecar is not valid JSON")
                continue
            source_paths = []
            if isinstance(source, dict) and isinstance(source.get("inbox_path"), str):
                source_paths = [source["inbox_path"]]
            elif isinstance(source, dict) and isinstance(source.get("inbox_paths"), list):
                source_paths = source["inbox_paths"]
            if not source_paths or not all(isinstance(path, str) and path.startswith("01-收件箱/已入库/") for path in source_paths):
                add_issue(issues, sidecar, "source paths must point to 01-收件箱/已入库/")
            for inbox_path in source_paths:
                if not (ROOT / inbox_path).is_file():
                    add_issue(issues, sidecar, f"source path does not resolve to an existing file: {inbox_path}")
            required_fields = ("ingest_batch", "prepared_at")
            required_fields += ("source_name",) if source.get("source_kind") == "collection" else ("source_filename",)
            for field in required_fields:
                if not isinstance(source.get(field), str) or not source[field]:
                    add_issue(issues, sidecar, f"{field} is missing")

            if source.get("source_kind") == "collection":
                mappings = source.get("mappings")
                if not isinstance(mappings, list) or len(mappings) != len(source_paths):
                    add_issue(issues, sidecar, "collection mappings must match source paths")
                    continue
                for index, mapping in enumerate(mappings):
                    if not isinstance(mapping, dict):
                        add_issue(issues, sidecar, "collection mapping is invalid")
                        continue
                    chapter_id = mapping.get("chapter")
                    raw_path = book / str(chapter_id) / "raw.md"
                    source_path = ROOT / source_paths[index]
                    if not raw_path.is_file():
                        add_issue(issues, book, f"mapped raw file is missing: {chapter_id}/raw.md")
                        continue
                    if not source_path.is_file():
                        continue
                    source_body = remove_frontmatter(source_path.read_text(encoding="utf-8"))
                    raw_body = raw_path.read_text(encoding="utf-8")
                    if raw_body != source_body:
                        add_issue(issues, raw_path, "raw.md does not exactly match its source chapter after frontmatter removal")
                    if mapping.get("sha256") != digest(source_body):
                        add_issue(issues, sidecar, f"collection source checksum drift: {chapter_id}")

    index = INSIGHT / "INDEX.md"
    if not index.is_file():
        add_issue(issues, INSIGHT, "INDEX.md is missing")
    else:
        indexed = {match.group(1).replace("\\", "/") for match in INDEX_LINK.finditer(index.read_text(encoding="utf-8"))}
        actual = set()
        for dimension in DIMENSIONS:
            folder = INSIGHT / dimension
            if not folder.is_dir():
                add_issue(issues, INSIGHT, f"{dimension} directory is missing")
                continue
            for path in folder.glob("*.md"):
                actual.add(f"{dimension}/{path.stem}")
        for target in sorted(actual - indexed):
            add_issue(issues, index, f"Insight entry missing from INDEX.md: {target}")
        for target in sorted(indexed - actual):
            if "/" in target and target.split("/", 1)[0] in DIMENSIONS:
                add_issue(issues, index, f"INDEX.md points to a missing Insight: {target}")

    print(json.dumps({"status": "ok" if not issues else "issues", "issues": issues}, ensure_ascii=False, indent=2))
    sys.exit(0 if not issues else 1)


if __name__ == "__main__":
    main()
