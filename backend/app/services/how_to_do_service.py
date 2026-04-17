from __future__ import annotations

import hashlib
import json
import random
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Any

from sqlalchemy.orm import Session

from app.services.llm_gateway import LLMGatewayError, generate_reply
from app.services.text_sanitizer import strip_think_blocks


SECTION_LABELS = {
    "cast": "排盘",
    "sundial": "日晷",
    "catalog": "六十四卦",
    "songs": "歌诀",
    "detail": "卦象详情",
}

CAST_MODE_LABELS = {
    "manual": "手动输入",
    "character": "汉字起卦",
    "number": "数字起卦",
    "coin": "硬币起卦",
    "taiji": "太极丸起卦",
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
    "010000": (7, "师"),
    "000010": (8, "比"),
    "111011": (9, "小畜"),
    "110111": (10, "履"),
    "111000": (11, "泰"),
    "000111": (12, "否"),
    "101111": (13, "同人"),
    "111101": (14, "大有"),
    "001000": (15, "谦"),
    "000100": (16, "豫"),
    "100110": (17, "随"),
    "011001": (18, "蛊"),
    "110000": (19, "临"),
    "000011": (20, "观"),
    "100101": (21, "噬嗑"),
    "101001": (22, "贲"),
    "000001": (23, "剥"),
    "100000": (24, "复"),
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
    "乾": "元亨利贞，刚健中正", "坤": "厚德载物，柔顺承载", "屯": "起步艰难，先立根基", "蒙": "启蒙求教，先明边界",
    "需": "等待时机，蓄势再动", "讼": "有争执，先化解冲突", "师": "有组织有纪律，稳住阵脚", "比": "靠拢协作，重在同心",
    "小畜": "小有积蓄，先蓄再发", "履": "步步谨慎，先看规则", "泰": "上下相通，局势顺畅", "否": "上下不交，先收后进",
    "同人": "同心协力，利于共识", "大有": "资源丰厚，宜守成", "谦": "谦受益，低调稳进", "豫": "有喜有动，先定节奏",
    "随": "顺势而为，但别失主见", "蛊": "旧局待修，先整再动", "临": "临近成局，重在把握", "观": "先观察，再决定动作",
    "噬嗑": "有阻则断，需果断处理", "贲": "外在修饰，内核要稳", "剥": "剥落之势，宜保守", "复": "回到起点，重新来过",
    "无妄": "顺其自然，不宜妄动", "大畜": "蓄养力量，耐心等待", "颐": "养身养心，注意入口", "大过": "压力偏大，别硬扛",
    "坎": "险中求通，先保安全", "离": "明而有附，重在清晰", "咸": "感应相通，利于沟通", "恒": "持久之道，贵在稳定",
    "遁": "退一步海阔天空", "大壮": "势能上升，别冲过头", "晋": "进展上升，宜顺势", "明夷": "光被遮蔽，先藏锋",
    "家人": "内在秩序，先顾内里", "睽": "分歧并存，先求对齐", "蹇": "阻碍较多，宜绕行", "解": "困难解开，顺势松绑",
    "损": "有所舍弃，换取长远", "益": "增益之象，利于推进", "夬": "决断之时，别拖延", "姤": "相遇突发，谨慎处理",
    "萃": "聚集成势，利于集中", "升": "稳步上升，循序渐进", "困": "受困受限，先找出口", "井": "资源可用，重在维护",
    "革": "变革更新，先定方向", "鼎": "承载转化，适合定型", "震": "突发变动，先稳住", "艮": "止而不动，先收住",
    "渐": "循序渐进，不可急进", "归妹": "关系不稳，需慎重", "丰": "盛极一时，注意收敛", "旅": "在外求行，先安顿",
    "巽": "渗透推进，柔中有力", "兑": "交流顺畅，利于沟通", "涣": "离散化解，先疏后聚", "节": "有节有度，守住边界",
    "中孚": "诚信内在，沟通更稳", "小过": "小事可成，不宜过大", "既济": "事情已成，注意后续", "未济": "未成之局，先别定论",
}

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

HEXAGRAM_SPECS = {
    "乾": {"palace": "乾宫", "tag": "六冲"},
    "姤": {"palace": "乾宫", "tag": "一世"},
    "遁": {"palace": "乾宫", "tag": "二世"},
    "否": {"palace": "乾宫", "tag": "三世"},
    "观": {"palace": "乾宫", "tag": "四世"},
    "剥": {"palace": "乾宫", "tag": "五世"},
    "晋": {"palace": "乾宫", "tag": "游魂"},
    "大有": {"palace": "乾宫", "tag": "归魂"},
    "兑": {"palace": "兑宫", "tag": "六冲"},
    "困": {"palace": "兑宫", "tag": "一世"},
    "萃": {"palace": "兑宫", "tag": "二世"},
    "咸": {"palace": "兑宫", "tag": "三世"},
    "蹇": {"palace": "兑宫", "tag": "四世"},
    "谦": {"palace": "兑宫", "tag": "五世"},
    "小过": {"palace": "兑宫", "tag": "游魂"},
    "归妹": {"palace": "兑宫", "tag": "归魂"},
    "离": {"palace": "离宫", "tag": "六冲"},
    "旅": {"palace": "离宫", "tag": "一世"},
    "鼎": {"palace": "离宫", "tag": "二世"},
    "未济": {"palace": "离宫", "tag": "三世"},
    "蒙": {"palace": "离宫", "tag": "四世"},
    "涣": {"palace": "离宫", "tag": "五世"},
    "讼": {"palace": "离宫", "tag": "游魂"},
    "同人": {"palace": "离宫", "tag": "归魂"},
    "震": {"palace": "震宫", "tag": "六冲"},
    "豫": {"palace": "震宫", "tag": "一世"},
    "解": {"palace": "震宫", "tag": "二世"},
    "恒": {"palace": "震宫", "tag": "三世"},
    "升": {"palace": "震宫", "tag": "四世"},
    "井": {"palace": "震宫", "tag": "五世"},
    "大过": {"palace": "震宫", "tag": "游魂"},
    "随": {"palace": "震宫", "tag": "归魂"},
    "巽": {"palace": "巽宫", "tag": "六冲"},
    "小畜": {"palace": "巽宫", "tag": "一世"},
    "家人": {"palace": "巽宫", "tag": "二世"},
    "益": {"palace": "巽宫", "tag": "三世"},
    "无妄": {"palace": "巽宫", "tag": "四世"},
    "噬嗑": {"palace": "巽宫", "tag": "五世"},
    "颐": {"palace": "巽宫", "tag": "游魂"},
    "蛊": {"palace": "巽宫", "tag": "归魂"},
    "坎": {"palace": "坎宫", "tag": "六冲"},
    "节": {"palace": "坎宫", "tag": "一世"},
    "屯": {"palace": "坎宫", "tag": "二世"},
    "既济": {"palace": "坎宫", "tag": "三世"},
    "革": {"palace": "坎宫", "tag": "四世"},
    "丰": {"palace": "坎宫", "tag": "五世"},
    "明夷": {"palace": "坎宫", "tag": "游魂"},
    "师": {"palace": "坎宫", "tag": "归魂"},
    "艮": {"palace": "艮宫", "tag": "六冲"},
    "贲": {"palace": "艮宫", "tag": "一世"},
    "大畜": {"palace": "艮宫", "tag": "二世"},
    "损": {"palace": "艮宫", "tag": "三世"},
    "睽": {"palace": "艮宫", "tag": "四世"},
    "履": {"palace": "艮宫", "tag": "五世"},
    "中孚": {"palace": "艮宫", "tag": "游魂"},
    "渐": {"palace": "艮宫", "tag": "归魂"},
    "坤": {"palace": "坤宫", "tag": "六冲"},
    "复": {"palace": "坤宫", "tag": "一世"},
    "临": {"palace": "坤宫", "tag": "二世"},
    "泰": {"palace": "坤宫", "tag": "三世"},
    "大壮": {"palace": "坤宫", "tag": "四世"},
    "夬": {"palace": "坤宫", "tag": "五世"},
    "需": {"palace": "坤宫", "tag": "游魂"},
    "比": {"palace": "坤宫", "tag": "归魂"},
}

GROUNDING_SNIPPETS = [
    "六爻更适合先看局势变化，再决定进退。",
    "有动爻时，先看变化位，再看整体趋势。",
    "变卦代表后势，不要只盯着本卦。",
    "时间起卦适合快速问事，手动起卦适合更明确的起卦过程。",
]

LINE_GUIDANCE = [
    "起点和底盘，先看稳不稳。",
    "基础承接位，先看配合。",
    "变化开始显现，别硬顶。",
    "外部推动与阻力，要看清。",
    "核心主位，决定当前走势。",
    "收尾与结果，别把话说满。",
]

SIX_SPIRITS = ["玄武", "白虎", "螣蛇", "勾陈", "朱雀", "青龙"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
RELATIONS = ["父母", "兄弟", "子孙", "妻财", "官鬼"]

PALACE_GUA_CATALOG = [
    (
        "乾宫",
        [
            ("乾为天", "六冲", "乾"),
            ("天风姤", "一世", "姤"),
            ("天山遁", "二世", "遁"),
            ("天地否", "三世", "否"),
            ("风地观", "四世", "观"),
            ("山地剥", "五世", "剥"),
            ("火地晋", "游魂", "晋"),
            ("火天大有", "归魂", "大有"),
        ],
    ),
    (
        "兑宫",
        [
            ("兑为泽", "六冲", "兑"),
            ("泽水困", "一世", "困"),
            ("泽地萃", "二世", "萃"),
            ("泽山咸", "三世", "咸"),
            ("水山蹇", "四世", "蹇"),
            ("地山谦", "五世", "谦"),
            ("雷山小过", "游魂", "小过"),
            ("雷泽归妹", "归魂", "归妹"),
        ],
    ),
    (
        "离宫",
        [
            ("离为火", "六冲", "离"),
            ("火山旅", "一世", "旅"),
            ("火风鼎", "二世", "鼎"),
            ("火水未济", "三世", "未济"),
            ("山水蒙", "四世", "蒙"),
            ("风水涣", "五世", "涣"),
            ("天水讼", "游魂", "讼"),
            ("天火同人", "归魂", "同人"),
        ],
    ),
    (
        "震宫",
        [
            ("震为雷", "六冲", "震"),
            ("雷地豫", "一世", "豫"),
            ("雷水解", "二世", "解"),
            ("雷风恒", "三世", "恒"),
            ("地风升", "四世", "升"),
            ("水风井", "五世", "井"),
            ("泽风大过", "游魂", "大过"),
            ("泽雷随", "归魂", "随"),
        ],
    ),
    (
        "巽宫",
        [
            ("巽为风", "六冲", "巽"),
            ("风天小畜", "一世", "小畜"),
            ("风火家人", "二世", "家人"),
            ("风雷益", "三世", "益"),
            ("天雷无妄", "四世", "无妄"),
            ("火雷噬嗑", "五世", "噬嗑"),
            ("山雷颐", "游魂", "颐"),
            ("山风蛊", "归魂", "蛊"),
        ],
    ),
    (
        "坎宫",
        [
            ("坎为水", "六冲", "坎"),
            ("水泽节", "一世", "节"),
            ("水雷屯", "二世", "屯"),
            ("水火既济", "三世", "既济"),
            ("泽火革", "四世", "革"),
            ("雷火丰", "五世", "丰"),
            ("地火明夷", "游魂", "明夷"),
            ("地水师", "归魂", "师"),
        ],
    ),
    (
        "艮宫",
        [
            ("艮为山", "六冲", "艮"),
            ("山火贲", "一世", "贲"),
            ("山天大畜", "二世", "大畜"),
            ("山泽损", "三世", "损"),
            ("火泽睽", "四世", "睽"),
            ("天泽履", "五世", "履"),
            ("风泽中孚", "游魂", "中孚"),
            ("风山渐", "归魂", "渐"),
        ],
    ),
    (
        "坤宫",
        [
            ("坤为地", "六冲", "坤"),
            ("地雷复", "一世", "复"),
            ("地泽临", "二世", "临"),
            ("地天泰", "三世", "泰"),
            ("雷天大壮", "四世", "大壮"),
            ("泽天夬", "五世", "夬"),
            ("水天需", "游魂", "需"),
            ("水地比", "归魂", "比"),
        ],
    ),
]

HEXAGRAM_NAME_TO_BINARY = {name: binary for binary, (_, name) in HEXAGRAM_MAP.items()}

ALL_GUA_CATALOG = []
for palace_index, (palace, guas) in enumerate(PALACE_GUA_CATALOG):
    for order, (name, tag, meaning_key) in enumerate(guas, start=1):
        number = palace_index * 8 + order
        binary = HEXAGRAM_NAME_TO_BINARY.get(meaning_key, "")
        ALL_GUA_CATALOG.append(
            {
                "number": number,
                "name": name,
                "meaning": HEXAGRAM_MEANINGS.get(meaning_key, "顺势而行"),
                "binary": binary,
                "palace": palace,
                "tag": tag,
            }
        )


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _stable_seed(*parts: Any) -> int:
    joined = "||".join(_normalize_text(part) for part in parts if _normalize_text(part))
    if not joined:
        joined = "liu-yao"
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _make_rng(*parts: Any) -> random.Random:
    return random.Random(_stable_seed(*parts))


def _sexagenary_name(index: int) -> str:
    return f"{STEMS[index % 10]}{BRANCHES[index % 12]}"


def _year_ganzhi(dt: datetime) -> str:
    adjusted_year = dt.year - 1 if (dt.month, dt.day) < (2, 4) else dt.year
    return _sexagenary_name((adjusted_year - 1984) % 60)


def _month_branch_index(dt: datetime) -> int:
    mapping = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 11,
        12: 0,
    }
    branch_index = mapping.get(dt.month, 1)
    if dt.month == 1 and (dt.month, dt.day) < (2, 4):
        branch_index = 1
    return branch_index


def _month_ganzhi(dt: datetime) -> str:
    year_stem = _year_ganzhi(dt)[0]
    first_stem_map = {
        "甲": "丙",
        "己": "丙",
        "乙": "戊",
        "庚": "戊",
        "丙": "庚",
        "辛": "庚",
        "丁": "壬",
        "壬": "壬",
        "戊": "甲",
        "癸": "甲",
    }
    first_stem = first_stem_map[year_stem]
    branch_index = _month_branch_index(dt)
    month_offset = (branch_index - 2) % 12
    stem_index = (STEMS.index(first_stem) + month_offset) % 10
    return f"{STEMS[stem_index]}{BRANCHES[branch_index]}"


def _day_ganzhi(dt: datetime) -> str:
    jdn = dt.toordinal() + 1721424
    return _sexagenary_name((jdn + 49) % 60)


def _hour_branch_index(dt: datetime) -> int:
    return ((dt.hour + 1) // 2) % 12


def _hour_ganzhi(dt: datetime) -> str:
    day_stem = _day_ganzhi(dt)[0]
    first_stem_map = {
        "甲": "甲",
        "己": "甲",
        "乙": "丙",
        "庚": "丙",
        "丙": "戊",
        "辛": "戊",
        "丁": "庚",
        "壬": "庚",
        "戊": "壬",
        "癸": "壬",
    }
    first_stem = first_stem_map[day_stem]
    branch_index = _hour_branch_index(dt)
    stem_index = (STEMS.index(first_stem) + branch_index) % 10
    return f"{STEMS[stem_index]}{BRANCHES[branch_index]}"


def _xunkong(dt: datetime) -> str:
    day_index = (dt.toordinal() + 1721424 + 49) % 60
    groups = [
        ("戌", "亥"),
        ("申", "酉"),
        ("午", "未"),
        ("辰", "巳"),
        ("寅", "卯"),
        ("子", "丑"),
    ]
    empty_a, empty_b = groups[day_index // 10]
    return f"旬空{empty_a}{empty_b}"


def _ganzhi_line(dt: datetime) -> str:
    year = _year_ganzhi(dt)
    month = _month_ganzhi(dt)
    day = _day_ganzhi(dt)
    hour = _hour_ganzhi(dt)
    return f"{year}年{month}月{day}日{hour}时({_xunkong(dt)})"


def _line_text(position: int, yin_yang: str, is_changing: bool) -> str:
    prefix = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][position - 1]
    return f"{prefix}：{'阳' if yin_yang == '阳' else '阴'}{'（动）' if is_changing else ''}"


def _build_line_detail(position: int, line: dict[str, Any], seed: str, question: str) -> dict[str, Any]:
    rng = _make_rng(seed, question, position, line.get("yin_yang"))
    hidden_relation = rng.choice(RELATIONS)
    hidden_stem = rng.choice(["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"])
    hidden_branch = BRANCHES[(position + 2) % len(BRANCHES)]
    hidden_element = rng.choice(["金", "木", "水", "火", "土"])
    return {
        "position": position,
        "position_name": line["position_name"],
        "text": line["text"],
        "guidance": line["guidance"],
        "is_changing": line["is_changing"],
        "yin_yang": line["yin_yang"],
        "six_spirit": SIX_SPIRITS[(position - 1) % len(SIX_SPIRITS)],
        "relation": RELATIONS[(position - 1) % len(RELATIONS)],
        "stem_branch": f"{rng.choice(['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'])}{BRANCHES[(position - 1) % len(BRANCHES)]}",
        "nayin": rng.choice(["海中金", "炉中火", "大林木", "路旁土", "剑锋金", "山头火", "涧下水", "城头土"]),
        "hidden_spirit": f"{hidden_relation}{hidden_stem}{hidden_branch}{hidden_element}" if position == 5 else "",
        "shi_ying": "世" if position == 1 else "应" if position == 4 else "",
    }


def _binary_from_lines(lines: list[dict[str, Any]]) -> str:
    return "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines)


def _trigram_index(lines: list[dict[str, Any]]) -> int:
    binary = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines)
    mapping = {"111": 0, "110": 1, "101": 2, "100": 3, "011": 4, "010": 5, "001": 6, "000": 7}
    return mapping.get(binary, 0)


def _hexagram_lookup(binary: str) -> tuple[int, str]:
    return HEXAGRAM_MAP.get(binary, (1, "乾"))


def _hexagram_meaning(name: str) -> str:
    return HEXAGRAM_MEANINGS.get(name, "顺势而行，先观察再动作")


def _build_mutual_hexagram(lines: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(lines) < 5:
        return None
    upper_bits = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines[2:5])
    lower_bits = "".join("1" if item["yin_yang"] == "阳" else "0" for item in lines[1:4])
    if len(upper_bits) != 3 or len(lower_bits) != 3:
        return None
    upper = TRIGRAMS[_trigram_index([{"yin_yang": "阳" if ch == "1" else "阴"} for ch in upper_bits])]
    lower = TRIGRAMS[_trigram_index([{"yin_yang": "阳" if ch == "1" else "阴"} for ch in lower_bits])]
    hexagram_number, name = _hexagram_lookup(upper_bits + lower_bits)
    return {
        "hexagram_number": hexagram_number,
        "name": name,
        "meaning": _hexagram_meaning(name),
        "upper_trigram": upper["name"],
        "lower_trigram": lower["name"],
    }


def _build_lines(seed: str, mode: str, cast_mode: str, question: str, source_text: str = "", manual_lines: list[int] | None = None) -> list[dict[str, Any]]:
    rng = _make_rng(seed, mode, cast_mode, question, source_text)
    lines: list[dict[str, Any]] = []
    manual_lines = manual_lines or []
    for position in range(1, 7):
      # 6/7/8/9 代表老阴、少阳、少阴、老阳
        if cast_mode == "manual":
            if position <= len(manual_lines) and manual_lines[position - 1] in {6, 7, 8, 9}:
                value = manual_lines[position - 1]
            else:
                value = rng.choice([6, 7, 8, 9])
        elif cast_mode == "character":
            base = sum(ord(ch) for ch in source_text or question or seed) + position * 17
            value = [6, 7, 8, 9][base % 4]
        elif cast_mode == "number":
            digits = [int(ch) for ch in f"{source_text}{question}{seed}" if ch.isdigit()]
            base = sum(digits) + position * 11 if digits else _stable_seed("number", source_text, question, seed, position)
            value = [6, 7, 8, 9][base % 4]
        elif cast_mode == "taiji":
            base = _stable_seed("taiji", seed, question, position, source_text)
            value = [6, 7, 8, 9][base % 4]
        else:
            value = rng.choice([6, 7, 8, 9])
        is_yang = value in {7, 9}
        is_changing = value in {6, 9}
        lines.append(
            {
                "position": position,
                "position_name": ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][position - 1],
                "value": value,
                "is_changing": is_changing,
                "yin_yang": "阳" if is_yang else "阴",
                "text": _line_text(position, "阳" if is_yang else "阴", is_changing),
                "guidance": LINE_GUIDANCE[position - 1],
            }
        )
    return lines


def _build_cast_result(question: str, category: str, cast_mode: str, cast_seed: str, source_text: str = "", manual_lines: list[int] | None = None) -> dict[str, Any]:
    seed_value = cast_seed or datetime.now().isoformat(timespec="seconds")
    lines = _build_lines(seed_value, "cast", cast_mode, question, source_text, manual_lines=manual_lines)
    binary = _binary_from_lines(lines)
    hexagram_number, name = _hexagram_lookup(binary)
    upper = TRIGRAMS[_trigram_index(lines[3:])]
    lower = TRIGRAMS[_trigram_index(lines[:3])]
    changing_lines = [item["position"] for item in lines if item["is_changing"]]
    mutual_hexagram = _build_mutual_hexagram(lines)
    hexagram_spec = HEXAGRAM_SPECS.get(name, {"palace": "未知宫", "tag": ""})
    transformed_hexagram = None
    transformed_line_details: list[dict[str, Any]] = []
    if changing_lines:
        transformed_lines = [
            {
                **item,
                "is_changing": False,
                "yin_yang": "阴" if item["yin_yang"] == "阳" else "阳",
                "text": _line_text(item["position"], "阴" if item["yin_yang"] == "阳" else "阳", False),
            }
            for item in lines
        ]
        transformed_binary = _binary_from_lines(transformed_lines)
        transformed_number, transformed_name = _hexagram_lookup(transformed_binary)
        transformed_upper = TRIGRAMS[_trigram_index(transformed_lines[3:])]
        transformed_lower = TRIGRAMS[_trigram_index(transformed_lines[:3])]
        transformed_hexagram = {
            "hexagram_number": transformed_number,
            "name": transformed_name,
            "meaning": _hexagram_meaning(transformed_name),
            "upper_trigram": transformed_upper["name"],
            "lower_trigram": transformed_lower["name"],
        }
        transformed_line_details = [
            _build_line_detail(position, item, seed_value + "-transformed", question)
            for position, item in enumerate(transformed_lines, start=1)
        ]

    summary = (
        f"本卦为{name}卦（第{hexagram_number}卦），{_hexagram_meaning(name)}。"
        f" 起卦方式为{CAST_MODE_LABELS.get(cast_mode, '硬币起卦')}。"
    )
    if changing_lines:
        summary += f" 动爻在第{'、'.join(f'{item}爻' for item in changing_lines)}，"
        if transformed_hexagram:
            summary += f"变卦为{transformed_hexagram['name']}卦。"
    else:
        summary += " 暂无动爻，先看本卦整体趋势。"
    summary += " 六爻更适合先看变化，再定进退。"

    cards = [
        {"label": "起卦方式", "value": CAST_MODE_LABELS.get(cast_mode, "硬币起卦")},
        {"label": "本卦", "value": f"{name}卦"},
        {"label": "上下卦", "value": f"{upper['name']} / {lower['name']}"},
        {"label": "互卦", "value": f"{mutual_hexagram['name']}卦" if mutual_hexagram else "无"},
        {"label": "动爻", "value": "、".join(f"{item}爻" for item in changing_lines) if changing_lines else "无"},
        {"label": "变卦", "value": f"{transformed_hexagram['name']}卦" if transformed_hexagram else "无"},
        {"label": "问念", "value": question or "未填写"},
        {"label": "分类", "value": category or "未分类"},
    ]
    shen_sha = {
        "卦身": BRANCHES[_stable_seed(seed_value, question, "gua-shen") % len(BRANCHES)],
        "贵人": f"{BRANCHES[_stable_seed(seed_value, question, 'gui-ren-1') % len(BRANCHES)]}、{BRANCHES[_stable_seed(seed_value, question, 'gui-ren-2') % len(BRANCHES)]}",
        "驿马": BRANCHES[_stable_seed(seed_value, question, "yi-ma") % len(BRANCHES)],
        "羊刃": BRANCHES[_stable_seed(seed_value, question, "yang-ren") % len(BRANCHES)],
    }
    line_details = [_build_line_detail(position, item, seed_value, question) for position, item in enumerate(lines, start=1)]
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    day_label = now.strftime("%Y年%m月%d日%H:%M:%S %A")
    day_label = day_label.replace("Monday", "周一").replace("Tuesday", "周二").replace("Wednesday", "周三").replace("Thursday", "周四").replace("Friday", "周五").replace("Saturday", "周六").replace("Sunday", "周日")
    panel_title = f"{lower['meaning']}{upper['meaning']}{name}"
    panel_subtitle = f"{hexagram_spec['palace'].replace('宫', '')}·{hexagram_spec['tag']}" if hexagram_spec["tag"] else hexagram_spec["palace"].replace("宫", "")
    time_line = f"{now.strftime('%Y年%m月%d日%H:%M:%S')} {day_label.split(' ')[-1]}农历三月初二"
    ganzhi_line = _ganzhi_line(now)
    suggestions = [
        "先看动爻在哪一层，再判断该守还是该推。",
        "有变卦时，优先看变化方向，不要只盯本卦。",
        "六爻更适合看当前局势，先定节奏再动作。",
    ]

    return {
        "method_label": "排盘",
        "question": question,
        "summary": summary,
        "cards": cards,
        "suggestions": suggestions,
        "raw_result": {
            "cast_mode": cast_mode,
            "hexagram_number": hexagram_number,
            "hexagram_name": name,
            "hexagram_meaning": _hexagram_meaning(name),
            "upper_trigram": upper["name"],
            "lower_trigram": lower["name"],
            "mutual_hexagram": mutual_hexagram,
            "binary": binary,
            "changing_lines": changing_lines,
            "lines": lines,
            "line_details": line_details,
            "transformed_hexagram": transformed_hexagram,
            "transformed_line_details": transformed_line_details,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "day_label": time_line,
            "ganzhi_line": ganzhi_line,
            "panel_title": panel_title,
            "panel_subtitle": panel_subtitle,
            "hexagram_tag": hexagram_spec["tag"],
            "hexagram_palace": hexagram_spec["palace"],
            "category": category or "未分类",
            "shensha": shen_sha,
        },
    }


def _build_catalog_result() -> dict[str, Any]:
    cards = [
        {"label": f"{item['number']} {item['name']}", "value": item["meaning"]}
        for item in ALL_GUA_CATALOG
    ]
    return {
        "method_label": "六十四卦",
        "question": "",
        "summary": "六十四卦库，点开任意一卦即可查看名称与卦意。",
        "cards": cards,
        "suggestions": ["可直接在卦库中搜索卦名。", "需要查看完整内容时，继续向下浏览。"],
        "raw_result": {"catalog": ALL_GUA_CATALOG},
    }


def _build_reference_result() -> dict[str, Any]:
    now = datetime.now()
    return {
        "method_label": "日晷",
        "question": "",
        "summary": "当前时间、日期、节气与时辰参考，放在这里先看时势。",
        "cards": [
            {"label": "当前时间", "value": now.strftime("%Y-%m-%d %H:%M:%S")},
            {"label": "中国时区", "value": "Asia/Shanghai"},
            {"label": "节气参考", "value": "当前节气与下一节气可由前端展示。"},
            {"label": "更新时间", "value": now.strftime("%Y-%m-%d %H:%M:%S")},
            {"label": "提示", "value": "日晷页只看时势，不替代排盘。"},
        ],
        "suggestions": ["如果要进一步判断，回到排盘页看本卦、互卦和变卦。"],
        "raw_result": {
            "sundial": {"timestamp": now.isoformat(timespec="seconds")},
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "date_text": date.today().isoformat(),
        },
    }


def _build_calendar_result() -> dict[str, Any]:
    today = date.today()
    summary = f"当前日期为 {today.isoformat()}，可作为时间参考。"
    return {
        "method_label": "日历",
        "question": "",
        "summary": summary,
        "cards": [
            {"label": "公历日期", "value": today.isoformat()},
            {"label": "星期", "value": today.strftime("%A")},
            {"label": "建议", "value": "可直接用今天时间起卦。"},
        ],
        "suggestions": ["如果要问今天的局势，可切回起卦页直接用当前时间。"],
        "raw_result": {"date": today.isoformat(), "weekday": today.strftime("%A")},
    }


def _build_clock_result() -> dict[str, Any]:
    now = datetime.now()
    summary = f"当前时间为 {now.strftime('%Y-%m-%d %H:%M:%S')}。"
    return {
        "method_label": "时钟",
        "question": "",
        "summary": summary,
        "cards": [
            {"label": "当前时间", "value": now.strftime("%Y-%m-%d %H:%M:%S")},
            {"label": "当前小时", "value": now.strftime("%H:00")},
            {"label": "建议", "value": "可直接按当前时间起卦。"},
        ],
        "suggestions": ["想用时间起卦时，直接切回起卦页。"],
        "raw_result": {"timestamp": now.isoformat(timespec="seconds")},
    }


def _build_records_result() -> dict[str, Any]:
    return {
        "method_label": "记录",
        "question": "",
        "summary": "记录由前端本地保存，方便回看最近的六爻结果。",
        "cards": [
            {"label": "记录位置", "value": "浏览器本地"},
            {"label": "说明", "value": "不会影响其他页面。"},
        ],
        "suggestions": ["可在前端保存最近的起卦记录。"],
        "raw_result": {"storage": "local"},
    }


def _build_songs_result() -> dict[str, Any]:
    built_in_songs = [
        {
            "title": "浑天甲子歌",
            "content": "干金甲子外壬午，坎水戊寅外戊申。震木庚子外庚午，艮土丙辰外丙戌。坤土乙未外癸丑，巽木辛丑外辛未。离火己卯外己酉，兑金丁巳外丁亥。",
        },
        {
            "title": "天干与内脏关系对应",
            "content": "甲肝乙胆丙小肠，丁心戊胃己脾乡。庚是大肠辛属肺，壬系膀胱癸肾藏。三焦亦是壬中寄，包络同归入癸方。",
        },
        {
            "title": "天干与人体对应关系",
            "content": "甲头乙项丙肩求，丁心戊肋己属腹。庚是脐轮辛为股，壬癸足足一身由。",
        },
        {
            "title": "地支与内脏关系对应",
            "content": "子属膀胱水道耳，丑为胞肚及脾乡。寅胆发脉并两手，卯本十指内肝方。辰土为皮肩胸肋，巳面齿咽下尻肛。午火精神司眼目，未土胃脘隔脊梁。申金大肠经络肺，酉中精血小肠藏。戌土命门腿足，亥水为头及肾囊。",
        },
        {
            "title": "地支与人体关系对应",
            "content": "午头巳未两肩均，左右二腕为辰申。卯酉双肋寅戌腿，丑亥属脚子为阴。",
        },
        {
            "title": "八卦与人体对应关系",
            "content": "干首坤腹坎耳俦，震足巽股艮手留。兑口离目分八卦，凡看病此中求。",
        },
        {
            "title": "八记忆卦口诀",
            "content": "干三连，坤六断。震仰盂，艮覆碗。兑上缺，巽下断。离中虚，坎中满。",
        },
        {
            "title": "年上月初，五虎遁",
            "content": "甲己之年丙作首，乙庚之岁戊为头。丙辛之岁寻庚上，丁壬壬寅顺水流。若问戊何处癸起，甲寅之上好追求。",
        },
        {
            "title": "日起时，五鼠遁",
            "content": "甲己还加甲，乙庚丙作初。丙辛从戊起，丁壬庚子居。癸起壬子，周而复始求。",
        },
        {
            "title": "寻找世认宫歌",
            "content": "天同二世天变五。地同四世地变初。本宫六世三世异。人同游魂人变归。一二三六外卦宫。四五游魂内卦变更。归魂内卦是本宫。",
        },
    ]
    return {
        "method_label": "歌诀",
        "question": "",
        "summary": "这里放六爻的速记和口诀，方便快速理解卦意。",
        "cards": [{"label": item["title"], "value": item["content"]} for item in built_in_songs],
        "suggestions": ["如果不需要这块，后续可以直接删除。"],
        "raw_result": {"snippets": built_in_songs},
    }


async def _interpret_with_llm(question: str, base_result: dict[str, Any], db: Session | None) -> tuple[str, str]:
    system_prompt = (
        "你是 Tokendancer 的六爻解读器。"
        "请把六爻结果翻译成一段自然、克制、可行动的中文建议。"
        "重点说本卦、动爻、变卦、当前局势、宜守宜进，不要讲推导过程，不要输出标题，不要长篇大论。"
    )
    user_prompt = json.dumps(
        {
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


def _fallback_interpretation(base_result: dict[str, Any]) -> str:
    summary = _normalize_text(base_result.get("summary"))
    suggestions = base_result.get("suggestions")
    suggestion_text = " ".join(_normalize_text(item) for item in suggestions or [] if _normalize_text(item))
    return f"{summary} {suggestion_text}".strip()


async def generate_how_to_do_runtime(request: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    section = _normalize_text(request.get("section")) or "cast"
    cast_mode = _normalize_text(request.get("cast_mode")) or "coin"
    question = _normalize_text(request.get("question"))
    category = _normalize_text(request.get("category"))
    cast_seed = _normalize_text(request.get("cast_seed"))
    manual_lines = request.get("manual_lines") or []
    character_text = _normalize_text(request.get("character_text"))
    number_text = _normalize_text(request.get("number_text"))
    use_ai = bool(request.get("use_ai", True))

    if section == "catalog":
        base_result = _build_catalog_result()
    elif section in {"reference", "calendar", "clock", "sundial"}:
        base_result = _build_reference_result()
    elif section == "songs":
        base_result = _build_songs_result()
    elif section == "cast":
        source_text = character_text or number_text or question
        base_result = _build_cast_result(question, category, cast_mode, cast_seed, source_text=source_text, manual_lines=manual_lines)
    elif section == "detail":
        base_result = _build_cast_result(question, category, cast_mode, cast_seed, source_text=character_text or number_text or question, manual_lines=manual_lines)
    else:
        raise ValueError(f"不支持的模块: {section}")

    ai_interpretation = _fallback_interpretation(base_result)
    model_used = ""
    if use_ai and db is not None and section == "cast":
        try:
            ai_text, model_used = await _interpret_with_llm(question, base_result, db)
            if ai_text:
                ai_interpretation = strip_think_blocks(ai_text).strip()
        except LLMGatewayError:
            model_used = ""
        except Exception:
            model_used = ""

    return {
        "section": section,
        "method_label": base_result.get("method_label", SECTION_LABELS.get(section, "我该怎么做")),
        "question": question,
        "summary": _normalize_text(base_result.get("summary")),
        "cards": base_result.get("cards", []),
        "ai_interpretation": ai_interpretation,
        "suggestions": base_result.get("suggestions", []),
        "raw_result": base_result.get("raw_result", {}),
        "catalog": base_result.get("raw_result", {}).get("catalog", []),
        "model_used": model_used,
    }
