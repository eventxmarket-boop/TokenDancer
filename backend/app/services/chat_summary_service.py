from __future__ import annotations

import re
from typing import Iterable

SUMMARY_CONTEXT_WINDOW = 20
SUMMARY_REFRESH_BATCH = 8
SUMMARY_MAX_LINES = 8

TOPIC_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("高考志愿与就业选择", ("高考", "志愿", "报考", "院校", "专业", "分数线", "位次", "录取")),
    ("考研与升学选择", ("考研", "双非", "985", "保研", "复试", "调剂")),
    ("院校与招生信息", ("学校", "院校", "招生", "录取", "分数线", "位次")),
    ("专业与就业路径", ("就业", "岗位", "薪资", "行业", "专业选择", "就业路径")),
    ("家庭条件与路径选择", ("家庭", "普通家庭", "预算", "条件", "退路", "代价")),
]

CONDITION_KEYWORDS = (
    "分数",
    "位次",
    "省份",
    "地区",
    "城市",
    "预算",
    "普通家庭",
    "家里",
    "家庭条件",
    "是否接受外省",
    "是否接受专升本",
)

GOAL_KEYWORDS = (
    "就业稳定",
    "稳定就业",
    "升学",
    "考研",
    "退路",
    "岗位",
    "薪资",
    "平台",
    "机会",
    "路径",
)

DIRECTION_KEYWORDS = (
    "电力",
    "铁路",
    "机械",
    "计算机",
    "金融",
    "临床",
    "人工智能",
    "AI",
    "新能源",
    "半导体",
    "文科",
    "师范",
    "医学",
)

PENDING_ITEMS = (
    "分数/位次",
    "城市接受度",
    "是否接受外省",
    "是否接受专升本",
    "家庭预算",
    "是否更看重就业还是升学",
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _dedupe_lines(lines: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        normalized = _normalize_text(line).strip("-•：: ")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _clean_summary_lines(summary: str | None) -> list[str]:
    if not summary:
        return []
    lines: list[str] = []
    for raw_line in summary.splitlines():
        cleaned = _normalize_text(raw_line).lstrip("-•").strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def _topic_label(text: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return "当前对话"
    for label, keywords in TOPIC_PATTERNS:
        if sum(1 for keyword in keywords if keyword and keyword in normalized) >= 2:
            return label
    if any(keyword in normalized for keyword in ("高考", "志愿", "分数线", "位次", "院校")):
        return "高考志愿与就业选择"
    if any(keyword in normalized for keyword in ("考研", "双非", "985", "保研", "调剂")):
        return "考研与升学选择"
    return "当前对话"


def _extract_condition_bits(text: str) -> list[str]:
    normalized = _normalize_text(text)
    bits: list[str] = []

    score_match = re.search(r"(?:\d{2,3}\s*分|\d{4,5}\s*位次)", normalized)
    if score_match:
        bits.append(score_match.group(0).replace(" ", ""))

    region_keywords = (
        "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
        "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "内蒙古",
        "广西", "宁夏", "新疆", "西藏",
    )
    for region in region_keywords:
        if region in normalized:
            bits.append(region)
            break

    if any(keyword in normalized for keyword in ("普通家庭", "家里条件一般", "家庭条件一般", "预算有限")):
        bits.append("普通家庭 / 预算有限")

    if any(keyword in normalized for keyword in ("外省", "异地", "跨省")):
        bits.append("是否接受外省")
    if any(keyword in normalized for keyword in ("专升本", "升本")):
        bits.append("是否接受专升本")

    if any(keyword in normalized for keyword in ("理科", "文科", "物理", "历史")):
        subject = next((keyword for keyword in ("理科", "文科", "物理", "历史") if keyword in normalized), "")
        if subject:
            bits.append(subject)

    return _dedupe_lines(bits)


def _extract_goal_bits(text: str) -> list[str]:
    normalized = _normalize_text(text)
    bits = [keyword for keyword in GOAL_KEYWORDS if keyword in normalized]
    if any(keyword in normalized for keyword in ("稳定", "稳定就业")):
        bits.append("优先稳定就业")
    if any(keyword in normalized for keyword in ("有退路", "退路清晰")):
        bits.append("优先退路清晰")
    return _dedupe_lines(bits)


def _extract_direction_bits(text: str) -> list[str]:
    normalized = _normalize_text(text)
    bits = [keyword for keyword in DIRECTION_KEYWORDS if keyword in normalized]
    return _dedupe_lines(bits)


def _extract_pending_bits(text: str) -> list[str]:
    normalized = _normalize_text(text)
    bits: list[str] = []
    if not any(keyword in normalized for keyword in ("分数", "位次")):
        bits.append("分数/位次")
    if not any(keyword in normalized for keyword in ("城市", "地区", "省份")):
        bits.append("城市接受度")
    if not any(keyword in normalized for keyword in ("外省", "异地", "跨省")):
        bits.append("是否接受外省")
    if not any(keyword in normalized for keyword in ("专升本", "升本")):
        bits.append("是否接受专升本")
    if not any(keyword in normalized for keyword in ("就业", "升学", "考研")):
        bits.append("是否更看重就业还是升学")
    return _dedupe_lines(bits)


def generate_session_summary(messages: list[dict[str, str]], previous_summary: str | None = None) -> str:
    previous_lines = _clean_summary_lines(previous_summary)
    user_text = " ".join(
        _normalize_text(message.get("content", ""))
        for message in messages
        if str(message.get("role", "")).strip() == "user"
    )
    all_text = " ".join(
        _normalize_text(message.get("content", ""))
        for message in messages
        if str(message.get("role", "")).strip() in {"user", "assistant"}
    )

    lines: list[str] = []
    if previous_lines:
        lines.extend(previous_lines)

    topic = _topic_label(all_text or user_text)
    lines.append(f"当前讨论主题：{topic}")

    condition_bits = _extract_condition_bits(user_text or all_text)
    if condition_bits:
        lines.append(f"已明确条件：{'，'.join(condition_bits[:4])}")

    direction_bits = _extract_direction_bits(all_text)
    if direction_bits:
        lines.append(f"已讨论方向：{'，'.join(direction_bits[:4])}")

    goal_bits = _extract_goal_bits(user_text or all_text)
    if goal_bits:
        lines.append(f"当前偏好：{'，'.join(goal_bits[:4])}")

    pending_bits = _extract_pending_bits(user_text or all_text)
    if pending_bits:
        lines.append(f"待确认：{'，'.join(pending_bits[:4])}")

    lines = _dedupe_lines(lines)
    return "\n".join(lines[:SUMMARY_MAX_LINES]).strip()


def should_refresh_summary(
    message_count: int,
    last_summary_at=None,
    messages_since_summary: int | None = None,
) -> bool:
    if message_count <= SUMMARY_CONTEXT_WINDOW:
        return False

    if last_summary_at is None:
        return True

    if messages_since_summary is None:
        return message_count > SUMMARY_CONTEXT_WINDOW

    return messages_since_summary >= SUMMARY_REFRESH_BATCH


def retrieve_relevant_older_messages(session_id: str, query: str) -> list[dict[str, str]]:
    """Reserved for future retrieval of older message snippets."""
    return []
