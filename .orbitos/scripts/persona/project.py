"""Dynamic Persona Layer — projections (#9 collaboration, #10 state + direction).

These functions project persona conclusions into derived views. Every projection
is explicitly derived from the persona source and must NOT become an independent
truth source. Stable baseline changes still require user confirmation elsewhere.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_source import PersonaSource  # noqa: E402

DERIVED_MARK = "（本块由动态人物档案主源自动投影，非独立真相；主源稳定基线改动需经用户确认）"
COLLAB_SECTION = "## 人物档案派生（投影）"


def _collect_direction_signals(source: PersonaSource) -> list[str]:
    keywords = ("输出", "方向", "内容", "项目", "知识", "候选", "值得", "信号", "闪光", "潜力")
    signals: list[str] = []
    for zone in ("confirmed", "hypotheses"):
        for line in (source.zones.get(zone) or "").splitlines():
            line = line.strip()
            if line.startswith("-") and any(k in line for k in keywords):
                signals.append(line.lstrip("- ").strip())
    return signals


def project_collaboration(source: PersonaSource, collab_path: Path) -> bool:
    """Append/update a derived collaboration block in the local collab prefs.

    Returns True if the file was modified.
    """
    collab_path = Path(collab_path)
    if not collab_path.is_file():
        return False

    bullets = []
    for zone in ("confirmed", "hypotheses"):
        for line in (source.zones.get(zone) or "").splitlines():
            line = line.strip()
            if line.startswith("-") and any(
                k in line for k in ("协作", "沟通", "节奏", "产出", "偏好")
            ):
                bullets.append(f"- {line.lstrip('- ').strip()}（派生，假设级，待行为证据复核）")

    if not bullets:
        return False

    block = COLLAB_SECTION + "\n\n" + DERIVED_MARK + "\n\n" + "\n".join(bullets) + "\n"
    text = collab_path.read_text(encoding="utf-8")
    if COLLAB_SECTION in text:
        # replace existing derived block up to the next '## ' heading (or EOF)
        new_text = re.sub(
            re.escape(COLLAB_SECTION) + r".*?(?=\n## )",
            block.rstrip("\n"),
            text,
            flags=re.DOTALL,
        )
    else:
        new_text = text.rstrip() + "\n\n" + block

    collab_path.write_text(new_text, encoding="utf-8")
    return True


def project_state(source: PersonaSource, out_path: Path) -> None:
    """Write a derived state-summary view (not the source of truth)."""
    out_path = Path(out_path)
    open_sugs = sum(
        1 for ln in (source.zones.get("suggestions") or "").splitlines()
        if ln.strip().startswith("-") and "状态：open" in ln
    )
    content = (
        "---\n"
        "title: 人物状态投影\n"
        "area: system\n"
        "purpose: persona-projection\n"
        "lifecycle: active\n"
        "tags:\n  - orbitos\n  - persona\n  - projection\n"
        "---\n\n"
        "# 人物状态投影（派生视图）\n\n"
        f"{DERIVED_MARK}\n\n"
        f"- MBTI 种子：{source.mbti_type}（可信度：{source.frontmatter.get('mbti_confidence')}）\n"
        f"- 基线状态：{source.baseline_status}\n"
        f"- 开放校准建议数：{open_sugs}\n"
        "- 说明：本视图只反映主源当前状态，不反向覆盖主源；稳定基线改动需经用户确认。\n"
    )
    out_path.write_text(content, encoding="utf-8")


def project_direction(source: PersonaSource, out_path: Path) -> int:
    """Route strong output-direction signals into a candidate view.

    Returns the number of routed signals.
    """
    out_path = Path(out_path)
    signals = _collect_direction_signals(source)
    if not signals:
        return 0
    bullets = "\n".join(f"- {s}" for s in signals)
    content = (
        "---\n"
        "title: 人物方向候选\n"
        "area: system\n"
        "purpose: persona-projection\n"
        "lifecycle: active\n"
        "tags:\n  - orbitos\n  - persona\n  - projection\n"
        "---\n\n"
        "# 人物方向候选（路由视图）\n\n"
        f"{DERIVED_MARK}\n\n"
        "以下信号值得考虑转为知识候选或项目候选（进入对应下游流，而非困在人物文档）：\n\n"
        f"{bullets}\n"
    )
    out_path.write_text(content, encoding="utf-8")
    return len(signals)


def run_projections(source, runtime: Path) -> bool:
    """Run all three projections from a loaded source or a source path."""
    if isinstance(source, (str, Path)):
        source = PersonaSource.load(Path(source))
    runtime = Path(runtime)
    if not source.is_source_of_truth():
        raise ValueError("target file is not marked as persona source_of_truth")
    changed = False
    changed |= project_collaboration(source, runtime / "00-系统" / "08-本地协作偏好.md")
    project_state(source, runtime / "00-系统" / "人物状态投影.md")
    project_direction(source, runtime / "00-系统" / "人物方向候选.md")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Project persona conclusions into views.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--runtime", required=True, help="OrbitOS runtime root")
    parser.add_argument("--all", action="store_true", help="run all projections")
    parser.add_argument("--collab", action="store_true")
    parser.add_argument("--state", action="store_true")
    parser.add_argument("--direction", action="store_true")
    args = parser.parse_args()

    source = PersonaSource.load(Path(args.source))
    runtime = Path(args.runtime)
    if not source.is_source_of_truth():
        raise ValueError("target file is not marked as persona source_of_truth")

    do_all = args.all or not (args.collab or args.state or args.direction)
    changed = False
    if args.collab or do_all:
        changed |= project_collaboration(
            source, runtime / "00-系统" / "08-本地协作偏好.md"
        )
    if args.state or do_all:
        project_state(source, runtime / "00-系统" / "人物状态投影.md")
    if args.direction or do_all:
        project_direction(source, runtime / "00-系统" / "人物方向候选.md")

    print(f"projections done (collab_modified={changed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
