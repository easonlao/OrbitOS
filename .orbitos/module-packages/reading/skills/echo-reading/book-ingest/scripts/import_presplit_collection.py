#!/usr/bin/env python3
"""Import an already split Markdown collection into the book-ingest layout."""

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path


def remove_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    end = content.find("\n---\n", 4)
    return content[end + 5 :] if end >= 0 else content


def checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def inbox_relative(path: Path) -> str:
    parts = path.parts
    try:
        start = parts.index("01-收件箱")
    except ValueError as error:
        raise ValueError(f"source is outside the inbox: {path}") from error
    return Path(*parts[start:]).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--book", required=True)
    parser.add_argument("--chapter", action="append", required=True, help="relative Markdown path in reading order")
    parser.add_argument("--ingest-batch", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    root = Path(args.root).resolve()
    if not source_dir.is_dir():
        sys.exit("source-dir must be an existing directory")
    if "01-收件箱" not in source_dir.parts or "已入库" not in source_dir.parts:
        sys.exit("source-dir must be an already ingested collection")

    book_dir = root / "books" / args.book
    if book_dir.exists():
        sys.exit(f"book directory already exists: {book_dir}")

    chapters = []
    for index, relative in enumerate(args.chapter, 1):
        source_path = (source_dir / relative).resolve()
        try:
            source_path.relative_to(source_dir)
        except ValueError:
            sys.exit(f"chapter escapes source-dir: {relative}")
        if not source_path.is_file() or source_path.suffix.lower() not in {".md", ".markdown"}:
            sys.exit(f"chapter must be an existing Markdown file: {relative}")
        content = remove_frontmatter(source_path.read_text(encoding="utf-8"))
        if not content.strip():
            sys.exit(f"chapter is empty after frontmatter removal: {relative}")
        heading = re.search(r"^#\s+(.+?)\s*$", content, re.MULTILINE)
        title = heading.group(1).strip() if heading else source_path.stem
        chapters.append({"source": source_path, "relative": relative.replace("\\", "/"), "content": content, "title": title})

    pad = max(2, len(str(len(chapters))))
    book_dir.mkdir(parents=True)
    source_paths = []
    mappings = []
    progress = [f"# 《{args.book}》阅读进度", "", f"底本:已拆章节集合（共 {len(chapters)} 章,保留原有顺序）", ""]
    for index, chapter in enumerate(chapters, 1):
        chapter_id = f"ch{index:0{pad}d}"
        raw_path = book_dir / chapter_id / "raw.md"
        raw_path.parent.mkdir(parents=True)
        raw_path.write_text(chapter["content"], encoding="utf-8", newline="\n")
        written = raw_path.read_text(encoding="utf-8")
        if checksum(written) != checksum(chapter["content"]):
            sys.exit(f"raw verification failed: {chapter['relative']}")
        source_paths.append(inbox_relative(chapter["source"]))
        mappings.append({"chapter": chapter_id, "source": chapter["relative"], "sha256": checksum(chapter["content"])})
        progress.append(f"- [ ] {chapter_id} — {chapter['title']}")

    (book_dir / "progress.md").write_text("\n".join(progress) + "\n", encoding="utf-8", newline="\n")
    (book_dir / ".orbitos-source.json").write_text(
        json.dumps(
            {
                "version": 1,
                "source_kind": "collection",
                "inbox_paths": source_paths,
                "ingest_batch": args.ingest_batch,
                "source_name": args.book,
                "prepared_at": date.today().isoformat(),
                "mappings": mappings,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "ok", "book": str(book_dir), "chapters": len(chapters)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
