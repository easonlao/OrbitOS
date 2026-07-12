#!/usr/bin/env python3
"""Read-only inbox scan for likely reading material."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "01-收件箱"
BOOK_EXTENSIONS = {".epub", ".mobi", ".azw", ".azw3", ".prc"}
TEXT_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt", ".docx"}
MIN_LONG_FORM_BYTES = 24 * 1024


def main() -> None:
    candidates = []
    if INBOX.is_dir():
        for path in sorted(INBOX.iterdir()):
            if not path.is_file() or path.name == "00-粘贴.md" or path.name.startswith("."):
                continue
            suffix = path.suffix.lower()
            if suffix in BOOK_EXTENSIONS:
                reason = "ebook format"
            elif suffix in TEXT_EXTENSIONS and path.stat().st_size >= MIN_LONG_FORM_BYTES:
                reason = "long-form text-like file"
            else:
                continue
            candidates.append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "kind": suffix.lstrip("."),
                "bytes": path.stat().st_size,
                "reason": reason,
            })
    print(json.dumps({"status": "ok", "candidates": candidates}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
