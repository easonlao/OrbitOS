"""Dynamic Persona Layer — first-run baseline flow (#7).

Collects the minimum information to initialize the persona source and generates
an MBTI-based seed. The MBTI result is stored explicitly but treated as a
hypothesis (default preference assumptions), never as final truth.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_source import PersonaSource  # noqa: E402
import mbti  # noqa: E402


def _render_hypotheses(hyps: list[dict]) -> str:
    lines = []
    for h in hyps:
        lines.append(
            f"- [{h['id']}] {h['statement']} "
            f"（derived_from={h['derived_from']}, confidence={h['confidence']}）"
        )
    return "\n".join(lines)


def build_baseline(
    source_path: Path,
    identity: str,
    answers: dict[str, str] | None = None,
    created: str | None = None,
    updated: str | None = None,
) -> PersonaSource:
    today = (_dt.date.today().isoformat())
    created = created or today
    updated = updated or today

    source = PersonaSource()
    source.frontmatter = {
        "title": "动态人物档案",
        "area": "system",
        "purpose": "persona",
        "lifecycle": "draft",
        "created": created,
        "updated": updated,
        "tags": ["orbitos", "persona", "runtime-local"],
        "source_of_truth": True,
    }

    if answers:
        result = mbti.score(answers)
        mbti_type = result["type"]
        source.frontmatter["mbti_type"] = mbti_type
        source.frontmatter["mbti_confidence"] = "hypothesis"
        source.frontmatter["baseline_status"] = "seeded"
        type_note = (
            f"MBTI 种子类型：{mbti_type}（{mbti.explain(mbti_type)}）。"
            f"这只是一个低成本、强可读的初始定调入口，不是终局真相；"
            f"后续真实行为证据优先于该假设，个体差异可覆盖类型假设。"
            + (f" 注：维度 {','.join(result['ties'])} 平票，按保守默认处理，可信度更低。"
               if result["ties"] else "")
        )
        hyps = mbti.derive_hypotheses(mbti_type)
        source.zones["baseline"] = f"- 稳定底色：{identity}\n\n{type_note}"
        source.zones["hypotheses"] = _render_hypotheses(hyps)
        source.zones["confirmed"] = "（暂无；待行为证据支撑后填入）"
        source.zones["suggestions"] = "（暂无）"
    else:
        source.frontmatter["mbti_type"] = None
        source.frontmatter["mbti_confidence"] = "hypothesis"
        source.frontmatter["baseline_status"] = "pending"
        source.zones["baseline"] = f"- 稳定底色：{identity}\n\n（待首次基线问卷生成 MBTI 种子）"
        source.zones["hypotheses"] = "（待生成）"
        source.zones["confirmed"] = "（暂无）"
        source.zones["suggestions"] = "（暂无）"

    source.save(Path(source_path))
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the dynamic persona baseline seed.")
    parser.add_argument("--source", required=True, help="path to the persona source Markdown")
    parser.add_argument("--identity", default="（待填写）", help="one-line stable self description")
    parser.add_argument("--answers", help="path to JSON file mapping question_id -> 'a'|'b'")
    parser.add_argument("--created", help="ISO date for created field (default today)")
    parser.add_argument("--updated", help="ISO date for updated field (default today)")
    args = parser.parse_args()

    answers = None
    if args.answers:
        answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))

    source = build_baseline(
        Path(args.source), args.identity, answers, args.created, args.updated
    )
    status = source.baseline_status
    print(f"baseline written: {args.source} (status={status}, mbti={source.mbti_type})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
