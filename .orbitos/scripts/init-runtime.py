import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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

    registry = {
        "version": 1,
        "updated": TODAY,
        "agents": []
    }
    results.append(
        write_if_missing(
            ".orbitos/agents/registry.yaml",
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        )
    )

    results.append(
        write_if_missing(
            "01-收件箱/00-粘贴.md",
            "# 粘贴\n\n把临时想丢进 OrbitOS 的文字、链接、摘录或待整理材料贴在这里。\n\n这里不要求 frontmatter。agent 处理时应保留原始输入，不直接把内容改写成知识卡片；确认后的处理结果再进入对应区域。\n",
        )
    )

    timeline_frontmatter = """---
title: {title}
area: timeline
purpose: status
lifecycle: active
created: {today}
updated: {now}
tags:
  - orbitos
  - timeline
---

""".format

    results.append(
        write_if_missing(
            "02-时间线/今日.md",
            timeline_frontmatter(title="今日", today=TODAY, now=NOW)
            + "# 今日\n\n> 首次初始化。让 agent 执行 Startup Sync 后刷新这里。\n\n## 当前判断\n\n- 第一次使用时，先让 agent 执行 Startup Sync。\n- 如果 agent 尚未注册，它应停止并请求你确认 `agent_id` 和部署信息。\n\n## 当前待确认\n\n- 首次使用时，通常需要先确认第一个 agent 的注册信息。\n\n## 今日进展\n\n- 暂无。由 Progress Sync 写入当天关键事实。\n\n## 可继续\n\n- 注册第一个 agent。\n- 把材料放入 `01-收件箱/`。\n- 让 agent 执行 Progress Sync，刷新当前状态。\n\n## 来源\n\n- 机器事实记录保存在 `.orbitos/logs/events/`。\n- 本周回顾见 [[本周]]。\n",
        )
    )
    results.append(
        write_if_missing(
            "02-时间线/本周.md",
            timeline_frontmatter(title="本周", today=TODAY, now=NOW)
            + "# 本周\n\n> 本周视图由 weekly-review workflow 更新。\n\n## 本周方向\n\n- 暂无。\n",
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
            "---\ntitle: Learned Rules Index\narea: internal\npurpose: rules\nlifecycle: active\ncreated: {today}\nupdated: {now}\ntags:\n  - orbitos\n  - rules\n---\n\n# Learned Rules Index\n\n> 本地 learned rules 汇总。core rule 提升必须经过用户确认。\n\n暂无。\n".format(today=TODAY, now=NOW),
        )
    )
    results.append(ensure_local_excludes(ROOT))

    for status, path in results:
        print(f"{status}: {path}")


if __name__ == "__main__":
    main()
