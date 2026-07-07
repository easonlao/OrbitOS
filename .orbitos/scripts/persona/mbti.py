"""MBTI baseline seed — first-run onboarding affordance.

This module provides a compact self-report questionnaire built on the four
MBTI dichotomies (E/I, S/N, T/F, J/P). It is NOT the official MBTI instrument
and is not a clinical or definitive classification. It exists only as a
low-cost, recognizable starting seed; the dynamic persona layer treats the
result as a hypothesis, never as final truth.

Licensing note: the items below are original statements authored for personal
onboarding. They are not copied from any proprietary assessment.
"""

from __future__ import annotations

import argparse
import json
from typing import Optional

QUESTIONNAIRE_VERSION = "mbti-seed-v2"

ASKING_CONSTRAINTS = {
    "mode": "single_question",
    "identity_prompt": "请先用一句话描述你认为自己相对稳定的底色。我会把这句话作为人物模块的初始 identity。",
    "intro": "下面开始 24 题、5 档倾向问卷。它只用于生成 MBTI 种子假设，不是官方 MBTI，也不是最终人格定论。",
    "answer_instruction": "每题从 5 个垂直选项里选 1 个，回复对应数字 `1 / 2 / 3 / 4 / 5` 即可。",
    "answer_scale": [
        "1 = 明显更接近左侧",
        "2 = 略微更接近左侧",
        "3 = 不确定 / 看情况",
        "4 = 略微更接近右侧",
        "5 = 明显更接近右侧",
    ],
    "must_do": [
        "先收集 identity，再进入 24 题问卷",
        "一次只问 1 题，并标明当前题号",
        "直接使用脚本导出的标准题面，不自行改写题意",
        "用户答案不合法时，只重问当前题，不推进下一题",
    ],
    "must_not": [
        "不得在提问时解释人格理论",
        "不得擅自补充示例、诱导语或题外分析",
        "不得把用户答案即时解释成人格结论",
        "不得一次混问多题，除非用户明确要求批量回答",
    ],
}

DICHOTOMIES = [
    ("E", "I", "ei"),
    ("S", "N", "sn"),
    ("T", "F", "tf"),
    ("J", "P", "jp"),
]

ANSWER_SCALE = [
    {"value": -2, "label": "strong_left", "display": "明显偏左"},
    {"value": -1, "label": "lean_left", "display": "略偏左"},
    {"value": 0, "label": "uncertain", "display": "不确定 / 看情况"},
    {"value": 1, "label": "lean_right", "display": "略偏右"},
    {"value": 2, "label": "strong_right", "display": "明显偏右"},
]

QUESTIONS: list[dict] = [
    {"id": "ei1", "axis": "ei", "left_pole": "E", "text_left": "我倾向通过和人讨论来理清想法", "text_right": "我倾向先自己想清楚再开口"},
    {"id": "ei2", "axis": "ei", "left_pole": "E", "text_left": "一周密集社交后我觉得被充电", "text_right": "一周密集社交后我需要独处回血"},
    {"id": "ei3", "axis": "ei", "left_pole": "E", "text_left": "遇到事我习惯先说出来", "text_right": "遇到事我习惯先消化再表达"},
    {"id": "ei4", "axis": "ei", "left_pole": "I", "text_left": "我在安静环境里产出更高", "text_right": "我在有点热闹的环境里更来劲"},
    {"id": "ei5", "axis": "ei", "left_pole": "E", "text_left": "我思考时常需要外部反馈", "text_right": "我思考时常需要内部确认"},
    {"id": "ei6", "axis": "ei", "left_pole": "I", "text_left": "深交几个人的关系对我更重要", "text_right": "认识很多人的圈子对我更重要"},
    {"id": "sn1", "axis": "sn", "left_pole": "S", "text_left": "我更信任已经验证过的经验", "text_right": "我更信任可能性和新模式"},
    {"id": "sn2", "axis": "sn", "left_pole": "S", "text_left": "我关注具体、可落地的细节", "text_right": "我关注整体脉络和远景"},
    {"id": "sn3", "axis": "sn", "left_pole": "N", "text_left": "我常从现有信息联想到其它方向", "text_right": "我常把现有信息压实到执行"},
    {"id": "sn4", "axis": "sn", "left_pole": "S", "text_left": "实操步骤清晰时我最踏实", "text_right": "方向有想象力时我最来劲"},
    {"id": "sn5", "axis": "sn", "left_pole": "N", "text_left": "我容易对重复机械的工作失去耐心", "text_right": "我能在重复里保持稳定产出"},
    {"id": "sn6", "axis": "sn", "left_pole": "S", "text_left": "我偏好一步到位的稳妥方案", "text_right": "我偏好可迭代试错的灵活方案"},
    {"id": "tf1", "axis": "tf", "left_pole": "T", "text_left": "做决定时我先看逻辑对不对", "text_right": "做决定时我先看人的感受"},
    {"id": "tf2", "axis": "tf", "left_pole": "F", "text_left": "我怕伤到人而不敢直说", "text_right": "我怕误导人而坚持直说"},
    {"id": "tf3", "axis": "tf", "left_pole": "T", "text_left": "我更欣赏犀利的论证", "text_right": "我更欣赏照顾周全的表达"},
    {"id": "tf4", "axis": "tf", "left_pole": "F", "text_left": "协作里关系顺不顺畅我很在意", "text_right": "协作里结论对不对我很在意"},
    {"id": "tf5", "axis": "tf", "left_pole": "T", "text_left": "批评我时直接点出问题最好", "text_right": "批评我时先肯定再点问题最好"},
    {"id": "tf6", "axis": "tf", "left_pole": "F", "text_left": "我常替对方处境着想", "text_right": "我常先站在事情本身立场"},
    {"id": "jp1", "axis": "jp", "left_pole": "J", "text_left": "我偏好提前计划好再动手", "text_right": "我偏好边做边调整"},
    {"id": "jp2", "axis": "jp", "left_pole": "P", "text_left": "我享受保留开放选项", "text_right": "我享受把事情定下来"},
    {"id": "jp3", "axis": "jp", "left_pole": "J", "text_left": "deadline 前我习惯提前收尾", "text_right": "deadline 前我常最后冲刺"},
    {"id": "jp4", "axis": "jp", "left_pole": "P", "text_left": "结构化太强会让我束手束脚", "text_right": "没有结构我会不安"},
    {"id": "jp5", "axis": "jp", "left_pole": "J", "text_left": "清单和进度让我安心", "text_right": "清单和进度让我觉得被束缚"},
    {"id": "jp6", "axis": "jp", "left_pole": "P", "text_left": "我常同时留几个方向在跑", "text_right": "我常一次只推进一个方向"},
]

QUESTION_BY_ID = {q["id"]: q for q in QUESTIONS}


def normalize_answer(value) -> Optional[int]:
    if isinstance(value, int) and value in (-2, -1, 0, 1, 2):
        return value
    if isinstance(value, int) and value in (1, 2, 3, 4, 5):
        return {1: -2, 2: -1, 3: 0, 4: 1, 5: 2}[value]
    if isinstance(value, str):
        raw = value.strip().lower()
        mapping = {
            "a": -2,
            "b": 2,
            "-2": -2,
            "-1": -1,
            "0": 0,
            "1": 1,
            "2": 2,
            "3": 0,
            "4": 1,
            "5": 2,
            "strong_left": -2,
            "lean_left": -1,
            "neutral": 0,
            "uncertain": 0,
            "lean_right": 1,
            "strong_right": 2,
        }
        return mapping.get(raw)
    return None


def questionnaire_spec() -> dict:
    questions = []
    total = len(QUESTIONS)
    for index, item in enumerate(QUESTIONS, start=1):
        enriched = dict(item)
        enriched["prompt"] = render_question_prompt(item, index=index, total=total)
        questions.append(enriched)
    return {
        "version": QUESTIONNAIRE_VERSION,
        "type": "mbti_seed",
        "question_count": len(QUESTIONS),
        "scale": ANSWER_SCALE,
        "asking_constraints": ASKING_CONSTRAINTS,
        "questions": questions,
    }


def render_question_prompt(question: dict, *, index: int, total: int) -> str:
    return (
        f"第 {index}/{total} 题\n"
        f"A. {question['text_left']}\n"
        f"B. {question['text_right']}\n\n"
        "请选择 1 个选项：\n"
        "1. 明显更接近 A\n"
        "2. 略微更接近 A\n"
        "3. 不确定 / 看情况\n"
        "4. 略微更接近 B\n"
        "5. 明显更接近 B\n\n"
        "请只回复数字 1 / 2 / 3 / 4 / 5。"
    )


def score(answers: dict[str, int | str]) -> dict:
    """Score questionnaire answers into an MBTI seed."""
    counts: dict[str, int] = {}
    dimension_scores: dict[str, int] = {}
    for pole_a, pole_b, _ in DICHOTOMIES:
        counts[pole_a] = 0
        counts[pole_b] = 0
    for _, _, axis in DICHOTOMIES:
        dimension_scores[axis] = 0

    answered = 0
    uncertain_answers = 0
    for qid, raw_value in answers.items():
        q = QUESTION_BY_ID.get(qid)
        value = normalize_answer(raw_value)
        if q is None or value is None:
            continue
        answered += 1
        if value == 0:
            uncertain_answers += 1
            continue
        left_pole = q["left_pole"]
        right_pole = _opposite(left_pole)
        leaned = left_pole if value < 0 else right_pole
        counts[leaned] += abs(value)
        dimension_scores[q["axis"]] += _axis_score(q["axis"], left_pole, value)

    type_letters = []
    ties = []
    for pole_a, pole_b, axis in DICHOTOMIES:
        axis_score = dimension_scores[axis]
        if axis_score > 0:
            type_letters.append(pole_a)
        elif axis_score < 0:
            type_letters.append(pole_b)
        else:
            type_letters.append(pole_a)
            ties.append(pole_a)

    return {
        "version": QUESTIONNAIRE_VERSION,
        "type": "".join(type_letters),
        "ties": ties,
        "counts": counts,
        "dimension_scores": dimension_scores,
        "answered": answered,
        "uncertain_answers": uncertain_answers,
        "valid": answered >= 18,
    }


def _opposite(pole: str) -> str:
    return {"E": "I", "I": "E", "S": "N", "N": "S", "T": "F", "F": "T", "J": "P", "P": "J"}[pole]


def _axis_score(axis: str, left_pole: str, value: int) -> int:
    pole_a = next(p[0] for p in DICHOTOMIES if p[2] == axis)
    return -value if left_pole == pole_a else value


def explain(mbti_type: str) -> str:
    layer = {
        "E": "外倾：倾向通过外部互动与讨论理清思路",
        "I": "内倾：倾向先内部想清楚再表达",
        "S": "实感：偏好具体、已验证、可落地的信息",
        "N": "直觉：偏好整体脉络、可能性与新模型",
        "T": "思考：决策先看重逻辑与对错",
        "F": "情感：决策先看重人与关系",
        "J": "判断：偏好提前计划、把事定下来",
        "P": "感知：偏好保留开放、边做边调",
    }
    parts = [layer.get(c, c) for c in mbti_type]
    return "；".join(parts)


def derive_hypotheses(mbti_type: str) -> list[dict]:
    """Default collaboration/output hypotheses derived from the MBTI seed.

    Every hypothesis is explicitly an assumption (confidence=hypothesis), never
    a confirmed preference. Later behavior evidence may refine or overturn it.
    """
    mapping = {
        "E": "初始协作偏好：可多用外部讨论/口头对齐来推进，但需以行为证据复核",
        "I": "初始协作偏好：先给书面结论与安静消化空间，再进入讨论",
        "S": "初始产出偏好：优先具体、可落地的交付物与实操步骤",
        "N": "初始产出偏好：优先方向、模型与可迭代试错空间",
        "T": "初始沟通偏好：直接给论证与结论，少铺垫",
        "F": "初始沟通偏好：先照顾关系与处境，再点问题",
        "J": "初始节奏偏好：提前计划、设清单与进度节点",
        "P": "初始节奏偏好：保留开放选项、边做边调整",
    }
    hyps = []
    for i, ch in enumerate(mbti_type):
        hyps.append(
            {
                "id": f"h{i+1}",
                "statement": mapping.get(ch, ""),
                "derived_from": f"mbti:{mbti_type}",
                "confidence": "hypothesis",
            }
        )
    return hyps


def main() -> int:
    parser = argparse.ArgumentParser(description="MBTI seed questionnaire helpers.")
    parser.add_argument("--print-json", action="store_true", help="print the questionnaire spec as JSON")
    args = parser.parse_args()
    if args.print_json:
        print(json.dumps(questionnaire_spec(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
