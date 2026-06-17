import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TODAY = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().strftime("%Y-%m-%dT%H:%M")


def write_if_missing(relative_path, content):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return "exists", relative_path
    path.write_text(content, encoding="utf-8", newline="\n")
    return "created", relative_path


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
            "01-收件箱/粘贴.md",
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
            + "# 今日\n\n> 首次初始化。让 agent 执行 Startup Sync 后刷新这里。\n\n## 今日总览\n\n- 暂无。\n\n## 待确认\n\n见 [[待确认]]。\n\n## 下一步\n\n见 [[下一步]]。\n",
        )
    )
    results.append(
        write_if_missing(
            "02-时间线/待确认.md",
            timeline_frontmatter(title="待确认", today=TODAY, now=NOW)
            + "# 待确认\n\n- 暂无。\n",
        )
    )
    results.append(
        write_if_missing(
            "02-时间线/下一步.md",
            timeline_frontmatter(title="下一步", today=TODAY, now=NOW)
            + "# 下一步\n\n- 接入第一个 agent，并让它从 `AGENTS.md` 开始执行 Startup Sync。\n",
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

    for status, path in results:
        print(f"{status}: {path}")


if __name__ == "__main__":
    main()
