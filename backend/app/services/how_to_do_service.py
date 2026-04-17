from __future__ import annotations

import hashlib
import json
import random
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.llm_gateway import LLMGatewayError, generate_reply
from app.services.text_sanitizer import strip_think_blocks


SECTION_LABELS = {
    "cast": "六爻起卦",
    "reference": "参考",
    "catalog": "卦库",
    "calendar": "日历",
    "clock": "时钟",
    "records": "记录",
    "songs": "歌诀",
}

CAST_MODE_LABELS = {
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

ALL_GUA_CATALOG = [
    {"number": number, "name": name, "meaning": HEXAGRAM_MEANINGS.get(name, "顺势而行"), "binary": binary}
    for binary, (number, name) in sorted(HEXAGRAM_MAP.items(), key=lambda item: item[1][0])
]


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


def _line_text(position: int, yin_yang: str, is_changing: bool) -> str:
    prefix = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][position - 1]
    return f"{prefix}：{'阳' if yin_yang == '阳' else '阴'}{'（动）' if is_changing else ''}"


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


def _build_lines(seed: str, mode: str, cast_mode: str, question: str, source_text: str = "") -> list[dict[str, Any]]:
    rng = _make_rng(seed, mode, cast_mode, question, source_text)
    lines: list[dict[str, Any]] = []
    for position in range(1, 7):
      # 6/7/8/9 代表老阴、少阳、少阴、老阳
        if cast_mode == "character":
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


def _build_cast_result(question: str, cast_mode: str, cast_seed: str, source_text: str = "") -> dict[str, Any]:
    lines = _build_lines(cast_seed or datetime.now().isoformat(timespec="seconds"), "cast", cast_mode, question, source_text)
    binary = _binary_from_lines(lines)
    hexagram_number, name = _hexagram_lookup(binary)
    upper = TRIGRAMS[_trigram_index(lines[:3])]
    lower = TRIGRAMS[_trigram_index(lines[3:])]
    changing_lines = [item["position"] for item in lines if item["is_changing"]]
    mutual_hexagram = _build_mutual_hexagram(lines)
    transformed_hexagram = None
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
        transformed_upper = TRIGRAMS[_trigram_index(transformed_lines[:3])]
        transformed_lower = TRIGRAMS[_trigram_index(transformed_lines[3:])]
        transformed_hexagram = {
            "hexagram_number": transformed_number,
            "name": transformed_name,
            "meaning": _hexagram_meaning(transformed_name),
            "upper_trigram": transformed_upper["name"],
            "lower_trigram": transformed_lower["name"],
        }

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
    ]
    suggestions = [
        "先看动爻在哪一层，再判断该守还是该推。",
        "有变卦时，优先看变化方向，不要只盯本卦。",
        "六爻更适合看当前局势，先定节奏再动作。",
    ]

    return {
        "method_label": "六爻排盘",
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
            "transformed_hexagram": transformed_hexagram,
        },
    }


def _build_catalog_result() -> dict[str, Any]:
    cards = [
        {"label": f"{item['number']} {item['name']}", "value": item["meaning"]}
        for item in ALL_GUA_CATALOG
    ]
    return {
        "method_label": "六十四卦库",
        "question": "",
        "summary": "六十四卦库，点开任意一卦即可查看名称与卦意。",
        "cards": cards[:12],
        "suggestions": ["可直接在卦库中搜索卦名。", "需要查看完整内容时，继续向下浏览。"],
        "raw_result": {"catalog": ALL_GUA_CATALOG},
    }


def _build_reference_result() -> dict[str, Any]:
    cards = [
        {"label": "方向", "value": "先看局势走向，再看进退节奏。"},
        {"label": "生克", "value": "先看谁生谁、谁克谁，再看谁更主动。"},
        {"label": "旺衰", "value": "看当前力量强弱，不只看单一符号。"},
        {"label": "类象", "value": "用基础类象辅助理解，不替代整体判断。"},
        {"label": "提示", "value": "参考页是底层辅助，最终还是回到本卦与动爻。"},
    ]
    return {
        "method_label": "参考",
        "question": "",
        "summary": "方向、生克、旺衰与类象辅助，放在这里先做参考。",
        "cards": cards,
        "suggestions": ["如果要进一步判断，回到起卦页看本卦、互卦和变卦。"],
        "raw_result": {"reference": cards},
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
    return {
        "method_label": "歌诀",
        "question": "",
        "summary": "这里放六爻的速记和口诀，方便快速理解卦意。",
        "cards": [{"label": "速记", "value": snippet} for snippet in GROUNDING_SNIPPETS[:4]],
        "suggestions": ["如果不需要这块，后续可以直接删除。"],
        "raw_result": {"snippets": GROUNDING_SNIPPETS},
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
    cast_seed = _normalize_text(request.get("cast_seed"))
    character_text = _normalize_text(request.get("character_text"))
    number_text = _normalize_text(request.get("number_text"))
    use_ai = bool(request.get("use_ai", True))

    if section == "catalog":
        base_result = _build_catalog_result()
    elif section == "reference":
        base_result = _build_reference_result()
    elif section == "calendar":
        base_result = _build_calendar_result()
    elif section == "clock":
        base_result = _build_clock_result()
    elif section == "records":
        base_result = _build_records_result()
    elif section == "songs":
        base_result = _build_songs_result()
    elif section == "cast":
        source_text = character_text or number_text or question
        base_result = _build_cast_result(question, cast_mode, cast_seed, source_text=source_text)
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
