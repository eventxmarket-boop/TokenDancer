from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.llm_gateway import LLMGatewayError, generate_reply
from app.services.text_sanitizer import strip_think_blocks


MODE_LABELS = {
    "zhouyi": "周易64卦",
    "liuyao": "六爻占卜",
    "bazi": "八字排盘",
}

TRIGRAMS = [
    {"name": "乾", "symbol": "☰", "meaning": "天"},
    {"name": "兑", "symbol": "☱", "meaning": "泽"},
    {"name": "离", "symbol": "☲", "meaning": "火"},
    {"name": "震", "symbol": "☳", "meaning": "雷"},
    {"name": "巽", "symbol": "☴", "meaning": "风"},
    {"name": "坎", "symbol": "☵", "meaning": "水"},
    {"name": "艮", "symbol": "☶", "meaning": "山"},
    {"name": "坤", "symbol": "☷", "meaning": "地"},
]

HEXAGRAM_MAP = {
    "111111": (1, "乾"),
    "000000": (2, "坤"),
    "100010": (3, "屯"),
    "010001": (4, "蒙"),
    "111010": (5, "需"),
    "010111": (6, "讼"),
    "000010": (7, "师"),
    "010000": (8, "比"),
    "111011": (9, "小畜"),
    "110111": (10, "履"),
    "111000": (11, "泰"),
    "000111": (12, "否"),
    "101111": (13, "同人"),
    "111101": (14, "大有"),
    "001000": (15, "谦"),
    "000100": (16, "豫"),
    "011110": (17, "随"),
    "100110": (18, "蛊"),
    "110000": (19, "临"),
    "000011": (20, "观"),
    "100101": (21, "噬嗑"),
    "101001": (22, "贲"),
    "100000": (23, "剥"),
    "000001": (24, "复"),
    "100111": (25, "无妄"),
    "111001": (26, "大畜"),
    "100001": (27, "颐"),
    "011110": (28, "大过"),
    "010010": (29, "坎"),
    "101101": (30, "离"),
    "001110": (31, "咸"),
    "011100": (32, "恒"),
    "001111": (33, "遁"),
    "111100": (34, "大壮"),
    "000101": (35, "晋"),
    "101000": (36, "明夷"),
    "101011": (37, "家人"),
    "110101": (38, "睽"),
    "001010": (39, "蹇"),
    "010100": (40, "解"),
    "110001": (41, "损"),
    "100011": (42, "益"),
    "111110": (43, "夬"),
    "011111": (44, "姤"),
    "000110": (45, "萃"),
    "011000": (46, "升"),
    "010110": (47, "困"),
    "011010": (48, "井"),
    "101110": (49, "革"),
    "011101": (50, "鼎"),
    "100100": (51, "震"),
    "001001": (52, "艮"),
    "001011": (53, "渐"),
    "110100": (54, "归妹"),
    "101100": (55, "丰"),
    "001101": (56, "旅"),
    "011011": (57, "巽"),
    "110110": (58, "兑"),
    "010011": (59, "涣"),
    "110010": (60, "节"),
    "110011": (61, "中孚"),
    "001100": (62, "小过"),
    "101010": (63, "既济"),
    "010101": (64, "未济"),
}

HEXAGRAM_MEANINGS = {
    "乾": "元亨利贞，刚健中正",
    "坤": "元亨，厚德载物",
    "泰": "小往大来，吉亨",
    "否": "否之匪人，不利君子贞",
    "需": "有孚光亨，利涉大川",
    "讼": "有孚窒惕，中吉终凶",
    "师": "贞丈人吉，无咎",
    "比": "吉，原筮元永贞，无咎",
    "咸": "亨，利贞，取女吉",
    "恒": "亨，无咎，利贞，利有攸往",
    "损": "有孚元吉，无咎，可贞",
    "益": "利有攸往，利涉大川",
    "解": "利西南，无所往，来复吉",
    "节": "亨，苦节不可贞",
    "中孚": "豚鱼吉，利涉大川",
    "既济": "亨，小利贞，初吉终乱",
    "未济": "亨，小狐汔济，濡其尾",
}

YAO_TEMPLATES = [
    "初爻：先别急，先定边界。",
    "二爻：能动，但别一次推满。",
    "三爻：这里要看时机，不宜硬冲。",
    "四爻：有转机，但要先稳住。",
    "五爻：可以推进，但要留余地。",
    "上爻：收一收，避免过头。",
]

HEAVENLY_STEMS = [
    ("甲", 0), ("乙", 1), ("丙", 2), ("丁", 3), ("戊", 4),
    ("己", 5), ("庚", 6), ("辛", 7), ("壬", 8), ("癸", 9),
]

EARTHLY_BRANCHES = [
    ("子", 0), ("丑", 1), ("寅", 2), ("卯", 3), ("辰", 4), ("巳", 5),
    ("午", 6), ("未", 7), ("申", 8), ("酉", 9), ("戌", 10), ("亥", 11),
]

WUXING_OF_STEM = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

WUXING_OF_BRANCH = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

YINYANG_OF_STEM = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}

NAYIN_TABLE = {
    "甲子": "海中金", "乙丑": "海中金", "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木", "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金", "甲戌": "山头火", "乙亥": "山头火",
    "丙子": "涧下水", "丁丑": "涧下水", "戊寅": "城头土", "己卯": "城头土",
    "庚辰": "白蜡金", "辛巳": "白蜡金", "壬午": "杨柳木", "癸未": "杨柳木",
    "甲申": "泉中水", "乙酉": "泉中水", "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火", "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水", "甲午": "砂石金", "乙未": "砂石金",
    "丙申": "山下火", "丁酉": "山下火", "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土", "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆灯火", "乙巳": "覆灯火", "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土", "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木", "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土", "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木", "壬戌": "大海水", "癸亥": "大海水",
}

SOLAR_TERMS_DATA = {
    2020: [("小寒", 1, 6), ("大寒", 1, 20), ("立春", 2, 4), ("雨水", 2, 19), ("惊蛰", 3, 5), ("春分", 3, 20), ("清明", 4, 4), ("谷雨", 4, 19), ("立夏", 5, 5), ("小满", 5, 20), ("芒种", 6, 5), ("夏至", 6, 21), ("小暑", 7, 6), ("大暑", 7, 22), ("立秋", 8, 7), ("处暑", 8, 22), ("白露", 9, 7), ("秋分", 9, 22), ("寒露", 10, 8), ("霜降", 10, 23), ("立冬", 11, 7), ("小雪", 11, 22), ("大雪", 12, 7), ("冬至", 12, 21)],
    2021: [("小寒", 1, 5), ("大寒", 1, 20), ("立春", 2, 3), ("雨水", 2, 18), ("惊蛰", 3, 5), ("春分", 3, 20), ("清明", 4, 4), ("谷雨", 4, 20), ("立夏", 5, 5), ("小满", 5, 21), ("芒种", 6, 5), ("夏至", 6, 21), ("小暑", 7, 7), ("大暑", 7, 22), ("立秋", 8, 7), ("处暑", 8, 23), ("白露", 9, 7), ("秋分", 9, 23), ("寒露", 10, 8), ("霜降", 10, 23), ("立冬", 11, 7), ("小雪", 11, 22), ("大雪", 12, 7), ("冬至", 12, 21)],
    2022: [("小寒", 1, 5), ("大寒", 1, 20), ("立春", 2, 4), ("雨水", 2, 19), ("惊蛰", 3, 5), ("春分", 3, 20), ("清明", 4, 5), ("谷雨", 4, 20), ("立夏", 5, 5), ("小满", 5, 21), ("芒种", 6, 6), ("夏至", 6, 21), ("小暑", 7, 7), ("大暑", 7, 23), ("立秋", 8, 7), ("处暑", 8, 23), ("白露", 9, 7), ("秋分", 9, 23), ("寒露", 10, 8), ("霜降", 10, 23), ("立冬", 11, 7), ("小雪", 11, 22), ("大雪", 12, 7), ("冬至", 12, 22)],
    2023: [("小寒", 1, 5), ("大寒", 1, 20), ("立春", 2, 4), ("雨水", 2, 19), ("惊蛰", 3, 6), ("春分", 3, 21), ("清明", 4, 5), ("谷雨", 4, 20), ("立夏", 5, 6), ("小满", 5, 21), ("芒种", 6, 6), ("夏至", 6, 21), ("小暑", 7, 7), ("大暑", 7, 23), ("立秋", 8, 8), ("处暑", 8, 23), ("白露", 9, 8), ("秋分", 9, 23), ("寒露", 10, 8), ("霜降", 10, 24), ("立冬", 11, 8), ("小雪", 11, 22), ("大雪", 12, 7), ("冬至", 12, 22)],
    2024: [("小寒", 1, 6), ("大寒", 1, 20), ("立春", 2, 4), ("雨水", 2, 19), ("惊蛰", 3, 5), ("春分", 3, 20), ("清明", 4, 4), ("谷雨", 4, 19), ("立夏", 5, 5), ("小满", 5, 20), ("芒种", 6, 5), ("夏至", 6, 21), ("小暑", 7, 6), ("大暑", 7, 22), ("立秋", 8, 7), ("处暑", 8, 22), ("白露", 9, 7), ("秋分", 9, 22), ("寒露", 10, 8), ("霜降", 10, 23), ("立冬", 11, 7), ("小雪", 11, 22), ("大雪", 12, 6), ("冬至", 12, 21)],
    2025: [("小寒", 1, 5), ("大寒", 1, 20), ("立春", 2, 3), ("雨水", 2, 18), ("惊蛰", 3, 5), ("春分", 3, 20), ("清明", 4, 4), ("谷雨", 4, 20), ("立夏", 5, 5), ("小满", 5, 21), ("芒种", 6, 5), ("夏至", 6, 21), ("小暑", 7, 7), ("大暑", 7, 22), ("立秋", 8, 7), ("处暑", 8, 23), ("白露", 9, 7), ("秋分", 9, 23), ("寒露", 10, 8), ("霜降", 10, 23), ("立冬", 11, 7), ("小雪", 11, 22), ("大雪", 12, 7), ("冬至", 12, 21)],
    2026: [("小寒", 1, 5), ("大寒", 1, 20), ("立春", 2, 4), ("雨水", 2, 18), ("惊蛰", 3, 5), ("春分", 3, 20), ("清明", 4, 5), ("谷雨", 4, 20), ("立夏", 5, 5), ("小满", 5, 21), ("芒种", 6, 5), ("夏至", 6, 21), ("小暑", 7, 7), ("大暑", 7, 22), ("立秋", 8, 7), ("处暑", 8, 23), ("白露", 9, 7), ("秋分", 9, 23), ("寒露", 10, 8), ("霜降", 10, 23), ("立冬", 11, 7), ("小雪", 11, 22), ("大雪", 12, 7), ("冬至", 12, 21)],
}

GROUNDING_SNIPPETS = [
    "乾卦：元亨利贞，刚健中正。",
    "坤卦：厚德载物，柔顺承载。",
    "泰卦：小往大来，先通后成。",
    "否卦：上下不交，先收后进。",
    "需卦：有孚光亨，宜等待时机。",
    "讼卦：有孚窒惕，宜先化解冲突。",
    "中孚：讲真诚，别硬拗。",
    "未济：事未成，先稳住再推进。",
]


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _stable_seed(*parts: Any) -> int:
    joined = "||".join(_normalize_text(part) for part in parts if _normalize_text(part))
    if not joined:
        joined = "zhouyi"
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _make_rng(*parts: Any) -> random.Random:
    return random.Random(_stable_seed(*parts))


def _build_line_templates() -> list[str]:
    return YAO_TEMPLATES[:]


def _hexagram_lookup(binary: str) -> tuple[int, str]:
    return HEXAGRAM_MAP.get(binary, (1, "乾"))


def _hexagram_meaning(name: str) -> str:
    return HEXAGRAM_MEANINGS.get(name, "顺势而行，先观察再动作")


def _build_hexagram(mode: str, question: str, cast_seed: str = "") -> dict[str, Any]:
    rng = _make_rng(mode, question, cast_seed or datetime.now().isoformat(timespec="minutes"))
    lines: list[dict[str, Any]] = []
    for index in range(6):
        coins = [2 if rng.random() < 0.5 else 3 for _ in range(3)]
        total = sum(coins)
        is_yang = total % 2 == 1
        is_changing = total in {6, 9}
        lines.append(
            {
                "position": index + 1,
                "is_changing": is_changing,
                "yin_yang": "阳" if is_yang else "阴",
                "text": f"{'九' if is_yang else '六'}{'（动）' if is_changing else ''}",
            }
        )

    binary = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines)
    hexagram_number, name = _hexagram_lookup(binary)
    upper = TRIGRAMS[_trigram_index(lines[:3])]
    lower = TRIGRAMS[_trigram_index(lines[3:])]
    changing_lines = [item["position"] for item in lines if item["is_changing"]]
    summary = f"{MODE_LABELS.get(mode, '周易')}" if mode else "周易"
    summary = f"所得卦象为{name}卦（第{hexagram_number}卦），{_hexagram_meaning(name)}。"
    if changing_lines:
        summary += f" 动爻在第{'、'.join(str(item) for item in changing_lines)}爻。"
    else:
        summary += " 暂无动爻，先看整体趋势。"
    summary += " 先稳住节奏，再决定要不要推进。"

    cards = [
        {"label": "卦名", "value": f"{name}卦"},
        {"label": "上下卦", "value": f"{upper['name']} / {lower['name']}"},
        {"label": "动爻", "value": "、".join(str(item) for item in changing_lines) if changing_lines else "无"},
        {"label": "卦意", "value": _hexagram_meaning(name)},
    ]
    suggestions = [
        "先看趋势，不要急着把话说死。",
        "如果有动爻，优先关注变化位。",
        "节奏上先稳，再判断下一步。",
    ]

    return {
        "method_label": MODE_LABELS.get(mode, "周易64卦"),
        "question": question,
        "summary": summary,
        "cards": cards,
        "suggestions": suggestions,
        "raw_result": {
            "upper_trigram": upper["name"],
            "lower_trigram": lower["name"],
            "hexagram_number": hexagram_number,
            "hexagram_name": name,
            "changing_lines": changing_lines,
            "lines": lines,
        },
    }


def _trigram_index(lines: list[dict[str, Any]]) -> int:
    binary = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines)
    mapping = {
        "111": 0,
        "110": 1,
        "101": 2,
        "100": 3,
        "011": 4,
        "010": 5,
        "001": 6,
        "000": 7,
    }
    return mapping.get(binary, 0)


def _solar_term_month(year: int, month: int, day: int) -> int:
    terms = SOLAR_TERMS_DATA.get(year)
    if not terms:
        return month
    current_date = date(year, month, day)
    result_month = month
    for name, term_month, term_day in terms[::-1]:
        if name not in {"立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"}:
            continue
        term_date = date(year, term_month, term_day)
        if current_date >= term_date:
            result_month = {
                "立春": 1,
                "惊蛰": 2,
                "清明": 3,
                "立夏": 4,
                "芒种": 5,
                "小暑": 6,
                "立秋": 7,
                "白露": 8,
                "寒露": 9,
                "立冬": 10,
                "大雪": 11,
                "小寒": 12,
            }[name]
            break
    return result_month


def _is_before_lichun(year: int, month: int, day: int) -> bool:
    terms = SOLAR_TERMS_DATA.get(year)
    if not terms:
        return False
    lichun = next((item for item in terms if item[0] == "立春"), None)
    if not lichun:
        return False
    return date(year, month, day) < date(year, lichun[1], lichun[2])


def _get_year_stem(year: int) -> tuple[str, int]:
    index = (year - 3) % 10
    return HEAVENLY_STEMS[index]


def _get_year_branch(year: int) -> tuple[str, int]:
    index = (year - 3) % 12
    return EARTHLY_BRANCHES[index]


def _get_year_stem_branch(year: int, month: int, day: int) -> tuple[tuple[str, int], tuple[str, int]]:
    actual_year = year - 1 if _is_before_lichun(year, month, day) else year
    return _get_year_stem(actual_year), _get_year_branch(actual_year)


def _get_month_branch(month: int) -> tuple[str, int]:
    month_to_branch = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]
    index = month_to_branch[(month - 1) % 12]
    return EARTHLY_BRANCHES[index]


def _get_month_stem(year_stem_index: int, month: int) -> tuple[str, int]:
    month_stem_index = (year_stem_index % 5 * 2 + month) % 10
    return HEAVENLY_STEMS[month_stem_index]


def _get_month_stem_branch(year: int, month: int, day: int) -> tuple[tuple[str, int], tuple[str, int]]:
    actual_year = year - 1 if _is_before_lichun(year, month, day) else year
    year_stem = _get_year_stem(actual_year)
    solar_term_month = _solar_term_month(year, month, day)
    return _get_month_stem(year_stem[1], solar_term_month), _get_month_branch(solar_term_month)


def _get_day_stem_branch(year: int, month: int, day: int) -> tuple[tuple[str, int], tuple[str, int]]:
    base_date = date(2000, 1, 7)
    target_date = date(year, month, day)
    days_diff = (target_date - base_date).days
    stem_index = days_diff % 10
    branch_index = days_diff % 12
    return HEAVENLY_STEMS[stem_index], EARTHLY_BRANCHES[branch_index]


def _get_hour_branch(hour: int) -> tuple[str, int]:
    index = (hour // 2) % 12
    return EARTHLY_BRANCHES[index]


def _get_hour_stem(day_stem: tuple[str, int], hour: int) -> tuple[str, int]:
    day_stem_index = day_stem[1]
    hour_branch_index = ((hour + 1) % 24) // 2
    hour_stem_index = ((day_stem_index * 2 + hour_branch_index) % 10 + 10) % 10
    return HEAVENLY_STEMS[hour_stem_index]


def _get_nayin(stem_name: str, branch_name: str) -> str:
    return NAYIN_TABLE.get(f"{stem_name}{branch_name}", "")


def _wuxing_distribution(pillars: list[tuple[tuple[str, int], tuple[str, int]]]) -> Counter[str]:
    counter: Counter[str] = Counter({"木": 0, "火": 0, "土": 0, "金": 0, "水": 0})
    for stem, branch in pillars:
        counter[WUXING_OF_STEM.get(stem[0], "")] += 1
        counter[WUXING_OF_BRANCH.get(branch[0], "")] += 1
    return counter


def _build_bazi_result(question: str, birth_year: int, birth_month: int, birth_day: int, birth_hour: int, gender: str) -> dict[str, Any]:
    year_pillar = _get_year_stem_branch(birth_year, birth_month, birth_day)
    month_pillar = _get_month_stem_branch(birth_year, birth_month, birth_day)
    day_pillar = _get_day_stem_branch(birth_year, birth_month, birth_day)
    hour_branch = _get_hour_branch(birth_hour)
    hour_stem = _get_hour_stem(day_pillar[0], birth_hour)

    pillars = [year_pillar, month_pillar, day_pillar, (hour_stem, hour_branch)]
    distribution = _wuxing_distribution(pillars)
    day_element = WUXING_OF_STEM.get(day_pillar[0][0], "")
    day_score = distribution.get(day_element, 0)
    if day_score >= 4:
        day_state = "偏旺"
    elif day_score >= 2:
        day_state = "中和"
    else:
        day_state = "偏弱"

    favor_elements = ["火", "土"] if day_state != "偏旺" else ["水", "木"]
    avoid_elements = ["金"] if day_state != "偏弱" else ["火", "土"]
    summary = (
        f"四柱：{year_pillar[0][0]}{year_pillar[1][0]} {month_pillar[0][0]}{month_pillar[1][0]} "
        f"{day_pillar[0][0]}{day_pillar[1][0]} {hour_stem[0]}{hour_branch[0]}。"
        f"五行：木{distribution['木']}、火{distribution['火']}、土{distribution['土']}、金{distribution['金']}、水{distribution['水']}。"
        f"日主{day_pillar[0][0]}({day_element}){day_state}。"
    )
    cards = [
        {"label": "年柱", "value": f"{year_pillar[0][0]}{year_pillar[1][0]}"},
        {"label": "月柱", "value": f"{month_pillar[0][0]}{month_pillar[1][0]}"},
        {"label": "日柱", "value": f"{day_pillar[0][0]}{day_pillar[1][0]}"},
        {"label": "时柱", "value": f"{hour_stem[0]}{hour_branch[0]}"},
        {"label": "五行", "value": f"木{distribution['木']} 火{distribution['火']} 土{distribution['土']} 金{distribution['金']} 水{distribution['水']}"},
        {"label": "日主", "value": f"{day_pillar[0][0]}({day_element}) {day_state}"},
        {"label": "纳音", "value": " / ".join(filter(None, [
            _get_nayin(*year_pillar[0]),
            _get_nayin(*month_pillar[0]),
            _get_nayin(*day_pillar[0]),
            _get_nayin(*hour_stem),
        ])) or "未展开"},
    ]
    suggestions = [
        f"当前更适合优先补{favor_elements[0]}、{favor_elements[1]}的节奏。",
        "先看整体平衡，再决定是否加速。",
        "如果是长期问题，先稳结构；如果是短期问题，先定边界。",
    ]
    return {
        "method_label": "八字排盘",
        "question": question,
        "summary": summary + " 先看平衡，再定动作。",
        "cards": cards,
        "suggestions": suggestions,
        "raw_result": {
            "year_pillar": f"{year_pillar[0][0]}{year_pillar[1][0]}",
            "month_pillar": f"{month_pillar[0][0]}{month_pillar[1][0]}",
            "day_pillar": f"{day_pillar[0][0]}{day_pillar[1][0]}",
            "hour_pillar": f"{hour_stem[0]}{hour_branch[0]}",
            "distribution": dict(distribution),
            "day_state": day_state,
            "gender": gender or "unknown",
        },
    }


async def _interpret_with_llm(mode: str, question: str, base_result: dict[str, Any], db: Session | None) -> tuple[str, str]:
    system_prompt = (
        "你是 Tokendancer 的「我该怎么做」解释器。"
        "请把周易64卦、六爻或八字结果翻译成一句能看懂、能行动的建议。"
        "不要讲模型过程，不要写长篇，不要输出标题，只输出一段自然中文。"
        "如果是卦象，重点说趋势、时机、风险；如果是八字，重点说节奏、平衡和长期倾向。"
        "语气要克制、清楚、可执行。"
    )
    user_prompt = json.dumps(
        {
            "mode": mode,
            "question": question,
            "base_result": base_result,
            "grounding_snippets": GROUNDING_SNIPPETS,
            "output_goal": "用 3 到 5 句给出简短解释和建议",
        },
        ensure_ascii=False,
        indent=2,
    )
    reply = await generate_reply(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        db=db,
    )
    return str(reply.get("content") or "").strip(), str(reply.get("model") or "")


def _fallback_interpretation(mode: str, base_result: dict[str, Any]) -> str:
    summary = _normalize_text(base_result.get("summary"))
    suggestions = base_result.get("suggestions")
    suggestion_text = " ".join(_normalize_text(item) for item in suggestions or [] if _normalize_text(item))
    if mode == "bazi":
        return f"{summary} {suggestion_text}".strip()
    return f"{summary} {suggestion_text}".strip()


async def generate_how_to_do_runtime(request: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    mode = _normalize_text(request.get("mode")) or "zhouyi"
    question = _normalize_text(request.get("question"))
    cast_seed = _normalize_text(request.get("cast_seed"))
    use_ai = bool(request.get("use_ai", True))

    if mode in {"zhouyi", "liuyao"}:
        base_result = _build_hexagram(mode, question, cast_seed)
    elif mode == "bazi":
        birth_year = int(request.get("birth_year") or 0)
        birth_month = int(request.get("birth_month") or 0)
        birth_day = int(request.get("birth_day") or 0)
        birth_hour = int(request.get("birth_hour") or 0)
        if not all([birth_year, birth_month, birth_day]) or birth_hour < 0:
            raise ValueError("八字模式需要完整的出生年月日时")
        base_result = _build_bazi_result(
            question=question,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            gender=_normalize_text(request.get("gender")) or "unknown",
        )
    else:
        raise ValueError(f"不支持的模式: {mode}")

    ai_interpretation = _fallback_interpretation(mode, base_result)
    model_used = ""
    if use_ai and db is not None:
        try:
            ai_text, model_used = await _interpret_with_llm(mode, question, base_result, db)
            if ai_text:
                ai_interpretation = strip_think_blocks(ai_text).strip()
        except LLMGatewayError:
            model_used = ""
        except Exception:
            model_used = ""

    return {
        "mode": mode,
        "method_label": base_result.get("method_label", MODE_LABELS.get(mode, "我该怎么做")),
        "question": question,
        "summary": _normalize_text(base_result.get("summary")),
        "cards": base_result.get("cards", []),
        "ai_interpretation": ai_interpretation,
        "suggestions": base_result.get("suggestions", []),
        "raw_result": base_result.get("raw_result", {}),
        "model_used": model_used,
    }
