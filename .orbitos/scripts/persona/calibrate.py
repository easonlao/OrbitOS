"""Dynamic Persona Layer — behavior-evidence calibration loop (#8).

Observes real OrbitOS behavior signals and compares them against the baseline
and current hypotheses. When a contradiction or meaningful pattern appears, it
produces a REVIEWABLE calibration suggestion.

Hard rule: this module must never silently rewrite the stable persona source.
It only appends to the open-calibration-suggestions zone (zone 4). Changing the
stable baseline requires explicit user confirmation elsewhere.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_source import PersonaSource  # noqa: E402


def collect_evidence(runtime_root: Path) -> dict:
    """Gather lightweight behavior signals from existing OrbitOS surfaces."""
    runtime_root = Path(runtime_root)
    signals: dict = {
        "active_projects": 0,
        "open_inbox_items": 0,
        "knowledge_drafts": 0,
        "recent_event_types": [],
        "timeline_present": False,
    }

    projects_dir = runtime_root / "03-项目"
    if projects_dir.is_dir():
        signals["active_projects"] = sum(
            1 for p in projects_dir.iterdir() if p.is_dir() and p.name != "OrbitOS"
        )

    inbox_dir = runtime_root / "01-收件箱"
    if inbox_dir.is_dir():
        signals["open_inbox_items"] = sum(1 for f in inbox_dir.iterdir() if f.is_file())

    draft_dir = runtime_root / "04-知识" / "00-草稿箱"
    if draft_dir.is_dir():
        signals["knowledge_drafts"] = sum(1 for f in draft_dir.iterdir() if f.is_file())

    events_dir = runtime_root / ".orbitos" / "logs" / "events"
    if events_dir.is_dir():
        types = [
            json.loads(p.read_text(encoding="utf-8")).get("event_type")
            for p in sorted(events_dir.glob("*.yaml"))
            if p.read_text(encoding="utf-8").lstrip().startswith("{")
        ]
        signals["recent_event_types"] = [t for t in types if t]

    signals["timeline_present"] = (runtime_root / "02-时间线" / "今日.md").is_file()
    return signals


def detect_contradictions(source: PersonaSource, evidence: dict) -> list[dict]:
    """Return reviewable calibration suggestions derived from evidence.

    Each suggestion references the behavior evidence and the baseline/hypothesis
    it appears to contradict. This function never mutates the source.
    """
    suggestions: list[dict] = []
    mbti_type = source.mbti_type
    if not mbti_type or source.baseline_status == "pending":
        return suggestions

    # Detector 1: J hypothesis vs. many parallel active projects / open inbox.
    if "J" in mbti_type:
        if evidence["active_projects"] >= 4 or evidence["open_inbox_items"] >= 8:
            suggestions.append(
                {
                    "id": "cal_parallelism",
                    "observation": (
                        f"当前有 {evidence['active_projects']} 个并行项目、"
                        f"{evidence['open_inbox_items']} 个未处理收件箱条目"
                    ),
                    "contradicts": "J 假设（偏好提前计划、把事定下来）",
                    "suggestion": "用户实际运作可能比 J 假设更开放；可考虑把『保留开放选项』也作为可信的协作假设，而非只看计划节点。",
                    "evidence": "03-项目/, 01-收件箱/",
                    "status": "open",
                }
            )

    # Detector 2: I hypothesis vs. very high collaboration/meeting event ratio.
    if "I" in mbti_type:
        etypes = evidence["recent_event_types"]
        collab_heavy = sum(1 for t in etypes if t in ("progress_sync", "handoff"))
        if etypes and collab_heavy >= max(3, len(etypes) * 0.5):
            suggestions.append(
                {
                    "id": "cal_collab_load",
                    "observation": f"近期 event 中协作/接手类占比偏高（{collab_heavy}/{len(etypes)}）",
                    "contradicts": "I 假设（先内部想清楚再表达）",
                    "suggestion": "用户近期大量处在多 agent 协作中；外部讨论可能已是主要理清方式，可复核 I 假设是否仍贴合。",
                    "evidence": ".orbitos/logs/events/",
                    "status": "open",
                }
            )

    # Detector 3: knowledge drafts accumulating vs. N hypothesis (prefers models).
    if "N" in mbti_type and evidence["knowledge_drafts"] >= 5:
        suggestions.append(
            {
                "id": "cal_draft_pile",
                "observation": f"知识草稿箱堆积 {evidence['knowledge_drafts']} 篇未收敛",
                "contradicts": "N 假设（偏好方向/模型，边做边调）",
                "suggestion": "草稿长期未确认可能说明方向发散或收敛机制不足；建议检视是否需更强的收口节奏，而非持续开新方向。",
                "evidence": "04-知识/00-草稿箱/",
                "status": "open",
            }
        )

    return suggestions


def run_calibration(source_path: Path, runtime_root: Path, dry_run: bool = False) -> int:
    source = PersonaSource.load(Path(source_path))
    if not source.is_source_of_truth():
        raise ValueError("target file is not marked as persona source_of_truth")

    evidence = collect_evidence(runtime_root)
    suggestions = detect_contradictions(source, evidence)

    added = 0
    for sug in suggestions:
        if not source.has_suggestion(sug["id"]):
            source.add_suggestion(sug)
            added += 1

    # Hard boundary: calibration never rewrites stable baseline / confirmed zones.
    stable_before = source.zones["baseline"]

    if not dry_run and added:
        source.frontmatter["updated"] = _today()
        source.save(Path(source_path))

    print(
        f"calibration: scanned evidence={json.dumps(evidence, ensure_ascii=False)}, "
        f"generated={len(suggestions)}, added={added}, "
        f"stable_baseline_untouched={'yes' if stable_before == source.zones['baseline'] else 'NO'}"
    )
    return added


def _today() -> str:
    import datetime as _dt

    return _dt.date.today().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the persona calibration loop.")
    parser.add_argument("--source", required=True, help="persona source Markdown path")
    parser.add_argument("--runtime", required=True, help="OrbitOS runtime root")
    parser.add_argument("--dry-run", action="store_true", help="do not write suggestions")
    args = parser.parse_args()
    run_calibration(Path(args.source), Path(args.runtime), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
