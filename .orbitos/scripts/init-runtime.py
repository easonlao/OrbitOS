import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = ROOT / ".orbitos/templates"
TODAY = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().strftime("%Y-%m-%dT%H:%M")
LOCAL_EXCLUDE_PATTERNS = [
    ".mimocode/",
    ".nova/",
]
LOCAL_EXCLUDE_HEADER = "# OrbitOS runtime-local excludes"


def write_if_missing(relative_path, content):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return "exists", relative_path
    path.write_text(content, encoding="utf-8", newline="\n")
    return "created", relative_path


def read_template(relative_path):
    return (TEMPLATE_ROOT / relative_path).read_text(encoding="utf-8")


def resolve_git_dir(root: Path) -> Path | None:
    git_path = root / ".git"
    if git_path.is_dir():
        return git_path
    if git_path.is_file():
        content = git_path.read_text(encoding="utf-8").strip()
        prefix = "gitdir:"
        if content.lower().startswith(prefix):
            git_dir = content[len(prefix):].strip()
            return (root / git_dir).resolve()
    return None


def ensure_local_excludes(root: Path) -> tuple[str, str]:
    git_dir = resolve_git_dir(root)
    if git_dir is None:
        return "skipped", ".git/info/exclude (git metadata unavailable)"

    info_dir = git_dir / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    exclude_path = info_dir / "exclude"
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""

    begin_marker = f"{LOCAL_EXCLUDE_HEADER} BEGIN"
    end_marker = f"{LOCAL_EXCLUDE_HEADER} END"
    managed_block = (
        f"{begin_marker}\n"
        "# Runtime-local agent workdirs and sandbox state.\n"
        + "".join(f"{pattern}\n" for pattern in LOCAL_EXCLUDE_PATTERNS)
        + f"{end_marker}\n"
    )

    if begin_marker in existing and end_marker in existing:
        start = existing.index(begin_marker)
        end = existing.index(end_marker) + len(end_marker)
        replacement = managed_block.rstrip("\n")
        new_content = existing[:start] + replacement + existing[end:]
        if not new_content.endswith("\n"):
            new_content += "\n"
    else:
        prefix = existing
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        if prefix and not prefix.endswith("\n\n"):
            prefix += "\n"
        new_content = prefix + managed_block

    if new_content == existing:
        return "exists", ".git/info/exclude"

    exclude_path.write_text(new_content, encoding="utf-8", newline="\n")
    return "updated", ".git/info/exclude"


def main():
    results = []

    results.append(
        write_if_missing(
            ".orbitos/agents/registry.yaml",
            read_template(".orbitos/agents/registry.yaml"),
        )
    )

    results.append(
        write_if_missing(
            "01-收件箱/00-粘贴.md",
            read_template("01-收件箱/00-粘贴.md"),
        )
    )

    results.append(
        write_if_missing(
            "02-时间线/今日.md",
            read_template("02-时间线/今日.md"),
        )
    )
    results.append(
        write_if_missing(
            "02-时间线/本周.md",
            read_template("02-时间线/本周.md"),
        )
    )

    results.append(
        write_if_missing(
            "03-项目/MAP.md",
            "---\ntitle: 项目地图\narea: project\npurpose: navigation\nlifecycle: active\ncreated: {today}\nupdated: {now}\ntags:\n  - orbitos\n  - project\n---\n\n# 项目地图\n\n- 暂无项目。\n".format(today=TODAY, now=NOW),
        )
    )
    results.append(
        write_if_missing(
            "04-知识/MAP.md",
            "---\ntitle: 知识地图\narea: knowledge\npurpose: navigation\nlifecycle: active\ncreated: {today}\nupdated: {now}\ntags:\n  - orbitos\n  - knowledge\n---\n\n# 知识地图\n\n- 暂无知识卡片。\n".format(today=TODAY, now=NOW),
        )
    )
    results.append(
        write_if_missing(
            ".orbitos/rules/learned/INDEX.md",
            read_template(".orbitos/rules/learned/INDEX.md"),
        )
    )
    results.append(ensure_local_excludes(ROOT))

    for status, path in results:
        print(f"{status}: {path}")


if __name__ == "__main__":
    main()
