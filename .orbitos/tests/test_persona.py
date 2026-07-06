"""Dynamic Persona Layer — seam tests (#6..#10).

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

# Answers that deterministically produce INTJ (to exercise the J detector).
SAMPLE_ANSWERS = {
    "ei1": "b", "ei2": "b", "ei3": "b", "ei4": "a", "ei5": "b", "ei6": "b",
    "sn1": "b", "sn2": "b", "sn3": "a", "sn4": "b", "sn5": "a", "sn6": "b",
    "tf1": "a", "tf2": "b", "tf3": "a", "tf4": "b", "tf5": "a", "tf6": "b",
    "jp1": "a", "jp2": "b", "jp3": "a", "jp4": "b", "jp5": "a", "jp6": "b",
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
    # minimal files so evidence collection does not crash
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
    _require(src.frontmatter.get("mbti_confidence") == "hypothesis",
             "MBTI result must be hypothesis-level, not confirmed truth")
    _require(src.baseline_status == "seeded", "baseline status should be seeded")
    for zone in ("baseline", "hypotheses", "confirmed", "suggestions"):
        _require(zone in src.zones, f"zone missing: {zone}")
    # hypotheses must carry confidence=hypothesis (not treated as final truth)
    _require("confidence=hypothesis" in src.zones["hypotheses"],
             "hypotheses must be explicitly hypothesis-level")
    # not scattered: single file, four zones present
    _require(src.zones["hypotheses"].count("- [h") == 4,
             "expected 4 default hypotheses derived from MBTI seed")


def test_calibration_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    # ensure a seeded baseline first
    baseline.build_baseline(
        source_path, "测试用户", SAMPLE_ANSWERS,
        created="2026-07-06", updated="2026-07-06",
    )
    # craft contradictory evidence: many parallel projects + open inbox
    for i in range(4):
        (runtime_root / "03-项目" / f"proj{i}").mkdir(parents=True, exist_ok=True)
    for i in range(8):
        (runtime_root / "01-收件箱" / f"item{i}.md").write_text("x", encoding="utf-8")

    src_before = PersonaSource.load(source_path)
    stable_baseline_before = src_before.zones["baseline"]

    added = calibrate.run_calibration(source_path, runtime_root, dry_run=False)
    _require(added >= 1, "calibration should produce at least one suggestion under contradictory evidence")

    src_after = PersonaSource.load(source_path)
    # HARD RULE: stable baseline must not be silently overwritten
    _require(src_after.zones["baseline"] == stable_baseline_before,
             "calibration must NOT rewrite the stable baseline zone")
    _require("cal_parallelism" in src_after.zones["suggestions"],
             "calibration suggestion must land in the open-suggestions zone")
    # confirmed patterns zone must remain untouched by calibration
    _require(src_after.zones["confirmed"] == src_before.zones["confirmed"],
             "calibration must not fabricate confirmed patterns")


def test_projection_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    baseline.build_baseline(
        source_path, "测试用户", SAMPLE_ANSWERS,
        created="2026-07-06", updated="2026-07-06",
    )
    # a local collaboration preference file must exist for the collab projection
    collab_path = runtime_root / "00-系统/08-本地协作偏好.md"
    collab_path.write_text(
        "---\ntitle: 本地协作偏好\n---\n\n# 本地协作偏好\n\n## 默认合作方式\n\n- 你定方向。\n",
        encoding="utf-8",
    )

    project.run_projections(source_path, runtime_root)

    # collaboration projection is derived, not a separate truth source
    collab_text = collab_path.read_text(encoding="utf-8")
    _require("人物档案派生" in collab_text, "collab projection must be written into local prefs")
    _require("非独立真相" in collab_text, "collab projection must be marked derived")

    state_path = runtime_root / "00-系统/人物状态投影.md"
    direction_path = runtime_root / "00-系统/人物方向候选.md"
    _require(not state_path.exists(), "separate state projection page should not be generated")
    _require(not direction_path.exists(), "separate direction projection page should not be generated")


def test_runtime_local_boundary() -> None:
    # The runtime-local persona source must NOT be shipped in the product repo.
    _require(not (SOURCE_ROOT / "00-系统/09-人物档案.md").exists(),
             "runtime-local persona source must not leak into the product repo")


def run_persona_tests(runtime_root=None) -> str:
    if runtime_root is None:
        with tempfile.TemporaryDirectory(prefix="orbitos-persona-test-") as td:
            root = Path(td) / "orbitos"
            root.mkdir(parents=True, exist_ok=True)
            _build_synthetic_runtime(root)
            test_baseline_seam(root)
            test_calibration_seam(root)
            test_projection_seam(root)
    else:
        _build_synthetic_runtime(runtime_root)
        test_baseline_seam(runtime_root)
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
