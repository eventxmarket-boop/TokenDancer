from __future__ import annotations

from typing import Any


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _split_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _merge_unique_lines(*values: Any) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        for line in _split_lines(value):
            normalized = _normalize_text(line)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)
    return merged


_BASE_QUESTION_BANK = [
    ("长期目标", "你最希望自己在哪个方向上越走越稳？", "确认长期目标"),
    ("价值锚点", "哪些价值是你最不愿意让步的？", "确认价值锚点"),
    ("核心判断规则", "你做重大判断时最先看的三个条件是什么？", "确认判断规则"),
    ("表达风格", "你在什么场景下会说得更直接，什么场景下会更克制？", "确认表达风格"),
    ("做事方式", "你做事时更偏先保底、先推进，还是先验证？", "确认做事方式"),
    ("阶段变化", "你最近一次明显的判断变化是什么，为什么会变？", "确认阶段变化"),
    ("他人评价", "别人最常怎么评价你的判断或表达？", "确认外部反馈"),
    ("公开资料源", "你希望系统优先参考哪些公开资料源来补全动态事实？", "确认知识源"),
    ("边界规则", "哪些事你绝对不会为了‘像你’而去说或去做？", "确认边界"),
    ("止损规则", "什么情况下你会果断止损，不再继续投入？", "确认止损"),
    ("推进规则", "什么情况下你会选择继续推进，而不是先观望？", "确认推进"),
    ("近期变化", "最近你新增了什么观点、偏好或做法？", "确认近期变化"),
]


def _dedupe_questions(questions: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    seen: set[str] = set()
    result: list[tuple[str, str, str]] = []
    for dimension, question, reason in questions:
        key = _normalize_text(question)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append((dimension, question, reason))
    return result


def _split_question_answer_line(value: str) -> tuple[str, str]:
    text = _normalize_text(value)
    if not text:
        return "", ""
    for delimiter in ["｜", "|", "：", ":"]:
        if delimiter in text:
            left, right = text.split(delimiter, 1)
            return _normalize_text(left), _normalize_text(right)
    return "", text


def build_self_profile_interview_pack(
    form_data: dict[str, Any],
    analysis_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(form_data, dict):
        form_data = {}
    analysis_report = analysis_report if isinstance(analysis_report, dict) else {}

    missing_dimensions = list(analysis_report.get("missing_dimensions") or [])
    questions: list[tuple[str, str, str]] = []

    missing_to_question = {
        "长期目标": ("长期目标", "如果只能保留一个长期方向，你会先保留哪一个？", "补长期目标"),
        "价值锚点": ("价值锚点", "哪三个价值一旦被碰到，你会立刻停下来？", "补价值锚点"),
        "核心判断规则": ("核心判断规则", "你下判断时最常用的三个规则是什么？", "补判断规则"),
        "表达风格": ("表达风格", "哪些场景你会说得更直，哪些场景你会收一点？", "补表达风格"),
        "做事方式": ("做事方式", "你更常用哪种做事顺序：先保底、先推进还是先验证？", "补做事方式"),
        "阶段变化": ("阶段变化", "你最近一次明显改变判断方式的转折是什么？", "补阶段变化"),
        "他人评价": ("他人评价", "别人最常怎么评价你的判断、推进方式或边界感？", "补外部反馈"),
        "公开资料源": ("公开资料源", "你愿意让系统优先查哪些可公开验证的资料源？", "补公开资料"),
        "边界规则": ("边界规则", "哪些事情你不允许系统为了‘像你’而编造？", "补边界"),
        "止损规则": ("止损规则", "什么信号出现时，你会判断该止损了？", "补止损"),
        "推进规则": ("推进规则", "什么信号出现时，你会判断值得继续推进？", "补推进"),
        "近期变化": ("近期变化", "最近 30 天你更新了哪些观点、工具或偏好？", "补近期变化"),
    }

    for dimension in missing_dimensions:
        item = missing_to_question.get(dimension)
        if item:
            questions.append(item)

    analysis_focus = _normalize_text(analysis_report.get("analysis_focus"))
    if analysis_focus:
        questions.append(("分析重心", f"围绕「{analysis_focus}」，你最想系统先抓住哪一点？", "补分析重心"))

    for title, value in [
        ("identity_summary.role", analysis_report.get("identity_summary", {}).get("role")),
        ("identity_summary.positioning", analysis_report.get("identity_summary", {}).get("positioning")),
        ("identity_summary.values", analysis_report.get("identity_summary", {}).get("values")),
        ("identity_summary.goals", analysis_report.get("identity_summary", {}).get("goals")),
    ]:
        if not _normalize_text(value):
            continue
        if "role" in title:
            questions.append(("身份", "如果只用一句话定义你自己，你会怎么说？", "补身份"))
        elif "positioning" in title:
            questions.append(("定位", "你更愿意把自己放在什么位置上说话？", "补定位"))
        elif "values" in title:
            questions.append(("价值", "你最坚持的三个价值是什么？", "补价值"))
        elif "goals" in title:
            questions.append(("目标", "你最近最想朝哪个方向前进？", "补目标"))

    questions.extend(_BASE_QUESTION_BANK)

    custom_questions = _merge_unique_lines(
        form_data.get("self_interview_custom_questions_text"),
        form_data.get("self_deep_dive_questions_text"),
        form_data.get("deep_dive_questions_text"),
    )
    for question in custom_questions:
        questions.append(("自定义补充", question, "用户自定义追问"))

    deduped = _dedupe_questions(questions)
    selected = deduped[:15]

    answer_text = (
        form_data.get("self_interview_answers_text")
        or form_data.get("self_interview_pairs_text")
        or form_data.get("self_deep_dive_answers_text")
        or form_data.get("deep_dive_answers_text")
    )
    raw_answer_lines = _split_lines(answer_text)
    explicit_pairs: list[tuple[str, str]] = []
    legacy_answers: list[str] = []
    for line in raw_answer_lines:
        question, answer = _split_question_answer_line(line)
        if question and answer:
            explicit_pairs.append((question, answer))
        elif answer:
            legacy_answers.append(answer)

    items: list[dict[str, Any]] = []
    answered_count = 0
    used_questions: set[str] = set()

    if explicit_pairs:
        for question, answer in explicit_pairs:
            used_questions.add(question)
            items.append(
                {
                    "question": question,
                    "dimension": "自定义补洞",
                    "reason": "用户通过下拉选项补充的追问",
                    "answer": answer,
                    "follow_up_needed": False,
                }
            )
            answered_count += 1

    legacy_index = 0
    for dimension, question, reason in selected:
        if _normalize_text(question) in used_questions:
            continue
        answer = ""
        if not explicit_pairs and legacy_index < len(legacy_answers):
            answer = legacy_answers[legacy_index]
            legacy_index += 1
        follow_up_needed = not bool(answer)
        if answer:
            answered_count += 1
        items.append(
            {
                "question": question,
                "dimension": dimension,
                "reason": reason,
                "answer": answer,
                "follow_up_needed": follow_up_needed,
            }
        )

    items = items[:15]
    return {
        "question_count": len(items),
        "answered_count": answered_count,
        "unanswered_count": max(len(items) - answered_count, 0),
        "questions": items,
        "answer_notes": _split_lines(
            form_data.get("self_interview_answer_notes_text")
            or form_data.get("self_deep_dive_answers_text")
            or form_data.get("deep_dive_answers_text")
        ),
    }
