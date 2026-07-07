"""Dynamic Persona Layer - seam tests.

These tests verify the current intended lifecycle:
- baseline seed generation writes one coherent runtime-local source
- calibration only appends reviewable suggestions and never rewrites baseline
- updates only happen after explicit confirmation and refresh the collaboration projection
- runtime-local source does not leak into the product repo
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
import update  # noqa: E402
from persona_source import PersonaSource  # noqa: E402

CURRENT_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_REPO_ROOT = CURRENT_ROOT if (CURRENT_ROOT / "AGENTS.md").exists() and (CURRENT_ROOT / "00-系统").exists() and (CURRENT_ROOT / ".orbitos").exists() and not (CURRENT_ROOT / "03-项目/OrbitOS/repo").exists() else CURRENT_ROOT / "03-项目/OrbitOS/repo"

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


def _write_collab_file(runtime_root: Path) -> Path:
    collab_path = runtime_root / "00-系统/08-本地协作偏好.md"
    collab_path.write_text(
        "---\ntitle: 本地协作偏好\n---\n\n# 本地协作偏好\n\n## 默认合作方式\n\n- 你定方向。\n",
        encoding="utf-8",
    )
    return collab_path


def test_baseline_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    baseline.build_baseline(
        source_path,
        "测试用户：系统型建设者",
        SAMPLE_ANSWERS,
        created="2026-07-06",
        updated="2026-07-06",
    )
    src = PersonaSource.load(source_path)
    _require(src.is_source_of_truth(), "persona source must be marked source_of_truth")
    _require(src.mbti_type == "INTJ", f"expected INTJ, got {src.mbti_type}")
    _require(src.frontmatter.get("mbti_confidence") == "hypothesis", "MBTI result must be hypothesis-level")
    _require(src.frontmatter.get("mbti_questionnaire_version") == "mbti-seed-v2", "questionnaire version must be persisted")
    _require(src.frontmatter.get("mbti_answered") == 24, "answered count must be persisted")
    _require(src.baseline_status == "seeded", "baseline status should be seeded")
    for zone in ("baseline", "hypotheses", "confirmed", "suggestions"):
        _require(zone in src.zones, f"zone missing: {zone}")
    _require("24 题、5 档垂直选项问卷" in src.zones["baseline"], "baseline note should describe the questionnaire shape")
    _require(src.zones["hypotheses"].count("- [h") == 4, "expected 4 default hypotheses")


def test_mbti_score_scale() -> None:
    spec = mbti.questionnaire_spec()
    _require(spec["asking_constraints"]["mode"] == "single_question", "questionnaire should enforce single-question mode")
    _require("prompt" in spec["questions"][0], "questionnaire questions should expose canonical prompts")
    _require("请只回复数字 1 / 2 / 3 / 4 / 5。" in spec["questions"][0]["prompt"], "canonical prompt should constrain the answer format")
    _require("不确定 / 看情况" in spec["questions"][0]["prompt"], "canonical prompt should expose an explicit middle option")
    result = mbti.score(
        {
            "ei1": "strong_right",
            "ei2": "lean_right",
            "ei3": "neutral",
            "ei4": "strong_left",
            "sn1": "5",
            "sn2": "4",
            "sn3": "1",
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
    _require(result["uncertain_answers"] == 1, "uncertain answers should be counted separately")
    _require(result["dimension_scores"]["jp"] != 0, "dimension score should reflect weighted answers")


def test_calibration_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    baseline.build_baseline(source_path, "测试用户", SAMPLE_ANSWERS, created="2026-07-06", updated="2026-07-06")
    for i in range(4):
        (runtime_root / "03-项目" / f"proj{i}").mkdir(parents=True, exist_ok=True)
    for i in range(8):
        (runtime_root / "01-收件箱" / f"item{i}.md").write_text("x", encoding="utf-8")

    src_before = PersonaSource.load(source_path)
    stable_baseline_before = src_before.zones["baseline"]
    added = calibrate.run_calibration(source_path, runtime_root, dry_run=False)
    _require(added >= 1, "calibration should produce at least one suggestion")
    src_after = PersonaSource.load(source_path)
    _require(src_after.zones["baseline"] == stable_baseline_before, "calibration must not rewrite the stable baseline zone")
    _require("cal_parallelism" in src_after.zones["suggestions"], "calibration suggestion must land in the suggestions zone")
    _require(src_after.zones["confirmed"] == src_before.zones["confirmed"], "calibration must not fabricate confirmed patterns")


def test_projection_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    collab_path = _write_collab_file(runtime_root)
    baseline.build_baseline(source_path, "测试用户", SAMPLE_ANSWERS, created="2026-07-06", updated="2026-07-06")
    project.run_projections(source_path, runtime_root)
    collab_text = collab_path.read_text(encoding="utf-8")
    _require("人物档案派生" in collab_text, "collab projection must be written into local prefs")
    _require("非独立真相" in collab_text, "collab projection must be marked derived")
    _require(not (runtime_root / "00-系统/人物状态投影.md").exists(), "legacy state projection page should not be generated")
    _require(not (runtime_root / "00-系统/人物方向候选.md").exists(), "legacy direction projection page should not be generated")


def test_update_seam(runtime_root: Path) -> None:
    source_path = runtime_root / "00-系统/09-人物档案.md"
    collab_path = _write_collab_file(runtime_root)
    baseline.build_baseline(source_path, "测试用户", SAMPLE_ANSWERS, created="2026-07-06", updated="2026-07-06")

    update.apply_update(source_path, runtime_root, confirm_baseline=True)
    src = PersonaSource.load(source_path)
    _require(src.baseline_status == "confirmed", "baseline confirmation should persist")

    for i in range(4):
        (runtime_root / "03-项目" / f"proj{i}").mkdir(parents=True, exist_ok=True)
    for i in range(8):
        (runtime_root / "01-收件箱" / f"item{i}.md").write_text("x", encoding="utf-8")
    calibrate.run_calibration(source_path, runtime_root, dry_run=False)

    update.apply_update(
        source_path,
        runtime_root,
        accept_suggestion="cal_parallelism",
        confirmed_statement="用户在复杂任务里长期保留多个并行方向，需要开放式节奏支持。",
        evidence="03-项目/, 01-收件箱/",
        note="用户确认这条建议成立",
    )
    src = PersonaSource.load(source_path)
    _require("[confirmed_cal_parallelism]" in src.zones["confirmed"], "accepted suggestion should become a confirmed pattern")
    _require("状态：accepted" in src.zones["suggestions"], "accepted suggestion status should persist")
    collab_text = collab_path.read_text(encoding="utf-8")
    _require("人物档案派生" in collab_text, "collaboration projection should refresh after update")


def test_runtime_local_boundary() -> None:
    _require(not (PRODUCT_REPO_ROOT / "00-系统/09-人物档案.md").exists(), "runtime-local persona source must not leak into the product repo")


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
            test_update_seam(root)
    else:
        _build_synthetic_runtime(runtime_root)
        test_baseline_seam(runtime_root)
        test_mbti_score_scale()
        test_calibration_seam(runtime_root)
        test_projection_seam(runtime_root)
        test_update_seam(runtime_root)
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
