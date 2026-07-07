"""Dynamic Persona Layer - seam tests (#6..#10).

These tests verify externally visible behavior and boundary preservation:

- baseline seam: completed questionnaire + MBTI seed -> one coherent persona source
  with explicit hypothesis fields (not scattered notes).
- calibration seam: evidence contradicts baseline -> reviewable suggestion, and
  the stable persona source is NOT silently overwritten.
- projection seam: only the local collaboration preference page receives a durable
  visible projection; separate state/direction Markdown pages are not generated.
- boundary: the runtime-local persona source must NOT leak into the product repo.
- confidence: hypotheses and MBTI result are explicitly hypothesis-level.

Run with: python .orbitos/tests/test_persona.py
"""

import sys
import tempfile
from pathlib import Path

PERSONA_DIR = Path(__file__).resolve().parents[2] / ".orbitos/scripts/persona"
sys.path.insert(0, str(PERSONA_DIR))

import baseline  # noqa: E402
import calibrate  # noqa: E402
import mbti  # noqa: E402
import project  # noqa: E402
from persona_source import PersonaSource  # noqa: E402

SOURCE_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_ANSWERS = {
    "ei1": 2, "ei2": 2, "ei3": 2, "ei4": -2, "ei5": 2, "ei6": 2,
    "sn1": 2, "sn2": 2, "sn3": -2, "sn4": 2, "sn5": -2, "sn6": 2,
    "tf1": -2, "tf2": 2, "tf3": -2, "tf4": 2, "tf5": -2, "tf6": 2,
    "jp1": -2, "jp2": 2, "jp3": -2, "jp4": 2, "jp5": -2, "jp6": 2,
}


def _require(condition, message):
    if not condition:
        raise AssertionError(message)


def _build_synthetic_runtime(root: Path) -> None:
    for d in [
        "00-系统",
        "01-收件箱",
        "02-时间线",
        "03-项目",
        "04-知识/00-草稿箱",
        ".orbitos/logs/events",
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "02-时间线/今日.md").write_text("# 今日\n", encoding="utf-8")


def test_baseline_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    baseline.build_baseline(
        source_path, "测试用户：系统型建设者", SAMPLE_ANSWERS,
        created="2026-07-06", updated="2026-07-06",
    )
    src = PersonaSource.load(source_path)
    _require(src.is_source_of_truth(), "persona source must be marked source_of_truth")
    _require(src.mbti_type == "INTJ", f"expected INTJ, got {src.mbti_type}")
    _require(
        src.frontmatter.get("mbti_confidence") == "hypothesis",
        "MBTI result must be hypothesis-level, not confirmed truth",
    )
    _require(
        src.frontmatter.get("mbti_questionnaire_version") == "mbti-seed-v2",
        "questionnaire version must be persisted",
    )
    _require(src.frontmatter.get("mbti_answered") == 24, "full baseline should persist answered count")
    _require(src.baseline_status == "seeded", "baseline status should be seeded")
    for zone in ("baseline", "hypotheses", "confirmed", "suggestions"):
        _require(zone in src.zones, f"zone missing: {zone}")
    _require(
        "confidence=hypothesis" in src.zones["hypotheses"],
        "hypotheses must be explicitly hypothesis-level",
    )
    _require(
        src.zones["hypotheses"].count("- [h") == 4,
        "expected 4 default hypotheses derived from MBTI seed",
    )
    _require(
        "24 题、5 档倾向问卷" in src.zones["baseline"],
        "baseline note should describe the current questionnaire shape",
    )


def test_mbti_score_scale() -> None:
    result = mbti.score(
        {
            "ei1": "strong_right",
            "ei2": "lean_right",
            "ei3": "neutral",
            "ei4": "strong_left",
            "sn1": "2",
            "sn2": "1",
            "sn3": "-2",
            "tf1": "-2",
            "jp1": "-1",
            "jp2": "2",
            "jp3": "a",
            "jp4": "b",
            "jp5": -2,
            "jp6": 2,
        }
    )
    _require(result["version"] == "mbti-seed-v2", "score result should expose questionnaire version")
    _require(result["answered"] == 14, "compatible labels should count as answered")
    _require(result["neutral_answers"] == 1, "neutral answers should be counted separately")
    _require(result["dimension_scores"]["jp"] != 0, "dimension score should reflect weighted answers")


def test_calibration_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    baseline.build_baseline(
        source_path, "测试用户", SAMPLE_ANSWERS,
        created="2026-07-06", updated="2026-07-06",
    )
    for i in range(4):
        (runtime_root / "03-项目" / f"proj{i}").mkdir(parents=True, exist_ok=True)
    for i in range(8):
        (runtime_root / "01-收件箱" / f"item{i}.md").write_text("x", encoding="utf-8")

    src_before = PersonaSource.load(source_path)
    stable_baseline_before = src_before.zones["baseline"]

    added = calibrate.run_calibration(source_path, runtime_root, dry_run=False)
    _require(added >= 1, "calibration should produce at least one suggestion under contradictory evidence")

    src_after = PersonaSource.load(source_path)
    _require(
        src_after.zones["baseline"] == stable_baseline_before,
        "calibration must NOT rewrite the stable baseline zone",
    )
    _require(
        "cal_parallelism" in src_after.zones["suggestions"],
        "calibration suggestion must land in the open-suggestions zone",
    )
    _require(
        src_after.zones["confirmed"] == src_before.zones["confirmed"],
        "calibration must not fabricate confirmed patterns",
    )


def test_projection_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    baseline.build_baseline(
        source_path, "测试用户", SAMPLE_ANSWERS,
        created="2026-07-06", updated="2026-07-06",
    )
    collab_path = runtime_root / "00-系统/08-本地协作偏好.md"
    collab_path.write_text(
        "---\ntitle: 本地协作偏好\n---\n\n# 本地协作偏好\n\n## 默认合作方式\n\n- 你定方向。\n",
        encoding="utf-8",
    )

    project.run_projections(source_path, runtime_root)

    collab_text = collab_path.read_text(encoding="utf-8")
    _require("人物档案派生" in collab_text, "collab projection must be written into local prefs")
    _require("非独立真相" in collab_text, "collab projection must be marked derived")

    state_path = runtime_root / "00-系统/人物状态投影.md"
    direction_path = runtime_root / "00-系统/人物方向候选.md"
    _require(not state_path.exists(), "separate state projection page should not be generated")
    _require(not direction_path.exists(), "separate direction projection page should not be generated")


def test_runtime_local_boundary() -> None:
    _require(
        not (SOURCE_ROOT / "00-系统/09-人物档案.md").exists(),
        "runtime-local persona source must not leak into the product repo",
    )


def run_persona_tests(runtime_root=None) -> str:
    if runtime_root is None:
        with tempfile.TemporaryDirectory(prefix="orbitos-persona-test-") as td:
            root = Path(td) / "orbitos"
            root.mkdir(parents=True, exist_ok=True)
            _build_synthetic_runtime(root)
            test_baseline_seam(root)
            test_mbti_score_scale()
            test_calibration_seam(root)
            test_projection_seam(root)
    else:
        _build_synthetic_runtime(runtime_root)
        test_baseline_seam(runtime_root)
        test_mbti_score_scale()
        test_calibration_seam(runtime_root)
        test_projection_seam(runtime_root)
    test_runtime_local_boundary()
    return "persona seam tests passed"


def main():
    with tempfile.TemporaryDirectory(prefix="orbitos-persona-test-") as td:
        root = Path(td) / "orbitos"
        root.mkdir(parents=True, exist_ok=True)
        result = run_persona_tests(root)
    print(result)


if __name__ == "__main__":
    main()
