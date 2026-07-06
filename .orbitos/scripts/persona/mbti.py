"""MBTI baseline seed — first-run onboarding affordance.

This module provides a compact self-report questionnaire built on the four
MBTI dichotomies (E/I, S/N, T/F, J/P). It is NOT the official MBTI instrument
and is not a clinical or definitive classification. It exists only as a
low-cost, recognizable starting seed; the dynamic persona layer treats the
result as a hypothesis, never as final truth.

Licensing note: the items below are original forced-choice statements authored
for personal onboarding. They are not copied from any proprietary assessment.
"""

from __future__ import annotations

from typing import Optional

DICHOTOMIES = [
    ("E", "I", "ei"),
    ("S", "N", "sn"),
    ("T", "F", "tf"),
    ("J", "P", "jp"),
]

# Each question leans to pole_a (text_a) or pole_b (text_b).
QUESTIONS: list[dict] = [
    # E / I
    {"id": "ei1", "a": "E", "text_a": "我倾向通过和人讨论来理清想法", "text_b": "我倾向先自己想清楚再开口"},
    {"id": "ei2", "a": "E", "text_a": "一周密集社交后我觉得被充电", "text_b": "一周密集社交后我需要独处回血"},
    {"id": "ei3", "a": "E", "text_a": "遇到事我习惯先说出来", "text_b": "遇到事我习惯先消化再表达"},
    {"id": "ei4", "a": "I", "text_a": "我在安静环境里产出更高", "text_b": "我在有点热闹的环境里更来劲"},
    {"id": "ei5", "a": "E", "text_a": "我思考时常需要外部反馈", "text_b": "我思考时常需要内部确认"},
    {"id": "ei6", "a": "I", "text_a": "深交几个人的关系对我更重要", "text_b": "认识很多人的圈子对我更重要"},
    # S / N
    {"id": "sn1", "a": "S", "text_a": "我更信任已经验证过的经验", "text_b": "我更信任可能性和新模式"},
    {"id": "sn2", "a": "S", "text_a": "我关注具体、可落地的细节", "text_b": "我关注整体脉络和远景"},
    {"id": "sn3", "a": "N", "text_a": "我常从现有信息联想到其它方向", "text_b": "我常把现有信息压实到执行"},
    {"id": "sn4", "a": "S", "text_a": "实操步骤清晰时我最踏实", "text_b": "方向有想象力时我最来劲"},
    {"id": "sn5", "a": "N", "text_a": "我容易对重复机械的工作失去耐心", "text_b": "我能在重复里保持稳定产出"},
    {"id": "sn6", "a": "S", "text_a": "我偏好一步到位的稳妥方案", "text_b": "我偏好可迭代试错的灵活方案"},
    # T / F
    {"id": "tf1", "a": "T", "text_a": "做决定时我先看逻辑对不对", "text_b": "做决定时我先看人的感受"},
    {"id": "tf2", "a": "F", "text_a": "我怕伤到人而不敢直说", "text_b": "我怕误导人而坚持直说"},
    {"id": "tf3", "a": "T", "text_a": "我更欣赏犀利的论证", "text_b": "我更欣赏照顾周全的表达"},
    {"id": "tf4", "a": "F", "text_a": "协作里关系顺不顺畅我很在意", "text_b": "协作里结论对不对我很在意"},
    {"id": "tf5", "a": "T", "text_a": "批评我时直接点出问题最好", "text_b": "批评我时先肯定再点问题最好"},
    {"id": "tf6", "a": "F", "text_a": "我常替对方处境着想", "text_b": "我常先站在事情本身立场"},
    # J / P
    {"id": "jp1", "a": "J", "text_a": "我偏好提前计划好再动手", "text_b": "我偏好边做边调整"},
    {"id": "jp2", "a": "P", "text_a": "我享受保留开放选项", "text_b": "我享受把事情定下来"},
    {"id": "jp3", "a": "J", "text_a": "deadline 前我习惯提前收尾", "text_b": "deadline 前我常最后冲刺"},
    {"id": "jp4", "a": "P", "text_a": "结构化太强会让我束手束脚", "text_b": "没有结构我会不安"},
    {"id": "jp5", "a": "J", "text_a": "清单和进度让我安心", "text_b": "清单和进度让我觉得被束缚"},
    {"id": "jp6", "a": "P", "text_a": "我常同时留几个方向在跑", "text_b": "我常一次只推进一个方向"},
]

QUESTION_BY_ID = {q["id"]: q for q in QUESTIONS}


def score(answers: dict[str, str]) -> dict:
    """Score questionnaire answers into an MBTI type.

    answers: {question_id: "a" | "b"}
    Returns dict with keys: type, ties (list of dichotomy letters that tied),
    counts (per dichotomy pole counts), valid (bool).
    """
    counts: dict[str, int] = {}
    for pole_a, pole_b, _ in DICHOTOMIES:
        counts[pole_a] = 0
        counts[pole_b] = 0
    answered = 0
    for qid, choice in answers.items():
        q = QUESTION_BY_ID.get(qid)
        if q is None or choice not in ("a", "b"):
            continue
        answered += 1
        leaned = q["a"] if choice == "a" else _opposite(q["a"])
        counts[leaned] += 1

    type_letters = []
    ties = []
    for pole_a, pole_b, _ in DICHOTOMIES:
        a, b = counts[pole_a], counts[pole_b]
        if a > b:
            type_letters.append(pole_a)
        elif b > a:
            type_letters.append(pole_b)
        else:
            type_letters.append(pole_a)  # tie-break default (conservative)
            ties.append(pole_a)
    return {
        "type": "".join(type_letters),
        "ties": ties,
        "counts": counts,
        "valid": answered >= 12,
    }


def _opposite(pole: str) -> str:
    return {"E": "I", "I": "E", "S": "N", "N": "S", "T": "F", "F": "T", "J": "P", "P": "J"}[pole]


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
